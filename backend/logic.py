from dotenv import load_dotenv
import os
import json
import google.generativeai as genai
import fitz  # PyMuPDF
import pandas as pd


load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key = GOOGLE_API_KEY)


## PATH TO STORE EXTRACTED DATA
csv_path = "backend/extracted_invoice_data.csv"
## PATH TO STORE EXTRACTED GOODS DESCRIPTION
goods_csv_path = "backend/extracted_goods_description.csv"


## FUNCTION - 1
def extract_text_from_pdf(pdf_file_path):
    pdf_reader = fitz.open(pdf_file_path)
    text = ""
    for page in pdf_reader:
        text += page.get_text()

        # if "e-Way Bill" in page_text or "eway bill" in page_text.lower():
        #     break

        # text += page_text
    return text

## FUNCTION - 1.1
def build_input_prompt(input_features_list):
    return f"""
You are an expert at reading invoices.

📌 Your task is to extract ONLY the main invoice data. DO NOT extract anything from sections like 'E-Way Bill', 'Transport Details', or repeated product summaries. Focus only on the core invoice table typically located at the top or middle of the document.

Extract the following fields:
{input_features_list}

For items like 'Description of goods', 'Part no.', 'Rate', and 'Quantity', if multiple goods are listed, return them in a list called "Line Items", like this:

"Line Items": [
  {{
    "Description of goods": "Item A",
    "Part no.": "1234",
    "Rate": "150.00",
    "Quantity": "2"
  }},
  {{
    "Description of goods": "Item B",
    "Part no.": "5678",
    "Rate": "250.00",
    "Quantity": "1"
  }}
]

⚡ Return ONLY a valid JSON object, no notes or explanations.
⚠️ Do not include anything from the E-Way Bill section or anything below that.

Example:
{{
  "Invoice Number": "[value]",
  "Date": "[value]",
  "Total Amount": "[value]",
  ...
  "Line Items": [
    {{ "Description of goods": "...", "Part no.": "...", "Rate": "...", "Quantity": "..." }},
    ...
  ]
}}
"""

## FUNCTION - 2
def get_gemini_response(prompt, pdf_text):
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content([prompt, pdf_text])
    return response.text


## FUNCTION - 3
def save_to_csv(extracted_data, csv_path):
    if os.path.exists(csv_path) and os.path.getsize(csv_path) > 0:
        existing_df = pd.read_csv(csv_path)
        updated_df = pd.concat([existing_df, pd.DataFrame([extracted_data])], ignore_index=True)

    else:
        updated_df = pd.DataFrame([extracted_data])

    updated_df.to_csv(csv_path, index=False)
    print(f"Data saved successfully to {csv_path}")


## FUNCTION - 3.1
def save_goods_description_to_csv(extracted_data, goods_csv_path):
    if "Line Items" in extracted_data:
        invoice_number = extracted_data.get("Invoice Number", "N/A")
        line_items = extracted_data["Line Items"]

        # if isinstance(line_items, list) and line_items:
        #     goods_df = pd.DataFrame(line_items)

        # ADD 'Invoice Number' TO EACH ITEM IN LINE ITEMS
        for item in line_items:
            item["Invoice Number"] = invoice_number

        goods_df = pd.DataFrame(line_items)

        if os.path.exists(goods_csv_path) and os.path.getsize(goods_csv_path) > 0:
            existing_goods_df = pd.read_csv(goods_csv_path)
            updated_goods_df = pd.concat([existing_goods_df, goods_df], ignore_index=True)
        else:
            updated_goods_df = goods_df

        updated_goods_df.to_csv(goods_csv_path, index=False)
        print(f"Line items saved successfully to {goods_csv_path}")
    else:
        print("No 'Line Items' found in the extracted data.")



## FUNCTION - 4 = MAIN FUNCTION -> ORCHESTRATOR THE ENTIRE WORKFLOW

def main(uploaded_pdf_path, input_features_list):

    print("----Starting the Extraction Process...-----\n")

    
    pdf_text = extract_text_from_pdf(uploaded_pdf_path)
    print("PDF Text Txtraction Complete!")
    print("==============================================================\n")
    # print(pdf_text)


    print("----Building the input prompt...----")
    input_prompt = build_input_prompt(input_features_list)
    print("Input prompt built successfully!")
    print("==============================================================\n")

    
    print("----Getting Response...----")
    response_text = get_gemini_response(input_prompt, pdf_text)
    print("Model Response Received!\n")
    print(response_text)
    print("==============================================================\n")


    print("----Cleaning the response text...----")

    ## CLEANING THE RESPONSE TEXT

    response_text = response_text.strip()

    start_idx = response_text.find('{')
    end_idx = response_text.rfind('}')

    if start_idx != -1 and end_idx != -1:
        response_text = response_text[start_idx:end_idx+1]
    else:
        print("Error: JSON object not found in Gemini response.")
        return
    
    print("\n----Getting the Expected JSON Response After Cleaning...----\n")
    print(response_text)
    print("==============================================================\n")
    

    ## PARSE THE JSON RESPONSE
    try:
        extracted_data = json.loads(response_text)
    except json.JSONDecodeError as e:
        print("Failed to parse the extracted data. Please check the Gemini output.")
        print(f"Error: {e}")
        return
    
    print("\nJSON response parsed successfully!\n")
    print(extracted_data)
    print("==============================================================\n")
    

    save_to_csv(extracted_data, csv_path)

    save_goods_description_to_csv(extracted_data, goods_csv_path)

    print("----Extraction complete!----")



if __name__ == "__main__":

    ## TESTING THE FUNCTIONALITY --> functional testing

    input_features_list = [
    "Invoice Number", "Buyer Name", "Billing Address", "Total Amount",
    "Taxable Amount", "Tax Amount", "invoice Date", "Dated", "Pincode",
    "Vendor Name", "Description of goods", "Part no.", "Rate", "Quantity"
    ]

    test_folder = "backend/test_pdfs"
    test_files = [f for f in os.listdir(test_folder) if f.endswith(".PDF")]

    for pdf_file in test_files:
        print(f"\n\n==== Now processing: {pdf_file} ====")
        uploaded_pdf_path = os.path.join(test_folder, pdf_file)
        main(uploaded_pdf_path, input_features_list)

