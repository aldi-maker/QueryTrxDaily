import streamlit as st
import pandas as pd
import re
import zipfile
import io
from datetime import timedelta

def run_parser():
    st.title("Parser EJ HITACHI (Upload Multiple ZIP)")

    # Upload banyak ZIP sekaligus
    uploaded_zips = st.file_uploader(
        "Upload file ZIP berisi EJ (.zip)", type=["zip"], accept_multiple_files=True
    )

    use_cutoff = st.checkbox("Aktifkan filter 10 menit terakhir")

    all_txn, all_cass, all_denom = [], [], []

    if uploaded_zips:
        for uploaded_zip in uploaded_zips:
            with zipfile.ZipFile(io.BytesIO(uploaded_zip.read())) as z:
                txt_files = [f for f in z.namelist() if f.endswith(".1")]
                st.write(f"ZIP {uploaded_zip.name} berisi {len(txt_files)} file EJ.")

                for file in txt_files:
                    content = z.read(file).decode("utf-8", errors="ignore")
                    lines = content.splitlines()

                    parsed_txn, parsed_cass, parsed_denom = [], [], []
                    current_txn = {}

                    for i, line in enumerate(lines):
                        # Header tanggal & jam
                        header_match = re.search(r"(\d{4}/\d{2}/\d{2})\s+(\d{2}:\d{2}:\d{2})", line)
                        if header_match:
                            current_txn["Tanggal"] = header_match.group(1)
                            current_txn["Jam"] = header_match.group(2)

                        # Machine ID
                        machine_match = re.search(r"MACHINE NO:(\d+)", line)
                        if machine_match:
                            current_txn["MachineID"] = machine_match.group(1)

                        # Total counted
                        total_counted = re.search(r"TOTAL COUNTED\s*=\s*RM([\d\.]+)", line)
                        if total_counted:
                            current_txn["TotalCounted"] = float(total_counted.group(1))

                        # Reject count
                        reject_match = re.search(r"REJECT COUNT\s*=\s*(\d+)", line)
                        if reject_match:
                            current_txn["RejectCount"] = int(reject_match.group(1))

                        # Cash deposit trx
                        deposit_match = re.search(r"TOTAL\s*=\s*RM([\d\.]+)", line)
                        if deposit_match:
                            current_txn["DepositAmount"] = float(deposit_match.group(1))

                        # Account number
                        acc_match = re.search(r"ACC\. NO\.\s*:\s*(\d+)", line)
                        if acc_match:
                            current_txn["AccountNo"] = acc_match.group(1)

                        # End transaksi
                        if "Trxn End" in line:
                            parsed_txn.append(current_txn)
                            current_txn = {}

                        # Bagian CASS/CURR/TOTAL
                        if "NOTES STORED INTO:" in line or "NOTES DISPENSED FROM:" in line:
                            cass_line = lines[i+1] if i+1 < len(lines) else ""
                            curr_line = lines[i+2] if i+2 < len(lines) else ""
                            total_line = lines[i+3] if i+3 < len(lines) else ""

                            cass_values = re.findall(r"\d+", cass_line)
                            curr_values = re.findall(r"\d+", curr_line)
                            total_values = re.findall(r"\d+", total_line)

                            ts = None
                            if current_txn.get("Tanggal") and current_txn.get("Jam"):
                                ts = pd.to_datetime(
                                    str(current_txn["Tanggal"]) + " " + str(current_txn["Jam"]),
                                    errors="coerce"
                                )

                            parsed_cass.append({
                                "File": f"{uploaded_zip.name}/{file}",
                                "Tanggal": current_txn.get("Tanggal"),
                                "Jam": current_txn.get("Jam"),
                                "MachineID": current_txn.get("MachineID"),
                                "Timestamp": ts,
                                "CASS": cass_values,
                                "CURR": curr_values,
                                "TOTAL": total_values
                            })

                        # Bagian Denom
                        denom_match = re.search(r"RM\s*([0-9]+\.00)\s*X\s*(\d+)", line)
                        if denom_match:
                            ts = None
                            if current_txn.get("Tanggal") and current_txn.get("Jam"):
                                ts = pd.to_datetime(
                                    str(current_txn["Tanggal"]) + " " + str(current_txn["Jam"]),
                                    errors="coerce"
                                )
                            parsed_denom.append({
                                "File": f"{uploaded_zip.name}/{file}",
                                "Tanggal": current_txn.get("Tanggal"),
                                "Jam": current_txn.get("Jam"),
                                "MachineID": current_txn.get("MachineID"),
                                "Timestamp": ts,
                                "Denom": denom_match.group(1),
                                "Jumlah": int(denom_match.group(2))
                            })

                    # DataFrame transaksi
                    df_txn = pd.DataFrame(parsed_txn)
                    if not df_txn.empty:
                        df_txn["Timestamp"] = pd.to_datetime(
                            df_txn["Tanggal"].astype(str) + " " + df_txn["Jam"].astype(str),
                            errors="coerce"
                        )
                        df_txn["File"] = f"{uploaded_zip.name}/{file}"
                        if use_cutoff:
                            max_time = df_txn["Timestamp"].max()
                            cutoff_time = max_time - timedelta(minutes=10)
                            df_txn = df_txn[df_txn["Timestamp"] >= cutoff_time]
                        all_txn.append(df_txn)

                    # DataFrame CASS
                    df_cass = pd.DataFrame(parsed_cass)
                    if not df_cass.empty:
                        if use_cutoff and "Timestamp" in df_cass.columns:
                            max_time = df_cass["Timestamp"].max()
                            cutoff_time = max_time - timedelta(minutes=10)
                            df_cass = df_cass[df_cass["Timestamp"] >= cutoff_time]
                        all_cass.append(df_cass)

                    # DataFrame Denom
                    df_denom = pd.DataFrame(parsed_denom)
                    if not df_denom.empty:
                        if use_cutoff and "Timestamp" in df_denom.columns:
                            max_time = df_denom["Timestamp"].max()
                            cutoff_time = max_time - timedelta(minutes=10)
                            df_denom = df_denom[df_denom["Timestamp"] >= cutoff_time]
                        all_denom.append(df_denom)

        # Gabungkan semua file dari semua ZIP
        if all_txn:
            df_all_txn = pd.concat(all_txn, ignore_index=True)
            st.subheader("Summary Semua Transaksi")
            st.dataframe(df_all_txn)

        if all_cass:
            df_all_cass = pd.concat(all_cass, ignore_index=True)
            st.subheader("Summary Semua CASS/CURR/TOTAL")
            st.dataframe(df_all_cass)

        if all_denom:
            df_all_denom = pd.concat(all_denom, ignore_index=True)
            df_pivot = df_all_denom.pivot_table(
                index=["File","Tanggal","Jam","MachineID","Timestamp"],
                columns="Denom",
                values="Jumlah",
                aggfunc="sum",
                fill_value=0
            ).reset_index()
            df_pivot = df_pivot.rename(columns={
                "10.00": "Denom10",
                "20.00": "Denom20",
                "50.00": "Denom50",
                "100.00": "Denom100"
            })
            st.subheader("Summary Semua Denominasi (Pivot)")
            st.dataframe(df_pivot)
    else:
        st.info("Silakan upload satu atau lebih file ZIP berisi EJ ATM.")

# Jika file dijalankan langsung, panggil run_parser()
if __name__ == "__main__":
    run_parser()
