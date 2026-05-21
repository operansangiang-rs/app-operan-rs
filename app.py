import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from streamlit_gsheets import GSheetsConnection

# 1. Konfigurasi Halaman Web
st.set_page_config(page_title="Sistem Operan Shift RS Multi-Unit", layout="wide")
st.title("🏥 Sistem Informasi Operan Shift Pasien Antar Unit")

# 2. Hubungkan ke Google Sheets (Database)
conn = st.connection("gsheets", type=GSheetsConnection)

# Fungsi muat data & Auto-Delete data > 40 hari
def load_and_clean_data():
    df = conn.read(ttl="1m") # cache 1 menit agar data cepat sinkron antar HP perawat
    if df.empty:
        return df
    
    df['Tanggal'] = pd.to_datetime(df['Tanggal'])
    batas_hari = datetime.now() - timedelta(days=40)
    data_baru = df[df['Tanggal'] >= batas_hari]
    
    if len(data_baru) < len(df):
        data_baru['Tanggal'] = data_baru['Tanggal'].dt.strftime('%Y-%m-%d')
        conn.update(data=data_baru)
        st.toast("🧹 Data lama di atas 40 hari otomatis dibersihkan!", icon="🗑️")
        return data_baru
        
    return df

df_pasien = load_and_clean_data()

# Master Data untuk Pilihan Dropdown
LIST_LANTAI = ["Lantai 1", "Lantai 2", "Lantai 3", "Lantai 4", "Lantai 5"]
LIST_UNIT = ["Perawatan Umum", "ICU", "Hemodialisa (HD)", "Kamar Operasi (OK)"]

# 3. SIDEBAR: FORM INPUT OPERAN SHIFT
st.sidebar.header("✍️ Input Operan Baru")
with st.sidebar.form(key="form_operan", clear_on_submit=True):
    tgl_input = st.date_input("Tanggal", datetime.now())
    shift_input = st.selectbox("Shift", ["Pagi", "Sore", "Malam"])
    
    st.sidebar.markdown("---")
    # Input Lokasi Baru
    lantai_input = st.selectbox("Pilih Lantai", LIST_LANTAI)
    unit_input = st.selectbox("Pilih Unit / Ruangan", LIST_UNIT)
    kamar = st.text_input("Nomor Kamar / Bed (Contoh: Kamar 302 / Bed A)")
    
    st.sidebar.markdown("---")
    nama_pasien = st.text_input("Nama Pasien")
    no_rm = st.text_input("No. Rekam Medis (RM)")
    diagnosa = st.text_area("Diagnosa Medis / Masalah Utama")
    catatan = st.text_area("Catatan Operan (SBAR / Instruksi Terapi)")
    
    submit_button = st.form_submit_button(label="🚀 Simpan & Oper")

if submit_button:
    if nama_pasien and no_rm:
        new_data = pd.DataFrame([{
            "Tanggal": tgl_input.strftime('%Y-%m-%d'),
            "Shift": shift_input,
            "Lantai": lantai_input,
            "Unit_Ruangan": unit_input,
            "Nama_Pasien": nama_pasien,
            "No_RM": no_rm,
            "Kamar": kamar,
            "Diagnosa": diagnosa,
            "Catatan_Operan": catatan
        }])
        
        if not df_pasien.empty:
            df_pasien['Tanggal'] = pd.to_datetime(df_pasien['Tanggal']).dt.strftime('%Y-%m-%d')
            updated_df = pd.concat([df_pasien, new_data], ignore_index=True)
        else:
            updated_df = new_data
            
        conn.update(data=updated_df)
        st.success(f"Data operan pasien {nama_pasien} berhasil disimpan di {unit_input}!", icon="✅")
        st.rerun()
    else:
        st.error("Nama Pasien dan No. RM wajib diisi!")

# 4. HALAMAN UTAMA: FILTER DAN NAVIGASI ANTAR UNIT
st.subheader("📋 Monitoring Data Pasien Terkini")

# Filter Global (Pencarian & Shift)
col1, col2 = st.columns([2, 1])
with col1:
    search_query = st.text_input("🔍 Cari Pasien (Ketik Nama, No. RM, atau Diagnosa)")
with col2:
    filter_shift = st.multiselect("Shift", ["Pagi", "Sore", "Malam"], default=["Pagi", "Sore", "Malam"])

# MEMBUAT TAB NAVIGASI UNTUK MASING-MASING UNIT
tabs = st.tabs([f"🏢 {unit}" for unit in LIST_UNIT])

# Logika Tampilan Data di Setiap Tab
for index, unit_name in enumerate(LIST_UNIT):
    with tabs[index]:
        if not df_pasien.empty:
            # Filter data berdasarkan Unit saat ini
            df_display = df_pasien.copy()
            df_display['Tanggal'] = pd.to_datetime(df_display['Tanggal']).dt.strftime('%Y-%m-%d')
            
            # Terapkan filter Unit
            df_display = df_display[df_display['Unit_Ruangan'] == unit_name]
            
            # Terapkan filter Shift global
            df_display = df_display[df_display['Shift'].isin(filter_shift)]
            
            # Terapkan filter Pencarian global jika diisi
            if search_query:
                df_display = df_display[
                    df_display['Nama_Pasien'].str.contains(search_query, case=False, na=False) | 
                    df_display['No_RM'].str.contains(search_query, case=False, na=False) |
                    df_display['Diagnosa'].str.contains(search_query, case=False, na=False)
                ]
            
            if not df_display.empty:
                st.caption(f"Menampilkan data operan shift untuk {unit_name}")
                # Tampilkan tabel interaktif
                st.dataframe(
                    df_display.sort_values(by=["Tanggal", "Lantai", "Kamar"], ascending=[False, True, True]),
                    use_container_width=True,
                    hide_index=True,
                    column_order=["Tanggal", "Shift", "Lantai", "Kamar", "Nama_Pasien", "No_RM", "Diagnosa", "Catatan_Operan"]
                )
            else:
                st.info(f"Tidak ada data operan untuk {unit_name} saat ini.")
        else:
            st.info("Database kosong. Silakan masukkan data pasien di sidebar.")
