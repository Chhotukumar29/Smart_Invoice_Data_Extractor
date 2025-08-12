import streamlit as st
from PIL import Image
import google.generativeai as genai
import PyPDF2
import io
import json
from dotenv import load_dotenv
import os
import re
import pdfplumber

# Load environment variables from .env file
load_dotenv()

# Configure the Google API key from environment variable
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    st.error("GEMINI_API_KEY not found in .env file. Please add your API key to the .env file.")
    st.stop()

genai.configure(api_key=api_key)

# ===== Function to load Gemini model and get responses =====
def get_gemini_response(input, image, prompt):
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content([input, image[0], prompt])
    return response.text

# ===== Function to convert PDF pages to images =====
def pdf_to_images(pdf_file):
    import fitz  # PyMuPDF
    pdf_document = fitz.open(stream=pdf_file.read(), filetype="pdf")
    images = []
    
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        pix = page.get_pixmap()
        img_data = pix.tobytes("png")
        images.append(img_data)
    
    pdf_document.close()
    return images

# ===== Function to set up image for processing =====
def input_image_setup(image_data, mime_type="image/png"):
    if image_data is not None:
        image_parts = [
            {
                "mime_type": mime_type,
                "data": image_data
            }
        ]
        return image_parts
    else:
        raise FileNotFoundError("No image data provided")

# ===== Extract HSN and GST rate directly from PDF =====
def extract_hsn_and_rate(pdf_path):
    results = []
    hsn_pattern = r"\b\d{4,8}\b"   # HSN code pattern
    gst_pattern = r"(\d{1,2})\s*%" # GST percentage pattern

    with pdfplumber.open(pdf_path) as pdf:
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
                    
                    # Check GST rate in same line
                    gst_match = re.search(gst_pattern, line)
                    if gst_match:
                        gst_rate = int(gst_match.group(1))
                    else:
                        # Check next 2 lines if not found
                        for next_line in lines[idx+1: idx+3]:
                            gst_match_next = re.search(gst_pattern, next_line)
                            if gst_match_next:
                                gst_rate = int(gst_match_next.group(1))
                                break
                    
                    results.append({
                        "HSN": hsn_code,
                        "GST_Rate(%)": gst_rate
                    })
    return results

# ===== Streamlit App UI =====
st.set_page_config(page_title="Invoice Extractor")
st.header("Multi Language Invoice Extractor")
st.write("Upload a PDF file containing multiple invoices (one per page) to extract information and GST rates from each invoice.")

uploaded_file = st.file_uploader("Choose a PDF file...", type=["pdf"])

if uploaded_file is not None:
    st.success(f"PDF file '{uploaded_file.name}' uploaded successfully!")
    pdf_reader = PyPDF2.PdfReader(uploaded_file)
    num_pages = len(pdf_reader.pages)
    st.info(f"PDF contains {num_pages} page(s). Each page will be processed as a separate invoice.")

submit_button = st.button("Extract Invoice Information")

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

if submit_button and uploaded_file is not None:
    try:
        st.subheader("Processing PDF...")
        import fitz  # PyMuPDF
        pdf_document = fitz.open(stream=uploaded_file.getvalue(), filetype="pdf")
        
        # Extract HSN & GST rates
        uploaded_file.seek(0)
        hsn_gst_data = extract_hsn_and_rate(uploaded_file)

        all_invoices = []
        for page_num in range(len(pdf_document)):
            st.write(f"Processing page {page_num + 1}...")
            page = pdf_document.load_page(page_num)
            pix = page.get_pixmap()
            img_data = pix.tobytes("png")
            
            image_data = input_image_setup(img_data)
            response = get_gemini_response(input_prompt, image_data, "Extract invoice information as JSON")
            
            try:
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
                            item["page_number"] = page_num + 1
                            # Auto-fill GST & HSN from extracted data if missing
                            for hg in hsn_gst_data:
                                if "Section 2_Transaction hsn" not in item or not item["Section 2_Transaction hsn"]:
                                    item["Section 2_Transaction hsn"] = hg["HSN"]
                                if "Section 2_Transaction gst" not in item or not item["Section 2_Transaction gst"]:
                                    item["Section 2_Transaction gst"] = hg["GST_Rate(%)"]
                            all_invoices.append(item)
                    else:
                        parsed_data["page_number"] = page_num + 1
                        all_invoices.append(parsed_data)
                else:
                    st.error(f"Could not extract valid JSON from page {page_num + 1}")
                    st.text(f"Raw response: {response}")
            except json.JSONDecodeError as e:
                st.error(f"Invalid JSON format on page {page_num + 1}: {str(e)}")
                st.text(f"Raw response: {response}")
        
        pdf_document.close()
        
        if all_invoices:
            st.subheader(f"Extracted Invoice Information ({len(all_invoices)} line items)")
            pages = {}
            for invoice in all_invoices:
                page_num = invoice.get('page_number', 1)
                if page_num not in pages:
                    pages[page_num] = []
                pages[page_num].append(invoice)
            
            for page_num in sorted(pages.keys()):
                page_items = pages[page_num]
                st.write(f"### Page {page_num} ({len(page_items)} line items)")
                for i, invoice in enumerate(page_items[:3]):
                    st.json(invoice)
                if len(page_items) > 3:
                    with st.expander(f"Show remaining {len(page_items) - 3} items from page {page_num}"):
                        for invoice in page_items[3:]:
                            st.json(invoice)
                st.write("---")
            
            json_output = json.dumps(all_invoices, indent=2)
            st.download_button(
                label=f"Download All {len(all_invoices)} Line Items as JSON",
                data=json_output,
                file_name="extracted_invoices.json",
                mime="application/json"
            )
        else:
            st.error("No valid invoice data could be extracted from the PDF.")
            
    except Exception as e:
        st.error(f"Error processing PDF: {str(e)}")
        st.write("Please make sure you have uploaded a valid PDF file.")
elif submit_button and uploaded_file is None:
    st.error("Please upload a PDF file first.")
