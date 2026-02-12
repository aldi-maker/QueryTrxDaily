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

    # Filter berdasarkan tanggal
    if 'Date/Time Tran Local' in df.columns:
        df['Date/Time Tran Local'] = pd.to_datetime(df['Date/Time Tran Local'], errors='coerce')

        min_date = df['Date/Time Tran Local'].min().date()
        max_date = df['Date/Time Tran Local'].max().date()

        st.subheader("Filter Berdasarkan Rentang Tanggal")
        start_date, end_date = st.date_input(
            "Pilih rentang tanggal",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )

        mask = (df['Date/Time Tran Local'].dt.date >= start_date) & (df['Date/Time Tran Local'].dt.date <= end_date)
        filtered_df = df.loc[mask]

        st.write(f"Menampilkan data dari {start_date} sampai {end_date}")
        st.dataframe(filtered_df)
        st.write("Jumlah hasil:", len(filtered_df))
    else:
        st.error("Kolom 'Date/Time Tran Local' tidak ditemukan. Cek header Excel.")