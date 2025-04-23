from dotenv import load_dotenv
import streamlit as st
import os
import fitz  # PyMuPDF
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Function to extract text from PDF
def extract_text_from_pdf(uploaded_file):
    pdf_reader = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    text = ""
    for page in pdf_reader:
        text += page.get_text()
    return text

# Function to get Gemini response
def get_gemini_response(prompt, pdf_text):
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content([prompt, pdf_text])
    return response.text

# Streamlit UI
st.set_page_config(page_title="Invoice Data Extractor")
st.header("Invoice PDF Data Extractor") 

input_features = st.text_area("Enter features to extract (comma separated):", "Invoice Number, Date, Total Amount, Vendor Name")

uploaded_file = st.file_uploader("Upload an invoice (PDF only)", type=["pdf"])
submit = st.button("Extract")

if submit and uploaded_file:
    with st.spinner("Extracting..."):
        pdf_text = extract_text_from_pdf(uploaded_file)

        # Create prompt
        input_prompt = f"""
        You are an expert at reading invoices.
        Extract the following fields from the invoice PDF:
        {input_features}.
        Return
          the output in plain text or readable format.
        """

        response_text = get_gemini_response(input_prompt, pdf_text)

        st.success("Extraction complete!")
        st.subheader("Extracted Data")
        st.write(response_text)
