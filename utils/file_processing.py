# utils/file_processing.py

import pandas as pd

def bersihkan_excel(df):
    """
    Membersihkan DataFrame dari file Excel SAP:
    - Konversi kolom 'Total of Reporting Period' ke angka (float).
    - Buang baris yang kosong (NaN) atau 0 di kolom 'Total of Reporting Period'.
    - Data asli tetap aman, hanya diproses di memori.
    """
    df_clean = df.copy()

    # Cek apakah kolom yang diperlukan ada
    if 'Total of Reporting Period' in df_clean.columns:
        # Konversi kolom menjadi float (jika error di-coerce jadi NaN)
        df_clean['Total of Reporting Period'] = pd.to_numeric(df_clean['Total of Reporting Period'], errors='coerce')

        # Buang baris yang NaN
        df_clean = df_clean[df_clean['Total of Reporting Period'].notna()]

        # Buang baris yang nilainya 0
        df_clean = df_clean[df_clean['Total of Reporting Period'] != 0]

        # Reset index biar rapih
        df_clean = df_clean.reset_index(drop=True)

    else:
        print('❌ Kolom \"Total of Reporting Period\" tidak ditemukan di file Excel.')

    return df_clean

def hitung_pembagian(df_bersih, porsia, porsib):
    """
    Hitung total Laba/Rugi dan pembagian ke dua entitas.
    """
    total_lr = df_bersih['Total of Reporting Period'].sum()
    nilai_a = total_lr * porsia
    nilai_b = total_lr * porsib
    return total_lr, nilai_a, nilai_b
