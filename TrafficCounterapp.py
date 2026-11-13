import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Traffic Counter Aplikom", page_icon="🚗", layout="centered")

st.title("🚗 Aplikasi Traffic Counter (Survei Lalu Lintas)")
st.markdown("Gunakan tombol di bawah untuk mencatat volume kendaraan secara *real-time*.")

# Inisialisasi state penyimpanan data sementara
if 'counts' not in st.session_state:
    st.session_state.counts = {"Sepeda Motor": 0, "Mobil Pribadi": 0, "Truk / Bus": 0}
if 'history' not in st.session_state:
    st.session_state.history = []

# Tombol interaktif pencatatan kendaraan
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🏍️ Motor", use_container_width=True):
        st.session_state.counts["Sepeda Motor"] += 1
        st.session_state.history.append({"Waktu": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Kendaraan": "Sepeda Motor"})
with col2:
    if st.button("🚗 Mobil", use_container_width=True):
        st.session_state.counts["Mobil Pribadi"] += 1
        st.session_state.history.append({"Waktu": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Kendaraan": "Mobil Pribadi"})
with col3:
    if st.button("🚛 Truk/Bus", use_container_width=True):
        st.session_state.counts["Truk / Bus"] += 1
        st.session_state.history.append({"Waktu": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Kendaraan": "Truk / Bus"})

st.divider()

# Tampilkan Rekapitulasi
st.subheader("📊 Rekapitulasi Volume Kendaraan")
metric_col1, metric_col2, metric_col3 = st.columns(3)
metric_col1.metric("Sepeda Motor", st.session_state.counts["Sepeda Motor"])
metric_col2.metric("Mobil Pribadi", st.session_state.counts["Mobil Pribadi"])
metric_col3.metric("Truk / Bus", st.session_state.counts["Truk / Bus"])

# Tombol Reset
if st.button("🔄 Reset Semua Data"):
    st.session_state.counts = {"Sepeda Motor": 0, "Mobil Pribadi": 0, "Truk / Bus": 0}
    st.session_state.history = []
    st.rerun()

# Tampilkan Riwayat & Tombol Download CSV
if st.session_state.history:
    st.subheader("⏱️ Riwayat Waktu Pencatatan")
    df = pd.DataFrame(st.session_state.history)
    st.dataframe(df, use_container_width=True)

    # Ekspor ke CSV
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Data Survei (.CSV)",
        data=csv,
        file_name="hasil_survei_lalin.csv",
        mime="text/csv",
    )