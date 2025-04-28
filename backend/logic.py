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
    return text


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


## FUNCTION - 4 = MAIN FUNCTION -> ORCHESTRATOR THE ENTIRE WORKFLOW

def main(uploaded_pdf_path, input_features_list):

    print("----Starting the Extraction Process...-----")

    pdf_text = extract_text_from_pdf(uploaded_pdf_path)

    print("PDF Text Txtraction Complete!")

    input_prompt = f"""
    You are an expert at reading invoices.
    Extract the following fields from the invoice PDF:
    {input_features_list}.

    ⚡ Important:
    - Return ONLY the output strictly as a valid JSON object.
    - Do not add any introduction, explanation, or notes.
    - The JSON should look like this:

    {{
    "Invoice Number": "[value]",
    "Date": "[value]",
    "Total Amount": "[value]",
    "Vendor Name": "[value]"
    }}

    Replace the field names with the actual fields requested, and [value] with the extracted value.
    Do not include any extra text outside the JSON brackets.
    """

    print("----Getting Response...----")

    response_text = get_gemini_response(input_prompt, pdf_text)

    print("Model Response Received!")
    print(response_text)

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
    
    print("----Getting the Expected JSON Response After Cleaning...----")
    print(response_text)
    

    ## PARSE THE JSON RESPONSE
    try:
        extracted_data = json.loads(response_text)
    except json.JSONDecodeError as e:
        print("Failed to parse the extracted data. Please check the Gemini output.")
        print(f"Error: {e}")
        return
    
    print("JSON response parsed successfully!")
    print(extracted_data)
    

    save_to_csv(extracted_data, csv_path)

    if "Description of goods" in extracted_data:
        goods_description = extracted_data["Description of goods"]
        goods_df = pd.DataFrame({"Description of Goods": [goods_description]})

        if os.path.exists(goods_csv_path) and os.path.getsize(goods_csv_path) > 0:
            existing_goods_df = pd.read_csv(goods_csv_path)
            updated_goods_df = pd.concat([existing_goods_df, goods_df], ignore_index=True)
        else:
            updated_goods_df = goods_df

        updated_goods_df.to_csv(goods_csv_path, index=False)
        print(f"Goods description saved successfully to {goods_csv_path}")
    else:
        print("No 'Description of goods' found in the extracted data.")



    print("----Extraction complete!----")



if __name__ == "__main__":

    ## TESTING THE FUNCTIONALITY
    uploaded_pdf_path = "data/multiple_product_data.pdf"  
    input_features_list = ["Invoice Number", "Buyer Name", "Billing Address", "Total Amount", "Taxable Amount", "Tax Amount", "invoice Date", "Dated", "Pincode", "Vendor Name", " Description of goods", "Part no.", "Rate", "Quantity"] 

    main(uploaded_pdf_path, input_features_list)

