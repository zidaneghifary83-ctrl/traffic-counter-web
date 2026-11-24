import streamlit as st
import pandas as pd
from datetime import datetime
import time

# Konfigurasi halaman utama
st.set_page_config(
    page_title="Traffic Counter Pro - Teknik Sipil",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS untuk mempercantik kartu, tombol, dan tipografi
st.markdown("""
<style>
    .metric-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 18px 20px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
        border-left: 6px solid #0284c7;
        margin-bottom: 12px;
    }
    .metric-card.motor { border-left-color: #0284c7; }
    .metric-card.mobil { border-left-color: #10b981; }
    .metric-card.truk { border-left-color: #f59e0b; }
    .metric-card.total {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #ffffff;
        border-left-color: #38bdf8;
    }
    .metric-card.smp {
        background: linear-gradient(135deg, #064e3b 0%, #065f46 100%);
        color: #ffffff;
        border-left-color: #34d399;
    }
    .metric-card.ds-aman {
        background: linear-gradient(135deg, #0f766e 0%, #115e59 100%);
        color: #ffffff;
        border-left-color: #5eead4;
    }
    .metric-card.ds-waspada {
        background: linear-gradient(135deg, #b45309 0%, #92400e 100%);
        color: #ffffff;
        border-left-color: #fcd34d;
    }
    .metric-card.ds-jenuh {
        background: linear-gradient(135deg, #991b1b 0%, #7f1d1d 100%);
        color: #ffffff;
        border-left-color: #fca5a5;
    }
    .metric-title {
        font-size: 0.80rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #64748b;
        margin-bottom: 4px;
    }
    .metric-card.total .metric-title,
    .metric-card.smp .metric-title,
    .metric-card.ds-aman .metric-title,
    .metric-card.ds-waspada .metric-title,
    .metric-card.ds-jenuh .metric-title {
        color: #e2e8f0;
    }
    .metric-value {
        font-size: 1.9rem;
        font-weight: 800;
        color: #0f172a;
        line-height: 1.1;
    }
    .metric-card.total .metric-value,
    .metric-card.smp .metric-value,
    .metric-card.ds-aman .metric-value,
    .metric-card.ds-waspada .metric-value,
    .metric-card.ds-jenuh .metric-value {
        color: #ffffff;
    }
    .metric-sub {
        font-size: 0.78rem;
        color: #64748b;
        margin-top: 6px;
    }
    .metric-card.total .metric-sub,
    .metric-card.smp .metric-sub,
    .metric-card.ds-aman .metric-sub,
    .metric-card.ds-waspada .metric-sub,
    .metric-card.ds-jenuh .metric-sub {
        color: #f1f5f9;
    }

    div.stButton > button {
        height: 3.6rem;
        font-size: 1.05rem;
        font-weight: 700;
        border-radius: 10px;
        transition: all 0.2s ease;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 14px rgba(0,0,0,0.12);
    }
</style>
""", unsafe_allow_html=True)

# Inisialisasi state data
if 'counts' not in st.session_state:
    st.session_state.counts = {"Sepeda Motor": 0, "Mobil Pribadi": 0, "Truk / Bus": 0}
if 'history' not in st.session_state:
    st.session_state.history = []
if 'survey_start_time' not in st.session_state:
    st.session_state.survey_start_time = None
if 'interval_minutes' not in st.session_state:
    st.session_state.interval_minutes = 15

# --- SIDEBAR: INFORMASI SURVEI, EMP, KAPASITAS & KONTROL ---
with st.sidebar:
    st.header("📍 Detail Lokasi Survei")
    ruas_jalan = st.text_input("Nama Ruas Jalan", placeholder="Contoh: Jl. Pemuda Magelang")
    arah_arus = st.selectbox("Arah Pergerakan", ["Utara → Selatan", "Selatan → Utara", "Timur → Barat", "Barat → Timur"])
    surveyor = st.text_input("Nama Surveyor", placeholder="Masukkan nama...")

    st.divider()
    st.subheader("📐 Faktor EMP (Satuan Mobil Penumpang)")
    st.caption("Sesuaikan nilai EMP dengan kondisi/tipe jalan survei.")
    emp_mc = st.number_input("EMP Sepeda Motor (MC)", min_value=0.05, max_value=2.0, value=0.25, step=0.05)
    emp_lv = st.number_input("EMP Kendaraan Ringan (LV)", min_value=0.5, max_value=3.0, value=1.00, step=0.05)
    emp_hv = st.number_input("EMP Kendaraan Berat (HV)", min_value=1.0, max_value=5.0, value=1.20, step=0.05)

    st.divider()
    st.subheader("🚦 Kapasitas & Derajat Kejenuhan (DS)")
    kapasitas_c = st.number_input(
        "Kapasitas Jalan, C (smp/jam)",
        min_value=100.0,
        max_value=20000.0,
        value=2500.0,
        step=50.0,
        help="Masukkan kapasitas jalan (C) dalam satuan smp/jam sesuai hasil perhitungan PKJI/MKJI."
    )
    metode_q_jam = st.radio(
        "Basis konversi arus ke smp/jam (Q):",
        ["Berdasarkan durasi interval (menit)", "Input durasi survei manual (menit)"],
        index=0
    )
    if metode_q_jam == "Input durasi survei manual (menit)":
        durasi_survei_menit = st.number_input("Durasi pencatatan (menit)", min_value=1.0, max_value=1440.0, value=15.0, step=1.0)
    else:
        durasi_survei_menit = None

    st.divider()
    st.subheader("⏱️ Durasi & Interval Survei")
    interval_opt = st.selectbox("Target Interval Rekap (menit)", [5, 10, 15, 30, 60], index=2)
    st.session_state.interval_minutes = interval_opt

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        if st.button("▶️ Mulai Timer", use_container_width=True):
            st.session_state.survey_start_time = time.time()
            st.toast("Timer survei dimulai!", icon="⏱️")
            st.rerun()
    with col_t2:
        if st.button("⏹️ Stop Timer", use_container_width=True):
            st.session_state.survey_start_time = None
            st.toast("Timer dihentikan.", icon="⏹️")
            st.rerun()

    if st.session_state.survey_start_time is not None:
        elapsed_sec = int(time.time() - st.session_state.survey_start_time)
        mins, secs = divmod(elapsed_sec, 60)
        hrs, mins = divmod(mins, 60)
        st.info(f"⏳ Durasi berjalan: **{hrs:02d}:{mins:02d}:{secs:02d}** (Interval target: {interval_opt} mnt)")

    st.divider()
    st.subheader("⚙️ Kontrol Data")

    if st.button("↩️ Batalkan Terakhir (Undo)", use_container_width=True):
        if st.session_state.history:
            last_entry = st.session_state.history.pop()
            kategori_terakhir = last_entry["Kendaraan"]
            if st.session_state.counts[kategori_terakhir] > 0:
                st.session_state.counts[kategori_terakhir] -= 1
            st.toast(f"Dibatalkan: 1 {kategori_terakhir}", icon="↩️")
            st.rerun()
        else:
            st.warning("Belum ada data untuk dibatalkan.")

    konfirmasi_reset = st.checkbox("Aktifkan tombol Reset")
    if st.button("🔄 Reset Semua Data", disabled=not konfirmasi_reset, use_container_width=True):
        st.session_state.counts = {"Sepeda Motor": 0, "Mobil Pribadi": 0, "Truk / Bus": 0}
        st.session_state.history = []
        st.session_state.survey_start_time = None
        st.rerun()

# --- AREA UTAMA ---
st.title("🚦 Traffic Counter Pro")
lokasi_info = f"**Lokasi:** {ruas_jalan if ruas_jalan else 'Belum diisi'} | **Arah:** {arah_arus} | **Kapasitas (C):** {kapasitas_c:,.0f} smp/jam"
if surveyor:
    lokasi_info += f" | **Surveyor:** {surveyor}"
st.caption(lokasi_info)

st.markdown("### 1. Panel Penghitung Kendaraan")
col_btn1, col_btn2, col_btn3 = st.columns(3)

emp_map = {
    "Sepeda Motor": emp_mc,
    "Mobil Pribadi": emp_lv,
    "Truk / Bus": emp_hv
}

def catat_kendaraan(jenis):
    if st.session_state.survey_start_time is None:
        st.session_state.survey_start_time = time.time()
    now_dt = datetime.now()
    st.session_state.counts[jenis] += 1
    st.session_state.history.append({
        "Waktu": now_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "Ruas Jalan": ruas_jalan if ruas_jalan else "-",
        "Arah": arah_arus,
        "Surveyor": surveyor if surveyor else "-",
        "Kendaraan": jenis,
        "EMP": emp_map[jenis]
    })

with col_btn1:
    if st.button("🏍️ +1 SEPEDA MOTOR (MC)", use_container_width=True, type="primary"):
        catat_kendaraan("Sepeda Motor")
with col_btn2:
    if st.button("🚗 +1 MOBIL / LV", use_container_width=True, type="primary"):
        catat_kendaraan("Mobil Pribadi")
with col_btn3:
    if st.button("🚛 +1 TRUK / BUS (HV)", use_container_width=True, type="primary"):
        catat_kendaraan("Truk / Bus")

st.markdown("### 2. Ringkasan Volume & Derajat Kejenuhan Real-Time")

motor_cnt = st.session_state.counts["Sepeda Motor"]
mobil_cnt = st.session_state.counts["Mobil Pribadi"]
truk_cnt = st.session_state.counts["Truk / Bus"]
total_cnt = motor_cnt + mobil_cnt + truk_cnt
total_smp = (motor_cnt * emp_mc) + (mobil_cnt * emp_lv) + (truk_cnt * emp_hv)

# Hitung arus ekuivalen per jam (Q dalam smp/jam)
if durasi_survei_menit is not None:
    basis_menit = durasi_survei_menit
else:
    basis_menit = float(st.session_state.interval_minutes)

q_smp_per_jam = total_smp * (60.0 / basis_menit) if basis_menit > 0 else 0.0
ds_value = (q_smp_per_jam / kapasitas_c) if kapasitas_c > 0 else 0.0

if ds_value < 0.75:
    ds_class = "ds-aman"
    ds_status = "Arus Stabil / Lancar (DS < 0.75)"
elif ds_value <= 0.85:
    ds_class = "ds-waspada"
    ds_status = "Mendekati Kapasitas (0.75 – 0.85)"
else:
    ds_class = "ds-jenuh"
    ds_status = "Padat / Jenuh (DS > 0.85)"

def persen(val, tot):
    return f"{(val / tot * 100):.1f}%" if tot > 0 else "0.0%"

c1, c2, c3, c4, c5, c6 = st.columns(6)

with c1:
    st.markdown(f"""
    <div class="metric-card motor">
        <div class="metric-title">🏍️ Sepeda Motor</div>
        <div class="metric-value">{motor_cnt}</div>
        <div class="metric-sub">{persen(motor_cnt, total_cnt)} | {(motor_cnt * emp_mc):.2f} smp</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="metric-card mobil">
        <div class="metric-title">🚗 Mobil / LV</div>
        <div class="metric-value">{mobil_cnt}</div>
        <div class="metric-sub">{persen(mobil_cnt, total_cnt)} | {(mobil_cnt * emp_lv):.2f} smp</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="metric-card truk">
        <div class="metric-title">🚛 Truk / Bus</div>
        <div class="metric-value">{truk_cnt}</div>
        <div class="metric-sub">{persen(truk_cnt, total_cnt)} | {(truk_cnt * emp_hv):.2f} smp</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="metric-card total">
        <div class="metric-title">📊 Total Unit</div>
        <div class="metric-value">{total_cnt}</div>
        <div class="metric-sub">Kendaraan Tercatat</div>
    </div>
    """, unsafe_allow_html=True)

with c5:
    st.markdown(f"""
    <div class="metric-card smp">
        <div class="metric-title">🛣️ Arus (Q)</div>
        <div class="metric-value">{q_smp_per_jam:.0f}</div>
        <div class="metric-sub">smp/jam ({total_smp:.2f} smp/{basis_menit:.0f}m)</div>
    </div>
    """, unsafe_allow_html=True)

with c6:
    st.markdown(f"""
    <div class="metric-card {ds_class}">
        <div class="metric-title">📉 Derajat Kejenuhan</div>
        <div class="metric-value">{ds_value:.2f}</div>
        <div class="metric-sub">{ds_status}</div>
    </div>
    """, unsafe_allow_html=True)

# --- VISUALISASI GRAFIK, INTERVAL & TABEL ---
if st.session_state.history:
    st.markdown("### 3. Analisis, Interval & Log Data Survei")
    tab1, tab2, tab3 = st.tabs(["📊 Grafik Kategori", "📈 Fluktuasi Waktu", "⏱️ Tabel Riwayat & Ekspor CSV"])

    df = pd.DataFrame(st.session_state.history)
    df["dt"] = pd.to_datetime(df["Waktu"])

    with tab1:
        chart_df = pd.DataFrame({
            "Kategori": ["Sepeda Motor (MC)", "Mobil / LV", "Truk / Bus (HV)"],
            "Jumlah (Kendaraan)": [motor_cnt, mobil_cnt, truk_cnt],
            "Setara (SMP)": [motor_cnt * emp_mc, mobil_cnt * emp_lv, truk_cnt * emp_hv]
        }).set_index("Kategori")
        st.bar_chart(chart_df, height=320)

    with tab2:
        freq_str = f"{st.session_state.interval_minutes}min"
        df_interval = df.set_index("dt").groupby([pd.Grouper(freq=freq_str), "Kendaraan"]).size().unstack(fill_value=0)
        st.caption(f"Rekapitulasi jumlah kendaraan per interval **{st.session_state.interval_minutes} menit** berdasarkan waktu pencatatan.")
        st.line_chart(df_interval, height=300)
        st.dataframe(df_interval, use_container_width=True)

    with tab3:
        df_tampil = df.drop(columns=["dt"])
        st.dataframe(df_tampil.iloc[::-1], use_container_width=True, height=260)

        csv = df_tampil.to_csv(index=False).encode('utf-8')
        nama_file = f"survei_{ruas_jalan.replace(' ', '_').lower()}.csv" if ruas_jalan else "hasil_survei_lalin.csv"
        st.download_button(
            label="📥 Download Hasil Survei (.CSV)",
            data=csv,
            file_name=nama_file,
            mime="text/csv",
            use_container_width=True
        )
else:
    st.info("👆 Klik salah satu tombol kendaraan di atas untuk mulai merekam data lalu lintas dan melihat grafik analisis.")
