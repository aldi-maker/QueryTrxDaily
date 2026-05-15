import streamlit as st
import pandas as pd
import zipfile
import re
from datetime import datetime

# Import parser Hitachi dari file eksternal
import ParsingEJ  # pastikan file ParsingEJ.py ada di folder yang sama

st.title("EJ Parser Multipage")

menu = st.sidebar.radio("Pilih Menu", ["ParsingEJ OKI", "ParsingEJ Hitachi"])

# -------------------------------
# Parsing EJ OKI
# -------------------------------
if menu == "ParsingEJ OKI":
    st.header("Parsing EJ OKI")

    uploaded_files = st.file_uploader("Upload ZIP files (OKI)", type="zip", accept_multiple_files=True)

    all_transactions, cass_summary, denom_summary = [], [], []

    def parse_cass_line(line):
        cass_dict = {}
        for part in line.split(":"):
            key = part[0]   # A, B, C, D, E, F, R
            value = int(part[1:])
            cass_dict[key] = value
        return cass_dict

    def parse_block(block_text):
        trx = {}

        # Timestamp slip
        slip_match = re.search(r"(\d{2}/\d{2}/\d{2} \d{2}:\d{2}:\d{2})", block_text)
        if slip_match:
            trx["Timestamp"] = datetime.strptime(slip_match.group(1), "%d/%m/%y %H:%M:%S")

        # Terminal ID & Sequence
        term_match = re.search(r"Terminal ID:\s*(\d+)", block_text)
        if term_match: trx["TerminalID"] = term_match.group(1)
        seq_match = re.search(r"Machine Sequence No\s*:\s*(\d+)", block_text)
        if seq_match: trx["SequenceNo"] = seq_match.group(1)

        # Amount: Deposit atau Withdrawal
        deposit_match = re.search(r"DEPOSIT\s*:\s*RM\s*([\d,\.]+)", block_text)
        withdraw_match = re.search(r"AMOUNT\s*:\s*RM\s*([\d,\.]+)", block_text)
        if deposit_match:
            trx["TotalAmount"] = float(deposit_match.group(1).replace(",", ""))
            trx["Type"] = "Deposit"
        elif withdraw_match:
            trx["TotalAmount"] = float(withdraw_match.group(1).replace(",", ""))
            trx["Type"] = "Withdrawal"

        # Surcharge
        surcharge_match = re.search(r"SURCHARGE\s*:\s*RM\s*([\d,\.]+)", block_text)
        if surcharge_match:
            trx["Surcharge"] = float(surcharge_match.group(1).replace(",", ""))

        # Kaset: ambil sesuai konteks
        withdraw_section = re.search(
            r"Banknote ejection to bucket\s*:\s*Succeeded.*?(A\d+:B\d+:C\d+:D\d+:E\d+:F\d+:R\d+)",
            block_text, flags=re.DOTALL)
        if withdraw_section:
            cm = withdraw_section.group(1)
            cass_summary.append({
                "Timestamp": trx.get("Timestamp"),
                "TerminalID": trx.get("TerminalID"),
                "Type": "Withdrawal",
                **parse_cass_line(cm)
            })

        deposit_section = re.search(
            r"Stored banknote\s*:.*?(A\d+:B\d+:C\d+:D\d+:E\d+:F\d+:R\d+)",
            block_text, flags=re.DOTALL)
        if deposit_section:
            cm = deposit_section.group(1)
            cass_summary.append({
                "Timestamp": trx.get("Timestamp"),
                "TerminalID": trx.get("TerminalID"),
                "Type": "Deposit",
                **parse_cass_line(cm)
            })

        # Denominasi
        denom_matches = re.findall(r"RM\s*(\d+)\s*[:]\s*(\d+)", block_text)
        if denom_matches:
            denom_dict = {
                "Timestamp": trx.get("Timestamp"),
                "TerminalID": trx.get("TerminalID"),
                "Type": trx.get("Type")
            }
            for d, n in denom_matches:
                denom_dict[f"RM{d}"] = int(n)
            denom_summary.append(denom_dict)

        return trx

    if uploaded_files:
        for uploaded_file in uploaded_files:
            with zipfile.ZipFile(uploaded_file) as z:
                for name in z.namelist():
                    if name.endswith(".txt") or name.endswith(".1"):
                        with z.open(name) as f:
                            text = f.read().decode("utf-8", errors="ignore")
                            blocks = re.findall(r"=>.*?TRANSACTION\s*END", text, flags=re.DOTALL)
                            for block in blocks:
                                trx = parse_block(block)
                                if trx:
                                    all_transactions.append(trx)

        df_trx = pd.DataFrame(all_transactions)
        df_cass = pd.DataFrame(cass_summary)
        df_denom = pd.DataFrame(denom_summary)

        tab1, tab2, tab3 = st.tabs(["Transaksi", "Kaset", "Denominasi"])
        with tab1:
            st.subheader("Summary Transaksi")
            st.dataframe(df_trx)
        with tab2:
            st.subheader("Summary Kaset (CASS)")
            st.dataframe(df_cass)
        with tab3:
            st.subheader("Summary Denominasi")
            st.dataframe(df_denom)

# -------------------------------
# Parsing EJ Hitachi
# -------------------------------
elif menu == "ParsingEJ Hitachi":
    st.header("Parsing EJ Hitachi")

    # Panggil fungsi parser dari file ParsingEJ.py
    ParsingEJ.run_parser()
