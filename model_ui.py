from dotenv import load_dotenv
import streamlit as st
import os
import fitz  # PyMuPDF
import google.generativeai as genai
import json
import pandas as pd
from datetime import datetime

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Configure Google API
genai.configure(api_key=GOOGLE_API_KEY)

# Set page configuration
st.set_page_config(
    page_title="InvoiceXtract Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton button {
        background-color: #4CAF50;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        font-weight: bold;
        border: none;
        transition: all 0.3s;
    }
    .stButton button:hover {
        background-color: #45a049;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    .header-container {
        display: flex;
        align-items: center;
        margin-bottom: 2rem;
    }
    .header-text {
        margin-left: 1rem;
    }
    .extraction-result {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        margin-top: 20px;
        border-left: 5px solid #4CAF50;
    }
    </style>
    """, unsafe_allow_html=True)

# Function to extract text from PDF
def extract_text_from_pdf(uploaded_file):
    try:
        pdf_reader = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        text = ""
        for page in pdf_reader:
            text += page.get_text()
        return text, len(pdf_reader)
    except Exception as e:
        st.error(f"Error processing PDF: {str(e)}")
        return None, 0

# Function to get Gemini response
def get_gemini_response(prompt, pdf_text, structured_output=False):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        if structured_output:
            prompt += "\nProvide the output as a valid JSON object."
            
        response = model.generate_content([prompt, pdf_text])
        return response.text
    except Exception as e:
        st.error(f"Error from Gemini API: {str(e)}")
        return None

# Function to parse response to dictionary (if possible)
def parse_response(response_text):
    try:
        # Try to extract JSON if it exists
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
            return json.loads(json_str)
        elif "```" in response_text:
            json_str = response_text.split("```")[1].strip()
            return json.loads(json_str)
        else:
            # Try parsing directly
            return json.loads(response_text)
    except:
        # Return None if not parseable as JSON
        return None

# Sidebar
with st.sidebar:
    st.markdown("## Settings")
    
    output_format = st.radio(
        "Output Format:",
        ["Text", "Structured (JSON)", "Table View"],
        index=2
    )
    
    st.markdown("---")
    st.markdown("### About InvoiceXtract Pro")
    st.info(
        "InvoiceXtract Pro helps you quickly extract key information from invoice PDFs, "
        "saving you time and reducing manual data entry errors."
    )
    


# Main content
st.markdown("<div class='header-container'><h1>InvoiceXtract Pro</h1></div>", unsafe_allow_html=True)


# Default fields
default_fields = "Invoice Number, Buyer Name, Billing Address, Total Amount, Taxable Amount, Tax Amount, Invoice Date, Dated, Pincode, Vendor Name"

col1, col2 = st.columns([2, 1])

with col1:
    input_features = st.text_area(
        "Key Fields to Extract (comma separated):",
        default_fields,
        help="List the specific fields you want to extract from the invoice"
    )

with col2:
    st.markdown("#### Quick Add Fields")
    quick_fields = st.multiselect(
        "Add common fields:",
        ["GST Number", "PO Number", "Payment Terms", "Currency", "Discount", "Line Items"],
        []
    )
    
    if quick_fields:
        if input_features.strip():
            input_features += ", " + ", ".join(quick_fields)
        else:
            input_features = ", ".join(quick_fields)
        
        # Update the text area with new fields
        st.session_state["input_features"] = input_features

# File uploader section
st.markdown("### Upload Invoice")
col1, col2 = st.columns([3, 1])

with col1:
    uploaded_file = st.file_uploader(
        "Drag and drop an invoice PDF or click to browse",
        type=["pdf"],
        help="We accept PDF files only"
    )

with col2:
    if not uploaded_file:
        st.info("No file uploaded yet")

# Process the uploaded file
if uploaded_file:
    file_details = {"Filename": uploaded_file.name, "Size": f"{uploaded_file.size / 1024:.2f} KB"}
    
    with st.expander("File Details", expanded=True):
        st.json(file_details)
    
    # Extract button
    extract_col, clear_col = st.columns([1, 1])
    
    with extract_col:
        submit = st.button("🔍 Extract Data", use_container_width=True)
    
    with clear_col:
        clear = st.button("🗑️ Clear Results", use_container_width=True)
        if clear:
            st.session_state.pop('extraction_result', None)
            st.experimental_rerun()
    
    if submit:
        with st.spinner("Processing invoice..."):
            # Show progress
            progress_bar = st.progress(0)
            
            # Step 1: Extract text
            progress_bar.progress(25)
            st.info("Reading PDF content...")
            pdf_text, page_count = extract_text_from_pdf(uploaded_file)
            
            if pdf_text:
                # Step 2: Prepare prompt
                progress_bar.progress(50)
                st.info("Analyzing invoice structure...")
                
                use_structured = output_format in ["Structured (JSON)", "Table View"]
                
                input_prompt = f"""
                You are an expert at reading invoices.
                Extract the following fields from the invoice PDF:
                {input_features}.
                
                Focus on accuracy and be precise with numbers and dates.
                If a field is not found, indicate with "Not found" or "N/A".
                """
                
                if use_structured:
                    input_prompt += "\nReturn the output as a properly formatted JSON object with the fields as keys."
                else:
                    input_prompt += "\nReturn the output in a clean, readable format."
                
                # Step 3: Get response
                progress_bar.progress(75)
                st.info("Extracting data points...")
                response_text = get_gemini_response(input_prompt, pdf_text, use_structured)
                
                # Step 4: Process results
                progress_bar.progress(100)
                
                if response_text:
                    st.session_state['extraction_result'] = response_text
                    st.session_state['extraction_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    st.success(f"✅ Extraction complete from {page_count} page{'s' if page_count > 1 else ''}!")
                    
                    # Parse the response if structured output is requested
                    parsed_data = None
                    if use_structured:
                        parsed_data = parse_response(response_text)
    
    # Display results if available
    if 'extraction_result' in st.session_state:
        st.markdown("---")
        st.subheader("📄 Extracted Data")
        st.markdown(f"<small>Extracted on: {st.session_state.get('extraction_time', 'Unknown')}</small>", unsafe_allow_html=True)
        
        result_text = st.session_state['extraction_result']
        
        # Handle different output formats
        if output_format == "Text":
            st.markdown("<div class='extraction-result'>", unsafe_allow_html=True)
            st.write(result_text)
            st.markdown("</div>", unsafe_allow_html=True)
            
        elif output_format == "Structured (JSON)":
            parsed_data = parse_response(result_text)
            if parsed_data:
                st.json(parsed_data)
            else:
                st.code(result_text)
                
        elif output_format == "Table View":
            parsed_data = parse_response(result_text)
            if parsed_data:
                # Convert to DataFrame
                df = pd.DataFrame(list(parsed_data.items()), columns=['Field', 'Value'])
                st.dataframe(df, use_container_width=True)
            else:
                # Try to parse from text format
                lines = result_text.split('\n')
                data = []
                for line in lines:
                    if ":" in line:
                        key, value = line.split(":", 1)
                        data.append({"Field": key.strip(), "Value": value.strip()})
                
                if data:
                    st.dataframe(pd.DataFrame(data), use_container_width=True)
                else:
                    st.write(result_text)
        
        # Download options
        st.markdown("### Export Results")
        col1, col2 = st.columns(2)
        
        with col1:
            st.download_button(
                label="📥 Download as Text",
                data=result_text,
                file_name=f"invoice_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
        
        with col2:
            parsed_data = parse_response(result_text)
            if parsed_data:
                st.download_button(
                    label="📥 Download as JSON",
                    data=json.dumps(parsed_data, indent=2),
                    file_name=f"invoice_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
else:
    # Show sample results or instructions when no file is uploaded
    st.markdown("### How It Works")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 1. Upload")
        st.markdown("Upload your invoice PDF file")
        
    with col2:
        st.markdown("#### 2. Configure")
        st.markdown("Select the fields you want to extract")
        
    with col3:
        st.markdown("#### 3. Extract")
        st.markdown("Get structured data in seconds")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center;'>"
    "<p>InvoiceXtract Pro | Powered by AI | Need help? Contact support@invoicextract.io</p>"
    "</div>",
    unsafe_allow_html=True
)