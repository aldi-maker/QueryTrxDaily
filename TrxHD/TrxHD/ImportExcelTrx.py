import streamlit as st
import pandas as pd
import os
import time

st.title("Upload Excel Transactions")

# Buat folder temp jika belum ada
os.makedirs("temp", exist_ok=True)

uploaded_file = st.file_uploader("Upload Excel", type=["xlsx", "xls"])

if uploaded_file is not None:
    # Buat nama unik: timestamp + nama file asli
    filename = f"{int(time.time())}_{uploaded_file.name}"
    file_path = os.path.join("temp", filename)

    # Simpan file ke disk
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Baca file untuk preview
    df = pd.read_excel(file_path, header=4)
    df.columns = df.columns.astype(str).str.strip()

    st.success(f"File {uploaded_file.name} berhasil diupload dan disimpan.")
    #st.write("Preview Data:")
    #st.dataframe(df.head())