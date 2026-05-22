import streamlit as st
import sqlite3
import pandas as pd
from io import BytesIO
from datetime import datetime
import pytz

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer
)

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import landscape, A4

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="Operan Shift RS Sari Asih Sangiang",
    page_icon="🏥",
    layout="wide"
)

st.title("🏥 Operan Shift RS Sari Asih Sangiang")

# =========================
# TIMEZONE
# =========================
jakarta = pytz.timezone("Asia/Jakarta")

# =========================
# DB
# =========================
@st.cache_resource
def conn_db():
    conn = sqlite3.connect("operan.db", check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

conn = conn_db()
c = conn.cursor()

# =========================
# AUTO DELETE
# =========================
try:
    c.execute("""
        DELETE FROM operan
        WHERE julianday('now') - julianday(tanggal) > 15
    """)
    conn.commit()
except Exception as e:
    print("Auto delete error:", e)

# =========================
# TABLE
# =========================
c.execute("""
CREATE TABLE IF NOT EXISTS operan (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tanggal TEXT,
    unit TEXT,
    shift TEXT,
    no_rm TEXT,
    nama_pasien TEXT,
    kamar TEXT,
    diagnosa TEXT,
    operan TEXT,
    pj_operan TEXT,
    edited_by TEXT,
    edited_at TEXT
)
""")
conn.commit()

# =========================
# SHIFT
# =========================
jam = datetime.now(jakarta).hour

if jam < 14:
    auto_shift = "Pagi"
elif jam < 21:
    auto_shift = "Sore"
else:
    auto_shift = "Malam"

# =========================
# UNIT
# =========================
unit_list = [
    "ICU","RPU LT 1","RPU LT 2","RPU LT 3 GL","RPU LT 3 GB",
    "RPU LT 4","RPU LT 5","Hemodialisa","Kamar Operasi",
    "IGD","NICU","PICU"
]

st.sidebar.title("🏥 Pilih Unit")
selected_unit = st.sidebar.selectbox("Unit", unit_list)

# =========================
# DATA
# =========================
st.subheader("📋 Data Operan")

df = pd.read_sql_query("""
SELECT *
FROM operan
WHERE unit = ?
ORDER BY id DESC
LIMIT 100
""", conn, params=(selected_unit,))

if "open_detail" not in st.session_state:
    st.session_state["open_detail"] = None

if "confirm_delete" not in st.session_state:
    st.session_state["confirm_delete"] = None

# =========================
# LOOP DATA
# =========================
for _, r in df.iterrows():

    with st.container():
        st.markdown("---")

        col1, col2, col3, col4 = st.columns(4)

        col1.write(f"📅 {r['tanggal']}")
        col2.write(f"⏱ {r['shift']}")
        col3.write(f"🆔 {r['no_rm']}")
        col4.write(f"👤 {r['nama_pasien']}")

        st.write(f"🏠 {r['kamar']} | 🧾 {r['diagnosa']} | 👨‍⚕️ {r['pj_operan']}")

        colA, colB = st.columns([1, 1])

        # =========================
        # DETAIL BUTTON
        # =========================
        if colA.button("📄 Detail", key=f"detail_{r['id']}"):
            if st.session_state["open_detail"] == r["id"]:
                st.session_state["open_detail"] = None
            else:
                st.session_state["open_detail"] = r["id"]

        # =========================
        # DELETE BUTTON (STEP 1)
        # =========================
        if colB.button("🗑 Hapus", key=f"del_{r['id']}"):
            st.session_state["confirm_delete"] = r["id"]

        # =========================
        # CONFIRM DELETE (STEP 2)
        # =========================
        if st.session_state["confirm_delete"] == r["id"]:

            st.warning(f"⚠️ Yakin ingin menghapus: {r['nama_pasien']} ?")

            col_yes, col_no = st.columns(2)

            with col_yes:
                if st.button("✅ Ya, Hapus", key=f"yes_{r['id']}"):
                    c.execute("DELETE FROM operan WHERE id=?", (r["id"],))
                    conn.commit()

                    st.session_state["confirm_delete"] = None
                    st.rerun()

            with col_no:
                if st.button("❌ Batal", key=f"no_{r['id']}"):
                    st.session_state["confirm_delete"] = None
                    st.rerun()

        # =========================
        # DETAIL CONTENT
        # =========================
        if st.session_state["open_detail"] == r["id"]:
            st.info(r["operan"])
            st.caption(f"✏️ Edit: {r['edited_by']} | {r['edited_at']}")

# =========================
# EDIT
# =========================
st.divider()
st.subheader("✏️ Edit Operan")

edit_rm = st.text_input("No RM Edit")
edit_by = st.text_input("Nama Pengedit")
edit_text = st.text_area("Operan Baru")

if st.button("Update"):

    waktu = datetime.now(jakarta).strftime("%Y-%m-%d %H:%M:%S")

    c.execute("""
        UPDATE operan
        SET operan = ?, edited_by = ?, edited_at = ?
        WHERE no_rm = ?
    """, (edit_text, edit_by, waktu, edit_rm))

    conn.commit()

    st.success("Updated")
    st.rerun()

# =========================
# FOOTER
# =========================
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #888; font-size: 12px;'>"
    "🏥 Sistem Operan Shift RS Sari Asih Sangiang<br>"
    "Developed by <b>RSD 2026</b> © All Rights Reserved"
    "</div>",
    unsafe_allow_html=True
)
