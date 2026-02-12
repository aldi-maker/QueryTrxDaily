import streamlit as st
import pandas as pd
import os
import glob

st.title("Query Transactions")

# Cari semua file di folder temp
files = glob.glob("temp/*.xlsx")

if not files:
    st.warning("Silakan upload file terlebih dahulu di halaman Upload.")
else:
    # Pilih file dari daftar
    filenames = [os.path.basename(f) for f in files]
    selected_file = st.selectbox("Pilih file untuk query", filenames)

    file_path = os.path.join("temp", selected_file)

    # Baca file terpilih
    df = pd.read_excel(file_path, header=4)
    df.columns = df.columns.astype(str).str.strip()

    # Preview data
    #st.subheader("Preview Data")
    #st.dataframe(df.head(20))

    # Filter berdasarkan Terminal ID
    if 'Terminal ID' in df.columns:
        terminal_ids = df['Terminal ID'].unique()
        selected_terminal = st.selectbox("Pilih Terminal ID", sorted(terminal_ids))

        filtered_df = df[df['Terminal ID'] == selected_terminal]

        st.write(f"Menampilkan data untuk Terminal ID: {selected_terminal}")
        st.dataframe(filtered_df)
        st.write("Jumlah hasil:", len(filtered_df))
    else:
        st.error("Kolom 'Terminal ID' tidak ditemukan. Cek header Excel.")