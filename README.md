### 📊 Donation Data Cleaner
A Streamlit-based data cleaning tool designed to standardize messy Excel donation data into a clean, structured format ready for analysis or data warehousing.

### 🚀 Overview
The Donation Data Cleaner allows users to upload Excel workbooks containing donation records across multiple sheets.

It automatically:
- Detects headers (even if misplaced)
- Maps inconsistent column names
- Cleans and standardizes data
- Validates required fields
- Splits output into clean and rejected datasets

This tool is especially useful for nonprofits, analysts, or data engineers dealing with inconsistent donor data formats.

### 🧠 Key Features

🔍 Smart Column Mapping
- Uses a predefined dictionary for common column name variations
- Falls back on fuzzy matching (fuzzywuzzy) for flexibility
- 
📑 Header Detection
- Automatically identifies the correct header row (even if not the first row)

🧹 Data Standardization
- Names → Proper case
- States → Uppercase
- ZIP codes → 5-digit format
- Donation amounts → Numeric
- Dates → YYYY-MM-DD
- ✅ Data Validation

Ensures all required fields are present:
- First Name
- Last Name
- Address
- City
- State
- ZIP Code
- Donation Date
- Donation Amount
- Client (derived from sheet name)

Rows missing any required field are automatically rejected.

### 📂 Input Requirements
- File type: .xlsx
- Each sheet represents a client
- Column names can vary — the app will attempt to map them
  
### 📤 Output
- ✅ Cleaned Data
- Fully standardized dataset
- Ready for downstream use
- Downloadable as CSV
- ⚠️ Rejected Data
- Rows missing required fields or failing validation
- Provided for review and correction
- 📋 Sheet Status Report
- Displays processing results for each sheet:
- Processed
- Skipped (empty / no header)
- Rejected (missing columns or invalid rows)

### 🛠 Installation
``` bash
pip install streamlit pandas fuzzywuzzy python-dateutil openpyxl
```

### ▶️ Running the App
``` bash
streamlit run app.py
```
Then open your browser at:
- http://localhost:8501

🧩 How It Works
- Upload Excel file
- App loops through each sheet
- Detects header row
- Maps columns using dictionary + fuzzy matching
- Cleans and standardizes values
- Validates required fields

Outputs:
- Clean dataset
- Rejected dataset
- Status summary

### ⚙️ Configuration
- Required Columns

``` python
REQUIRED_COLUMNS = [
    "First", "Last", "Address1", "City",
    "State", "Zip", "DonationDate", "DonationAmount", "Client"
]
```

- Column Mapping Dictionary
- Customizable in COLUMN_DICT to support additional naming variations.
- Fuzzy Matching Threshold
- FUZZY_THRESHOLD = 80
- Adjust to make matching stricter or more lenient.

### ⚠️ Known Limitations
- Extremely inconsistent or ambiguous column names may fail mapping
- Date parsing relies on dateutil and may misinterpret unusual formats
- ZIP code cleaning assumes numeric values
  
###💡 Future Improvements
- Add UI for manual column mapping override
- Support CSV uploads
- Improve error reporting for rejected rows
- Add logging/export of transformation steps
- Integrate database export (e.g., PostgreSQL, Snowflake)

### 👩‍💻 Author
- Jessica Tran

Jessica Tran
Computer Science / Data Science
