# 🧾 AI-Powered Invoice Data Extraction System

This project is a lightweight, end-to-end solution to extract structured data from PDF invoices using Google Gemini LLM. It converts unstructured invoice text into clean, structured JSON and stores the output into CSV and PostgreSQL for easy analysis.

---

## 📌 Project Overview

Traditional OCR tools often miss the context or structure of complex invoice layouts. This project uses a custom pipeline combining PDF text extraction, Gemini LLM-based parsing, and database sync to create a clean, scalable data extraction workflow.

---

## 🚀 Features

- ✅ Extracts invoice data from scanned/digital PDFs  
- 🤖 Uses Google Gemini LLM for structured JSON output  
- 📄 Outputs two clean CSVs: `Invoice Summary` and `Goods Description`  
- 🔁 CSV-to-PostgreSQL synchronization  
- ⚡ Lightweight, runs on 4GB RAM setup  
- 🔐 Secure & modular code structure

---

## 🧱 Tech Stack

| Layer           | Tools/Tech Used                         |
|----------------|------------------------------------------|
| PDF Extraction  | `PyMuPDF (fitz)`                        |
| AI Model        | Google Gemini API (LLM)                 |
| Data Processing | Python, Pandas, JSON, CSV               |
| Storage         | CSV, PostgreSQL                         |
| Automation      | Custom Python scripts (sync + parsing)  |

---

## 🧭 Workflow

1. 📤 **User Uploads Invoice (PDF)**  
2. 🔍 **Raw Text Extraction** using `fitz` (PyMuPDF)  
3. 🤖 **Gemini LLM** processes text → returns structured **Invoice JSON**  
4. 📂 JSON split into:
   - `invoice_summary.csv`
   - `goods_description.csv`  
5. 🔁 CSVs are synced with **PostgreSQL database**

---

## 🛠️ Project Setup

### 1. Clone Repository
```bash
git clone https://github.com/Brigu09/Invoice_Data_Extractor_Ai_System
cd invoice-ai-extractor
