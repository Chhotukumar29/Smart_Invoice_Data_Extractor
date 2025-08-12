from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import google.generativeai as genai
import PyPDF2
import json
import os
import re
import pdfplumber
import fitz  # PyMuPDF
from datetime import datetime
import tempfile
import uuid


app = FastAPI(title="Invoice Extractor MCP API", version="1.0.0")


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


# Pydantic models
class InvoiceItem(BaseModel):
    title: str
    doc_id: str
    type: str
    uploaded_from: str = "web"
    user_doc_id: Optional[str] = None
    doc_meta_data: Optional[str] = None
    folder_name: Optional[str] = None
    folder_id: Optional[str] = None
    status: str = "reviewing"
    created_at_iso: str
    modified_at_iso: str
    section_2_transaction_sort: int
    section_2_transaction_number: Optional[str] = None
    section_2_transaction_rate: Optional[float] = None
    section_2_transaction_qty: Optional[int] = None
    section_2_transaction_gst: Optional[float] = None
    section_2_transaction_discount: Optional[float] = None
    section_2_transaction_hsn: Optional[str] = None
    section_2_transaction_mrp: Optional[float] = None
    page_number: int


class InvoiceResponse(BaseModel):
    success: bool
    message: str
    data: List[InvoiceItem]
    total_items: int
    pages_processed: int


class HealthResponse(BaseModel):
    status: str
    message: str
    timestamp: str


# Utility functions
def get_gemini_response(input_prompt: str, image_data: bytes, prompt: str) -> str:
    """Get response from Gemini model"""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        image_parts = [{
            "mime_type": "image/png",
            "data": image_data
        }]
        response = model.generate_content([input_prompt, image_parts[0], prompt])
        return response.text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini API error: {str(e)}")


def extract_hsn_and_rate(pdf_bytes: bytes) -> List[Dict[str, Any]]:
    """Extract HSN codes and GST rates from PDF"""
    results = []
    hsn_pattern = r"\b\d{4,8}\b"
    gst_pattern = r"(\d{1,2})\s*%"
    
    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(pdf_bytes)
            tmp_file_path = tmp_file.name
        
        with pdfplumber.open(tmp_file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue
                
                lines = text.split("\n")
                for idx, line in enumerate(lines):
                    hsn_match = re.search(hsn_pattern, line)
                    if hsn_match:
                        hsn_code = hsn_match.group(0)
                        gst_rate = None
                        
                        gst_match = re.search(gst_pattern, line)
                        if gst_match:
                            gst_rate = int(gst_match.group(1))
                        else:
                            for next_line in lines[idx+1: idx+3]:
                                gst_match_next = re.search(gst_pattern, next_line)
                                if gst_match_next:
                                    gst_rate = int(gst_match_next.group(1))
                                    break
                        
                        results.append({
                            "HSN": hsn_code,
                            "GST_Rate(%)": gst_rate
                        })
        
        os.unlink(tmp_file_path)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"HSN extraction error: {str(e)}")


# API Routes
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        message="Invoice Extractor MCP API is running",
        timestamp=datetime.now().isoformat()
    )


@app.post("/extract-invoice", response_model=InvoiceResponse)
async def extract_invoice(file: UploadFile = File(...)):
    """Extract invoice information from uploaded PDF"""
    
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        # Read PDF content
        pdf_content = await file.read()
        
        # Extract HSN and GST data
        hsn_gst_data = extract_hsn_and_rate(pdf_content)
        
        # Process PDF pages
        pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
        all_invoices = []
        
        input_prompt = """
        You are an expert in understanding invoices. Analyze the invoice image and extract ALL line items/transactions from the invoice.
        Extract GST rate from PDF using HSN code and fill Section 2_Transaction gst column automatically.
        For EACH line item in the invoice, create a separate JSON object with this structure:


        {
            "title": "[PDF filename or invoice title]",
            "doc_id": "[generate a unique ID or extract from invoice]",
            "type": "[invoice type like 'Tax Invoice']",
            "uploaded_from": "web",
            "user_doc_id": "[extract if available]",
            "doc_meta_data": "[extract if available]",
            "folder_name": "[extract if available]",
            "folder_id": "[extract if available]",
            "status": "reviewing",
            "created_at_iso": "[current date in ISO format]",
            "modified_at_iso": "[current date in ISO format]",
            "Section 2_Transaction sort": "[line item number/sequence]",
            "Section 2_Transaction number": "[product/part number]",
            "Section 2_Transaction rate": "[unit price as number]",
            "Section 2_Transaction qty": "[quantity as number]",
            "Section 2_Transaction gst": "[GST percentage as number]",
            "Section 2_Transaction discount": "[discount if any]",
            "Section 2_Transaction hsn": "[HSN code]",
            "Section 2_Transaction MRP": "[total amount for this line item]"
        }


        IMPORTANT: 
        - Return a JSON ARRAY containing ALL line items from the invoice
        - Each line item should be a separate object in the array
        - Extract ALL products/services listed in the invoice
        - Use consistent metadata for all line items from the same invoice
        - Generate sequential numbers for 'Section 2_Transaction sort' (1, 2, 3, etc.)


        Return ONLY the JSON array without any additional text.
        """
        
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            pix = page.get_pixmap()
            img_data = pix.tobytes("png")
            
            # Get Gemini response
            if GEMINI_API_KEY:
                response = get_gemini_response(input_prompt, img_data, "Extract invoice information as JSON")
                
                try:
                    # Parse JSON response
                    json_start = response.find('[')
                    json_end = response.rfind(']') + 1
                    if json_start == -1:
                        json_start = response.find('{')
                        json_end = response.rfind('}') + 1
                    
                    if json_start != -1 and json_end != -1:
                        json_str = response[json_start:json_end]
                        parsed_data = json.loads(json_str)
                        
                        if isinstance(parsed_data, list):
                            for item in parsed_data:
                                # Map fields to snake_case for Pydantic
                                invoice_item = {
                                    "title": item.get("title", file.filename),
                                    "doc_id": item.get("doc_id", str(uuid.uuid4())),
                                    "type": item.get("type", "Tax Invoice"),
                                    "uploaded_from": "web",
                                    "user_doc_id": item.get("user_doc_id"),
                                    "doc_meta_data": item.get("doc_meta_data"),
                                    "folder_name": item.get("folder_name"),
                                    "folder_id": item.get("folder_id"),
                                    "status": "reviewing",
                                    "created_at_iso": datetime.now().isoformat(),
                                    "modified_at_iso": datetime.now().isoformat(),
                                    "section_2_transaction_sort": item.get("Section 2_Transaction sort", 1),
                                    "section_2_transaction_number": item.get("Section 2_Transaction number"),
                                    "section_2_transaction_rate": float(item.get("Section 2_Transaction rate", 0)) if item.get("Section 2_Transaction rate") else None,
                                    "section_2_transaction_qty": int(item.get("Section 2_Transaction qty", 0)) if item.get("Section 2_Transaction qty") else None,
                                    "section_2_transaction_gst": float(item.get("Section 2_Transaction gst", 0)) if item.get("Section 2_Transaction gst") else None,
                                    "section_2_transaction_discount": float(item.get("Section 2_Transaction discount", 0)) if item.get("Section 2_Transaction discount") else None,
                                    "section_2_transaction_hsn": item.get("Section 2_Transaction hsn"),
                                    "section_2_transaction_mrp": float(item.get("Section 2_Transaction MRP", 0)) if item.get("Section 2_Transaction MRP") else None,
                                    "page_number": page_num + 1
                                }
                                
                                # Auto-fill HSN and GST from extracted data
                                for hg in hsn_gst_data:
                                    if not invoice_item["section_2_transaction_hsn"]:
                                        invoice_item["section_2_transaction_hsn"] = hg["HSN"]
                                    if not invoice_item["section_2_transaction_gst"]:
                                        invoice_item["section_2_transaction_gst"] = hg["GST_Rate(%)"]
                                
                                all_invoices.append(InvoiceItem(**invoice_item))
                    else:
                        # Handle single item
                        invoice_item = {
                            "title": parsed_data.get("title", file.filename),
                            "doc_id": parsed_data.get("doc_id", str(uuid.uuid4())),
                            "type": parsed_data.get("type", "Tax Invoice"),
                            "uploaded_from": "web",
                            "created_at_iso": datetime.now().isoformat(),
                            "modified_at_iso": datetime.now().isoformat(),
                            "section_2_transaction_sort": 1,
                            "page_number": page_num + 1
                        }
                        all_invoices.append(InvoiceItem(**invoice_item))
                
                except json.JSONDecodeError:
                    # If JSON parsing fails, create a basic item
                    basic_item = {
                        "title": file.filename,
                        "doc_id": str(uuid.uuid4()),
                        "type": "Tax Invoice",
                        "uploaded_from": "web",
                        "status": "reviewing",
                        "created_at_iso": datetime.now().isoformat(),
                        "modified_at_iso": datetime.now().isoformat(),
                        "section_2_transaction_sort": 1,
                        "page_number": page_num + 1
                    }
                    all_invoices.append(InvoiceItem(**basic_item))
        
        pdf_document.close()
        
        return InvoiceResponse(
            success=True,
            message=f"Successfully extracted {len(all_invoices)} invoice items from {len(pdf_document)} pages",
            data=all_invoices,
            total_items=len(all_invoices),
            pages_processed=len(pdf_document)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Invoice Extractor MCP API", "version": "1.0.0", "docs": "/docs"}
