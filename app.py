import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(
    page_title="Operan RS",
    layout="wide"
)

st.title("Operan RS")

# Koneksi Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Nama worksheet
WORKSHEET = "Sheet1"

# =========================
# LOAD DATA
# =========================
try:
    df = conn.read(
        worksheet=WORKSHEET,
        usecols=list(range(20)),
        ttl=0
    )

    if df is None or df.empty:
        df = pd.DataFrame(columns=[
            "Tanggal",
            "Ruangan",
            "Keterangan"
        ])

except Exception as e:
    st.error(f"Gagal membaca data: {e}")

    df = pd.DataFrame(columns=[
        "Tanggal",
        "Ruangan",
        "Keterangan"
    ])

# =========================
# FORM INPUT
# =========================
with st.form("form_operan"):

    tanggal = st.date_input("Tanggal")
    ruangan = st.text_input("Ruangan")
    keterangan = st.text_area("Keterangan")

    submit = st.form_submit_button("Simpan")

# =========================
# SIMPAN DATA
# =========================
if submit:

    new_data = pd.DataFrame([{
        "Tanggal": str(tanggal),
        "Ruangan": ruangan,
        "Keterangan": keterangan
    }])

    updated_df = pd.concat([df, new_data], ignore_index=True)

    # Hapus index agar tidak error saat upload
    updated_df = updated_df.reset_index(drop=True)

    try:
        conn.update(
            worksheet=WORKSHEET,
            data=updated_df
        )

        st.success("Data berhasil disimpan")

        st.rerun()

    except Exception as e:
        st.error(f"Gagal menyimpan data: {e}")

# =========================
# TAMPILKAN DATA
# =========================
st.subheader("Data Operan")

st.dataframe(
    df,
    use_container_width=True
)
