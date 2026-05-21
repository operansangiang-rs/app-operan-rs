import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="Operan RS",
    layout="wide"
)

st.title("Operan RS")

# =========================
# KONEKSI GOOGLE SHEETS
# =========================
try:
    conn = st.connection(
        "gsheets",
        type=GSheetsConnection
    )

except Exception as e:
    st.error(f"Gagal koneksi Google Sheets: {e}")
    st.stop()

# =========================
# NAMA WORKSHEET
# =========================
WORKSHEET = "Database_Operan_Shift"

# =========================
# LOAD DATA
# =========================
try:
    df = conn.read(
        worksheet=WORKSHEET,
        ttl=0
    )

    # Jika sheet kosong
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

    submit = st.form_submit_button("Simpan Data")

# =========================
# SIMPAN DATA
# =========================
if submit:

    try:

        # Data baru
        data_baru = pd.DataFrame([{
            "Tanggal": str(tanggal),
            "Ruangan": ruangan,
            "Keterangan": keterangan
        }])

        # Gabungkan data lama + baru
        df_baru = pd.concat(
            [df, data_baru],
            ignore_index=True
        )

        # Reset index
        df_baru = df_baru.reset_index(drop=True)

        # Simpan ke Google Sheets
        conn.update(
            worksheet=WORKSHEET,
            data=df_baru
        )

        st.success("Data berhasil disimpan")

        st.rerun()

    except Exception as e:

        st.error(f"Gagal menyimpan data: {e}")

# =========================
# TAMPILKAN DATA
# =========================
st.subheader("Database Operan Shift")

st.dataframe(
    df,
    use_container_width=True
)
