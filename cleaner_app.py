import streamlit as st
import pandas as pd
from fuzzywuzzy import process
import re
from dateutil import parser

# ---------------------------
# CONFIG / DATA DICTIONARY
# ---------------------------
REQUIRED_COLUMNS = [
    "First", "Last", "Address1", "City",
    "State", "Zip", "DonationDate", "DonationAmount", "Client"
]

COLUMN_DICT = {
    "First": ["First", "FName", "F. Name", "FirstName", "fname"],
    "Last": ["Last", "LastName", "LName", "last_name", "lname"],
    "Address1": ["Address", "Address1", "Street", "addr"],
    "City": ["City", "Town"],
    "State": ["ST", "State"],
    "Zip": ["Zip", "Zipcode", "PostalCode", "zip_code", "postal"],
    "DonationDate": ["DonationDate", "GiftDate", "Date", "donationdate"],
    "DonationAmount": ["Amount", "DonationAmount", "GiftAmount", "donationamount"]
}

FUZZY_THRESHOLD = 80

# ---------------------------
# HELPER FUNCTIONS
# ---------------------------
def normalize_col_name(name: str) -> str:
    return re.sub(r'[^a-z0-9]', '', str(name).lower())

def map_columns(columns):
    mapped = {}
    norm_columns = {normalize_col_name(col): col for col in columns}

    for req_col in REQUIRED_COLUMNS:
        if req_col == "Client":
            continue  # handled separately

        # Dictionary match (normalized)
        found = False
        for variant in COLUMN_DICT.get(req_col, []):
            norm_variant = normalize_col_name(variant)
            if norm_variant in norm_columns:
                mapped[req_col] = (norm_columns[norm_variant], "dict")
                found = True
                break

        if not found:
            # Fuzzy fallback
            match = process.extractOne(req_col, columns)
            if match:
                col, score = match
                if score >= FUZZY_THRESHOLD:
                    mapped[req_col] = (col, "fuzzy")

    return mapped

def detect_header(df, max_rows=10):
    if df.empty:
        return None

    norm_req = [normalize_col_name(c) for c in REQUIRED_COLUMNS if c != "Client"]

    best_row = None
    best_score = 0

    for i in range(min(max_rows, len(df))):
        row = [normalize_col_name(str(c)) for c in df.iloc[i]]

        score = sum(
            1 for cell in row
            for req in norm_req
            if req in cell or cell in req
        )

        if score > best_score:
            best_score = score
            best_row = i

    if best_score >= 3:
        return best_row

    return None

def clean_sheet(df, client_name="Unknown"):
    if df.empty:
        return pd.DataFrame(), pd.DataFrame(), {}, "empty"

    header_row = detect_header(df)
    if header_row is None or header_row >= len(df):
        return pd.DataFrame(), df, {}, "no_header"

    # Set header
    df.columns = df.iloc[header_row]
    df = df[header_row + 1:].reset_index(drop=True)

    if df.empty:
        return pd.DataFrame(), pd.DataFrame(), {}, "empty_after_header"

    mapped = map_columns(df.columns.tolist())

    missing_cols = [c for c in REQUIRED_COLUMNS if c not in mapped and c != "Client"]
    if missing_cols:
        return pd.DataFrame(), df, mapped, f"missing_columns: {missing_cols}"

    rename_dict = {v[0]: k for k, v in mapped.items()}
    df = df.rename(columns=rename_dict)

    # Add Client column BEFORE validation
    df["Client"] = str(client_name).strip()

    # Ensure all required columns exist
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            df[col] = None

    # Keep only required columns
    df = df[REQUIRED_COLUMNS]

    # ---------------------------
    # STANDARDIZATION
    # ---------------------------
    df['First'] = df['First'].apply(lambda x: str(x).title() if pd.notnull(x) else None)
    df['Last'] = df['Last'].apply(lambda x: str(x).title() if pd.notnull(x) else None)
    df['State'] = df['State'].apply(lambda x: str(x).upper() if pd.notnull(x) else None)
    df['City'] = df['City'].apply(lambda x: str(x).title() if pd.notnull(x) else None)
    df['Address1'] = df['Address1'].apply(lambda x: str(x).strip() if pd.notnull(x) else None)

    df['Zip'] = df['Zip'].apply(
        lambda x: str(int(float(x))).zfill(5)
        if pd.notnull(x) and str(x).replace('.', '').isdigit()
        else None
    )

    df['DonationAmount'] = df['DonationAmount'].apply(
        lambda x: float(re.sub(r'[^0-9.-]', '', str(x)))
        if pd.notnull(x) else None
    )

    df['DonationDate'] = df['DonationDate'].apply(
        lambda x: parser.parse(str(x)).strftime("%Y-%m-%d")
        if pd.notnull(x) else None
    )

    # ---------------------------
    # VALIDATION
    # ---------------------------
    clean = df.dropna(subset=REQUIRED_COLUMNS)
    rejected = df[df[REQUIRED_COLUMNS].isna().any(axis=1)]

    status = "passed" if not clean.empty else "rejected"

    return clean, rejected, mapped, status

# ---------------------------
# STREAMLIT UI
# ---------------------------
st.set_page_config(page_title="Donation Cleaner", layout="wide")
st.title("📊 Donation Data Cleaner")
st.write("Upload Excel workbooks and get a clean CSV for your data warehouse.")

uploaded_file = st.file_uploader("Upload Excel File (.xlsx)", type=["xlsx"])

if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)

    all_cleaned = []
    all_rejected = []
    sheet_statuses = []

    for sheet in xls.sheet_names:
        st.write(f"Processing sheet: **{sheet}**...")

        # 🔥 CRITICAL FIX: header=None
        df = pd.read_excel(xls, sheet_name=sheet, dtype=str, header=None)

        clean, rejected, mapping, status = clean_sheet(df, client_name=sheet)

        if status == "empty":
            st.info(f"⏭ Skipped '{sheet}': Empty")
            continue

        elif status == "no_header":
            st.warning(f"⏭ Skipped '{sheet}': No header found")
            continue

        elif status.startswith("missing_columns"):
            st.warning(f"⚠️ '{sheet}' rejected: {status}")
            all_rejected.append(rejected)
            sheet_statuses.append((sheet, status))
            continue

        elif status == "rejected":
            st.warning(f"⚠️ '{sheet}': All rows rejected")
            all_rejected.append(rejected)
            sheet_statuses.append((sheet, status))
            continue

        else:
            st.success(f"✅ '{sheet}' processed")
            all_cleaned.append(clean)

            if not rejected.empty:
                st.warning(f"⚠️ '{sheet}' has {len(rejected)} rejected rows")
                all_rejected.append(rejected)

        sheet_statuses.append((sheet, status))

    # ---------------------------
    # OUTPUTS
    # ---------------------------
    if all_cleaned:
        final_cleaned = pd.concat(all_cleaned, ignore_index=True)

        st.subheader("✅ Cleaned Data")
        st.dataframe(final_cleaned)

        st.download_button(
            "📥 Download Cleaned CSV",
            final_cleaned.to_csv(index=False).encode("utf-8"),
            "cleaned_donations.csv",
            "text/csv"
        )
    else:
        st.warning("No valid data found.")

    if all_rejected:
        final_rejected = pd.concat(all_rejected, ignore_index=True)

        st.subheader("⚠️ Rejected Rows")
        st.dataframe(final_rejected)

        st.download_button(
            "📥 Download Rejected CSV",
            final_rejected.to_csv(index=False).encode("utf-8"),
            "rejected_donations.csv",
            "text/csv"
        )

    st.subheader("📋 Sheet Statuses")
    for sheet, status in sheet_statuses:
        st.write(f"**{sheet}** → {status}")