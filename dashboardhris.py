import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import warnings
import itertools
import io
import textwrap
import pytz
from datetime import date, datetime, time, timedelta

# --- 1. CONFIG & STYLE ---
warnings.filterwarnings('ignore')
st.set_page_config(page_title="HRIS Dashboard", layout="wide", page_icon="🏢")

st.markdown("""
<style>
    /* Font Import */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');

    /* Global Settings */
    .stApp { 
        background-color: #f8fafc; 
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Card Design */
    div[data-testid="metric-container"] {
        background: #ffffff;
        padding: 24px;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        border-color: #3b82f6;
    }
    
    /* Headers */
    h1, h2, h3 { color: #0f172a; font-weight: 700; letter-spacing: -0.5px; }
    p, label { color: #64748b; }
    
    /* Custom Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; padding-bottom: 10px; }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        white-space: pre-wrap;
        background-color: #ffffff;
        border-radius: 8px;
        color: #64748b;
        font-weight: 600;
        border: 1px solid #e2e8f0;
        padding: 0 24px;
        transition: all 0.2s ease;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2563eb !important;
        color: white !important;
        border-color: #2563eb !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
    }
    
    /* DataFrame */
    .stDataFrame { border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# --- 2. DATA CONFIGURATION ---
libur_nasional = {
    # 2025
    date(2025, 1, 1): "Tahun Baru Masehi", date(2025, 1, 27): "Isra Mikraj",
    date(2025, 1, 28): "Cuti Imlek", date(2025, 1, 29): "Imlek",
    date(2025, 3, 29): "Nyepi", date(2025, 3, 31): "Idul Fitri",
    date(2025, 4, 1): "Idul Fitri", date(2025, 4, 2): "Cuti Lebaran",
    date(2025, 4, 3): "Cuti Lebaran", date(2025, 4, 4): "Cuti Lebaran",
    date(2025, 4, 18): "Jumat Agung", date(2025, 4, 20): "Paskah",
    date(2025, 5, 1): "Hari Buruh", date(2025, 5, 12): "Waisak",
    date(2025, 5, 29): "Kenaikan Isa Almasih", date(2025, 6, 1): "Pancasila",
    date(2025, 6, 6): "Idul Adha", date(2025, 6, 27): "1 Muharram",
    date(2025, 8, 17): "Kemerdekaan RI", date(2025, 9, 5): "Maulid Nabi",
    date(2025, 12, 25): "Natal", date(2025, 12, 26): "Cuti Natal",
    # 2026
    date(2026, 1, 1): "Tahun Baru Masehi", date(2026, 1, 16): "Isra Mikraj",
    date(2026, 2, 17): "Tahun Baru Imlek", date(2026, 3, 19): "Hari Suci Nyepi",
    date(2026, 3, 21): "Idul Fitri", date(2026, 3, 22): "Idul Fitri",
    date(2026, 4, 3): "Jumat Agung", date(2026, 4, 5): "Paskah",
    date(2026, 5, 1): "Hari Buruh", date(2026, 5, 14): "Kenaikan Yesus Kristus",
    date(2026, 5, 27): "Idul Adha", date(2026, 5, 31): "Hari Raya Waisak",
    date(2026, 6, 1): "Hari Lahir Pancasila", date(2026, 6, 16): "Tahun Baru Islam",
    date(2026, 8, 17): "Kemerdekaan RI", date(2026, 8, 25): "Maulid Nabi",
    date(2026, 12, 25): "Hari Raya Natal"
}

kantor_list = [
    "SCIENTIA", "GADING SERPONG", "CURUG SANGERENG", "KELAPA DUA", 
    "PAGEDANGAN", "MEDANG", "BINONG", "CISAUK", "LEGOK", "BSD", "SERPONG",
    "PT ITOKO SANNIN ABADI", "GLOBAL KONSULTAN", "PT. PRATAMA SOLUTION", "REGUS", 
    "PT. PARAMADAKSA TEKNOLOGI NUSANTARA", "AIMAN - ANUGERAH INOVASI MANUNGGAL", 
    "PT GANITRI NITSAYA HARITA", "PT VALUTAC INOVASI KREASI",
    "PRIME GLOBAL (KAP KANEL & REKAN)", "SANJAYA SOLUSINDO (PT SANJAYA SOLUSI DIGITAL INDONESIA)",
    "PT. SARAHMA GLOBAL INFORMATIKA", "TRIPROCKETS TRAVEL INDONESIA", "THE MAP CONSULTANT",
    "KESSLER EXECUTIVE SEARCH", "APP INTERNATIONAL INDONESIA", "PT WIAGA INTECH NUSANTARA",
    "PARAMADAKSA TEKNOLOGI NUSANTARA NEXSOFT",  
    "Astra Biz Center", "Ararasa BSD", "Branchsto Equestrian Park", "Cluster Aether Greenwich Park", 
    "Cluster Albera Foresta", "Cluster Alesha Vanya Park", "Cluster Alevia Foresta", "Cluster Allevare Foresta", 
    "Cluster Amarine The Mozia", "Cluster Amata The Mozia", "Cluster Amor Foresta", "Cluster Amozze The Mozia", 
    "Cluster Anarta Vanya Park", "Cluster Anila Vanya Park", "Cluster Aria Foresta", "Cluster Asatti Vanya Park",
    "Cluster Assana Vanya Park", "Cluster Aure The Mozia", "Cluster Avezza The Mozia", "Cluster Azura Vanya Park", 
    "Cluster Caelus Greenwich Park", "Cluster Fiore Foresta", "Cluster Foglio Foresta", "Cluster Fresco Foresta", 
    "Cluster Giardina Foresta", "Cluster Hylands Greenwich Park", "Cluster Illustria The Eminent", "Cluster Imajihaus Greenwich Park", 
    "Cluster Impresahaus Tabebuya", "Cluster Ingenia The Eminent", "Cluster Inspirahaus Tabebuya", "Cluster Invensihaus Tabebuya", 
    "Cluster Kanade The Zora", "Cluster Kazumi The Zora", "Cluster Keia The Zora", "Cluster Kimora The Zora", "Cluster Kiyomi The Zora", 
    "Cluster Luxmore Greenwich Park", "Cluster Mayfield Greenwich Park", "Cluster Naturale Foresta", "Cluster Piazza The Mozia", "Cluster Precia The Eminent", 
    "Cluster Prestigia The Eminent", "Cluster Prive Foresta", "Cluster Sheffield Greenwich Park", "Cluster Studento Foresta", "Cluster Ultimo Foresta", 
    "Cluster Vivacia The Eminent", "Cluster Whelford Greenwich Park", "Cluster Whitsand Greenwich Park", "Cluster Zena The Mozia", "Eastvara Mall", 
    "Foresta Business Loft", "Hotel Santika Premiere ICE BSD", "ICE BSD", "ICE Business Park", "IPEKA BSD", "Jakarta Nanyang School", "Mekia Park", 
    "Mercure Tangerang BSD City", "Northpoint Business Park", "Pasar Modern Intermoda BSD", "Prasetiya Mulya University", "QBig BSD City", "Regentown", 
    "Sapphire Sky Hotel", "Sinarmas World Academy", "Stasiun Cisauk", "Terminal Intermoda BSD", "Unilever Indonesia Head Office", "Vanya Park Lake", 
    "Virginia Arcade", "West Village Business Park", "Wisma BCA Foresta", "Vanya Park", "Metropark"
]

# --- 3. HELPER FUNCTIONS ---
if 'language' not in st.session_state:
    st.session_state['language'] = 'Bahasa Indonesia'

def tr(indo, eng):
    """Helper to switch text based on language"""
    return indo if st.session_state['language'] == 'Bahasa Indonesia' else eng

def format_date_custom(dt_obj):
    """Format date manually to ensure Indonesia names if selected"""
    if st.session_state['language'] == 'Bahasa Indonesia':
        days = {0: 'Senin', 1: 'Selasa', 2: 'Rabu', 3: 'Kamis', 4: 'Jumat', 5: 'Sabtu', 6: 'Minggu'}
        months = {
            1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April', 5: 'Mei', 6: 'Juni',
            7: 'Juli', 8: 'Agustus', 9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
        }
        return f"{days[dt_obj.weekday()]}, {dt_obj.day} {months[dt_obj.month]} {dt_obj.year}"
    else:
        return dt_obj.strftime('%A, %d %B %Y')

@st.cache_data
def load_data_smart(file):
    try:
        # Detect Header Row Smartly
        try:
            df_scan = pd.read_excel(file, header=None, nrows=10)
        except Exception:
            file.seek(0)
            df_scan = pd.read_csv(file, header=None, nrows=10, encoding='utf-8', sep=None, engine='python')
    
        header_idx = 0
        found = False
        for i, row in df_scan.iterrows():
            txt = " ".join(row.astype(str).str.upper().tolist())
            if "NAMA" in txt and ("MASUK" in txt or "ABSEN" in txt):
                header_idx = i
                found = True
                break
            
        file.seek(0)
        if not found: 
            header_idx = 0
        
        try:
            df = pd.read_excel(file, header=header_idx)
        except Exception:
            file.seek(0)
            df = pd.read_csv(file, header=header_idx, encoding='utf-8', sep=None, engine='python')
        return df
    except Exception:
        return None

def make_synced_input(label, key_prefix, default_val=80):
    """Creates a slider and number input that stay in sync"""
    key_val = f"{key_prefix}_val"
    if key_val not in st.session_state: 
        st.session_state[key_val] = default_val
    
    def update_sl(): 
        st.session_state[key_val] = st.session_state[f"{key_prefix}_slider"]
    
    def update_nm(): 
        st.session_state[key_val] = st.session_state[f"{key_prefix}_number"]

    st.markdown(f"<div style='margin-bottom:5px; font-weight:600; font-size:14px; color:#475569'>{label}</div>", unsafe_allow_html=True)
    c1, c2 = st.columns([3, 1])
    with c1: 
        st.slider("S", 0, 100, st.session_state[key_val], key=f"{key_prefix}_slider", on_change=update_sl, label_visibility="collapsed")
    with c2: 
        st.number_input("N", 0, 100, st.session_state[key_val], key=f"{key_prefix}_number", on_change=update_nm, label_visibility="collapsed")
    return st.session_state[key_val]

# --- 4. HEADER SECTION ---
c1, c2 = st.columns([3, 1])
with c1:
    st.title("🏢 HRIS Dashboard")
    st.markdown(f"<p style='font-size: 16px; margin-top: -10px; color: #64748b;'>{tr('Sistem Analisis SDM & Manajemen Performa', 'Enterprise People Analytics & Performance Management System')}</p>", unsafe_allow_html=True)

with c2:
    try:
        tz_jkt = pytz.timezone('Asia/Jakarta')
        now_jkt = datetime.now(tz_jkt)
    except:
        now_jkt = datetime.now() # Fallback if timezone fails
    
    st.markdown(f"""
    <div style="text-align: right; padding: 12px; background: white; border-radius: 12px; border: 1px solid #e2e8f0;">
        <span style="font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">{tr('Tanggal', 'Date')}</span><br>
        <span style="font-size: 16px; font-weight: 700; color: #0f172a;">{format_date_custom(now_jkt)}</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# --- 5. SIDEBAR & PROCESSING ---
with st.sidebar:
    st.markdown(f"### 🌐 Language / Bahasa")
    lang_opt = st.radio("Pilih Bahasa", ["Bahasa Indonesia", "English"], label_visibility="collapsed")
    
    if st.session_state['language'] != lang_opt:
        st.session_state['language'] = lang_opt
        st.rerun()

    st.markdown("---")
    
    st.subheader(tr("⚙️ Aturan Bisnis", "⚙️ Business Rules"))
    target_jam = st.number_input(tr("Standar Jam Kerja", "Standard Daily Hours"), value=8.5, step=0.5)
    jam_masuk_kantor = st.time_input(tr("Batas Keterlambatan", "Late Threshold Time"), value=time(9, 0))
    st.markdown("---")

    st.header(tr("📂 Import Data", "📂 Data Import"))
    uploaded_files = st.file_uploader(tr("Upload File Absensi", "Upload Attendance Files"), type=["xlsx", "csv"], accept_multiple_files=True)
    st.caption(tr("Mendukung format .xlsx dan .csv", "Supports .xlsx and .csv formats"))
    
    if st.button(tr("🧹 Reset Data", "🧹 Reset Data")):
        st.cache_data.clear()
        if 'df_full' in st.session_state: del st.session_state['df_full']
        st.rerun()
    st.markdown("---")

if uploaded_files:
    all_dfs = []
    for file in uploaded_files:
        try:
            df_temp = load_data_smart(file)
            if df_temp is not None:
                df_temp.columns = [str(c).strip() for c in df_temp.columns]
                all_dfs.append(df_temp)
        except Exception as e:
            st.error(f"Error reading file {file.name}: {e}")

    if all_dfs:
        df_raw = pd.concat(all_dfs, ignore_index=True)
        df_raw.columns = [str(c).strip() for c in df_raw.columns]
        cols = df_raw.columns.tolist()

        st.sidebar.subheader(tr("🛠️ Pemetaan Kolom", "🛠️ Column Mapping"))
        def find(k): 
            for i,c in enumerate(cols): 
                if any(x in c.upper() for x in k): return i
            return 0

        c_nama = st.sidebar.selectbox(tr("Nama Karyawan", "Employee Name"), cols, index=find(['NAMA','NAME']))
        c_masuk = st.sidebar.selectbox(tr("Jam Masuk", "Check In Time"), cols, index=find(['MASUK','IN']))
        c_keluar = st.sidebar.selectbox(tr("Jam Keluar", "Check Out Time"), cols, index=find(['KELUAR','OUT']))
        c_lokasi = st.sidebar.selectbox(tr("Lokasi", "Location"), cols, index=find(['LOKASI','LOC']))
        c_catatan = st.sidebar.selectbox(tr("Catatan", "Notes"), cols, index=find(['CATATAN','KET']))

        st.sidebar.markdown("---")
        
        if st.sidebar.button(tr("🚀 Analisa Data", "🚀 Analyze Data"), type="primary", use_container_width=True):
            with st.spinner(tr("🔄 Memproses Data...", "🔄 Crunching Data & Generating Insights...")):
                # --- PROCESSING PIPELINE ---
                try:
                    df_act = df_raw[[c_nama, c_masuk, c_keluar, c_lokasi, c_catatan]].copy()
                    df_act.columns = ['Nama', 'Masuk_Raw', 'Keluar_Raw', 'Lokasi', 'Catatan']
                    
                    # Fix: Add dayfirst=True for Indonesia Date Format stability
                    df_act['Masuk_Obj'] = pd.to_datetime(df_act['Masuk_Raw'], errors='coerce', dayfirst=True)
                    df_act['Keluar_Obj'] = pd.to_datetime(df_act['Keluar_Raw'], errors='coerce', dayfirst=True)
                    
                    df_act = df_act.dropna(subset=['Masuk_Obj']) 
                    
                    if df_act.empty: 
                        st.error(tr("Data valid tidak ditemukan atau format tanggal salah.", "No valid data found or date format incorrect."))
                        st.stop()

                    df_act['Tanggal'] = df_act['Masuk_Obj'].dt.date

                    # Grouping
                    df_act_grouped = df_act.groupby(['Nama', 'Tanggal']).agg({
                        'Masuk_Obj': 'min', 'Keluar_Obj': 'max',
                        'Lokasi': 'first', 'Catatan': 'first'      
                    }).reset_index()

                    df_act_grouped.rename(columns={'Masuk_Obj': 'Absen Masuk', 'Keluar_Obj': 'Absen Keluar'}, inplace=True)
                    df_act_grouped['Jam_Masuk'] = df_act_grouped['Absen Masuk'].dt.time
                    
                    df_act_grouped['Lokasi'] = df_act_grouped['Lokasi'].fillna("Unknown").astype(str).str.upper()
                    df_act_grouped['Catatan'] = df_act_grouped['Catatan'].fillna("-").astype(str).str.upper()

                    # === AUTO CHECKOUT ===
                    def apply_checkout_rules(row):
                        limit_time = datetime.combine(row['Tanggal'], time(20, 0))
                        current_out = row['Absen Keluar']
                        current_note = row['Catatan']

                        if pd.isnull(row['Absen Masuk']): return current_out, current_note

                        if pd.isnull(current_out):
                            return limit_time, current_note + " (SYSTEM: AUTO-OUT 20:00)"
                        elif current_out > limit_time:
                            return limit_time, current_note + " (CAPPED: MAX 20:00)"
                        else:
                            return current_out, current_note

                    res_rules = df_act_grouped.apply(apply_checkout_rules, axis=1, result_type='expand')
                    df_act_grouped['Absen Keluar'] = res_rules[0]
                    df_act_grouped['Catatan'] = res_rules[1]

                    df_act_grouped['Durasi'] = (df_act_grouped['Absen Keluar'] - df_act_grouped['Absen Masuk']).dt.total_seconds() / 3600
                    df_act_grouped['Durasi'] = df_act_grouped['Durasi'].fillna(0).round(2)

                    # Late Logic (Store both versions)
                    def cek_keterlambatan(row, lang):
                        if lang == 'ID':
                            txt_ontime, txt_mild = "Tepat Waktu", "Terlambat Ringan (<15m)"
                            txt_mod, txt_sev = "Terlambat Sedang (15-60m)", "Terlambat Berat (>60m)"
                        else:
                            txt_ontime, txt_mild = "On Time", "Mild Late (<15m)"
                            txt_mod, txt_sev = "Moderate Late (15-60m)", "Severe Late (>60m)"

                        if pd.isnull(row['Jam_Masuk']): return txt_ontime
                        if row['Jam_Masuk'] > jam_masuk_kantor:
                            dt_masuk = datetime.combine(date.min, row['Jam_Masuk'])
                            dt_target = datetime.combine(date.min, jam_masuk_kantor)
                            diff_min = (dt_masuk - dt_target).total_seconds() / 60
                            if diff_min <= 15: return txt_mild
                            elif diff_min <= 60: return txt_mod
                            else: return txt_sev
                        return txt_ontime
                    
                    # Logic for Is_Late Flag (Numerical)
                    def cek_is_late(row):
                        if pd.isnull(row['Jam_Masuk']): return 0
                        if row['Jam_Masuk'] > jam_masuk_kantor:
                            dt_masuk = datetime.combine(date.min, row['Jam_Masuk'])
                            dt_target = datetime.combine(date.min, jam_masuk_kantor)
                            if (dt_masuk - dt_target).total_seconds() / 60 > 0: return 1
                        return 0

                    df_act_grouped['Late_ID'] = df_act_grouped.apply(lambda r: cek_keterlambatan(r, 'ID'), axis=1)
                    df_act_grouped['Late_EN'] = df_act_grouped.apply(lambda r: cek_keterlambatan(r, 'EN'), axis=1)
                    df_act_grouped['Is_Late'] = df_act_grouped.apply(cek_is_late, axis=1)

                    unique_names = df_act_grouped['Nama'].unique()
                    min_date = df_act_grouped['Tanggal'].min()
                    max_date = df_act_grouped['Tanggal'].max()
                    grid = list(itertools.product(unique_names, pd.date_range(min_date, max_date).date))
                    df_master = pd.DataFrame(grid, columns=['Nama', 'Tanggal'])
                    
                    df_final = pd.merge(df_master, df_act_grouped, on=['Nama', 'Tanggal'], how='left')

                    # Status Logic (Store both versions)
                    def get_status(row, lang):
                        tgl = row['Tanggal']
                        cat = str(row['Catatan']).strip().upper() if pd.notnull(row['Catatan']) else ""
                        lok = str(row['Lokasi']).strip().upper() if pd.notnull(row['Lokasi']) else ""
                        ada_absen = pd.notnull(row['Absen Masuk'])
                        is_weekend = tgl.weekday() >= 5 
                        
                        # Language Dicts
                        if lang == 'ID':
                            l_cuti, l_libur, l_lembur_l, l_weekend, l_lembur_w = "Cuti", "Libur Nasional", "Libur Nasional", "Libur Akhir Pekan", "Weekend"
                            l_alpha = "Alpha"
                        else:
                            l_cuti, l_libur, l_lembur_l, l_weekend, l_lembur_w = "Leave", "National Holiday", "National Holiday", "Weekend", "Weekend"
                            l_alpha = "Absent"

                        # Keywords check
                        if any(x in cat for x in ["CUTI", "IZIN", "SAKIT", "LEAVE", "SICK"]): return l_cuti

                        if tgl in libur_nasional:
                            if ada_absen: 
                                suffix = "(WFO)" if any(k in lok for k in kantor_list) else "(WFH)"
                                return f"{l_lembur_l} {suffix}"
                            return l_libur
                        
                        if is_weekend:
                            if ada_absen: 
                                suffix = "(WFO)" if any(k in lok for k in kantor_list) else "(WFH)"
                                return f"{l_lembur_w} {suffix}"
                            return l_weekend
                        
                        if cat != "" and not any(k in cat for k in ['WFH', 'WFO', 'MASUK', 'WORK', '-', 'NAN', 'HADIR', '', 'SYSTEM', 'CAPPED']): return l_cuti
                        
                        if ada_absen: 
                            return "WFO" if any(k in lok for k in kantor_list) else "WFH"
                        return l_alpha

                    df_final['Status_ID'] = df_final.apply(lambda r: get_status(r, 'ID'), axis=1)
                    df_final['Status_EN'] = df_final.apply(lambda r: get_status(r, 'EN'), axis=1)
                    
                    # Zero out duration (check ID status for logic)
                    non_working_id = ["Cuti", "Alpha", "Libur Nasional", "Libur Akhir Pekan"]
                    df_final.loc[df_final['Status_ID'].isin(non_working_id), 'Durasi'] = 0
                    
                    df_final['Tanggal_DT'] = pd.to_datetime(df_final['Tanggal'])
                    df_final['Tahun'] = df_final['Tanggal_DT'].dt.year
                    
                    # --- DUAL VERSION for Month and Day ---
                    # 1. Version Indonesia
                    month_map_id = {1:'Januari', 2:'Februari', 3:'Maret', 4:'April', 5:'Mei', 6:'Juni', 7:'Juli', 8:'Agustus', 9:'September', 10:'Oktober', 11:'November', 12:'Desember'}
                    day_map_id = {0:'Senin', 1:'Selasa', 2:'Rabu', 3:'Kamis', 4:'Jumat', 5:'Sabtu', 6:'Minggu'}
                    
                    df_final['Bulan_ID'] = df_final['Tanggal_DT'].dt.month.map(month_map_id)
                    df_final['Hari_ID'] = df_final['Tanggal_DT'].dt.dayofweek.map(day_map_id)
                    
                    # 2. Version English
                    df_final['Bulan_EN'] = df_final['Tanggal_DT'].dt.month_name()
                    df_final['Hari_EN'] = df_final['Tanggal_DT'].dt.day_name()
                    
                    df_final['Bulan_Angka'] = df_final['Tanggal_DT'].dt.month
                    df_final['Minggu_Ke'] = df_final['Tanggal_DT'].dt.isocalendar().week
                    
                    df_final['Is_Late'] = df_final['Is_Late'].fillna(0)
                    df_final['Late_ID'] = df_final['Late_ID'].fillna("-")
                    df_final['Late_EN'] = df_final['Late_EN'].fillna("-")

                    st.session_state['df_full'] = df_final
                    st.success(tr("✅ Analisa Selesai!", "✅ Analytics Completed!"))
                except Exception as e:
                    st.error(f"Error during processing: {e}")
    else:
        st.sidebar.info(tr("👋 Silakan upload file absensi.", "👋 Welcome! Please upload attendance file to start."))

# --- 6. VISUALIZATION ENGINE ---
if 'df_full' in st.session_state:
    df = st.session_state['df_full'].copy()
    
    # --- DYNAMIC LANGUAGE SWITCHING FOR DATA CONTENT ---
    if st.session_state['language'] == 'Bahasa Indonesia':
        df['Bulan'] = df['Bulan_ID']
        df['Hari'] = df['Hari_ID']
        df['Status'] = df['Status_ID']
        df['Late_Category'] = df['Late_ID']
    else:
        df['Bulan'] = df['Bulan_EN']
        df['Hari'] = df['Hari_EN']
        df['Status'] = df['Status_EN']
        df['Late_Category'] = df['Late_EN']
    
    with st.sidebar.expander(tr("🌪️ Filter Data", "🌪️ Filter & Slice"), expanded=True):
        sel_tahun = st.multiselect(tr("Tahun", "Year"), sorted(df['Tahun'].unique()), default=sorted(df['Tahun'].unique()))
        
        # Sort using Bulan_Angka but display Bulan
        df_bln = df[['Bulan', 'Bulan_Angka']].drop_duplicates().sort_values('Bulan_Angka')
        sel_bulan = st.multiselect(tr("Bulan", "Month"), df_bln['Bulan'].tolist(), default=df_bln['Bulan'].tolist())
        
        if not df.empty:
            w_min, w_max = int(df['Minggu_Ke'].min()), int(df['Minggu_Ke'].max())
            if w_min < w_max:
                sel_minggu = st.slider(tr("Minggu", "Week"), w_min, w_max, (w_min, w_max))
            else:
                sel_minggu = (w_min, w_max)
        else: sel_minggu = (0,0)
            
        all_emp = sorted(df['Nama'].unique())
        is_select_all = st.checkbox(tr("Pilih Semua Karyawan", "Select All Employees"), value=True)
        if is_select_all:
            sel_karyawan = st.multiselect(tr("Karyawan", "Employees"), all_emp, default=all_emp)
        else:
            sel_karyawan = st.multiselect(tr("Karyawan", "Employees"), all_emp)

    if not sel_tahun: sel_tahun = df['Tahun'].unique()
    if not sel_bulan: sel_bulan = df['Bulan'].unique()
    if not sel_karyawan: sel_karyawan = df['Nama'].unique()
    
    mask = (df['Tahun'].isin(sel_tahun) & df['Bulan'].isin(sel_bulan) & 
            (df['Minggu_Ke'] >= sel_minggu[0]) & (df['Minggu_Ke'] <= sel_minggu[1]) & 
            df['Nama'].isin(sel_karyawan))
    df_f = df[mask].copy()
    
    st.sidebar.markdown("---")
    
    # Fix: Add error handling for Excel Export (Missing xlsxwriter/openpyxl)
    try:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_f.to_excel(writer, index=False, sheet_name='Report')
        st.sidebar.download_button(tr("📥 Download Data", "📥 Download Raw Data"), buffer.getvalue(), f"HR_Report_{date.today()}.xlsx", "application/vnd.ms-excel", use_container_width=True)
    except Exception as e:
        st.sidebar.warning(tr("⚠️ Install 'xlsxwriter' untuk fitur download.", "⚠️ Install 'xlsxwriter' for download feature."))

    tab1, tab2 = st.tabs([tr("📊 Dashboard Monitoring", "📊 Dashboard Monitoring"), tr("📝 Penilaian Kinerja", "📝 Performance Review")])
    
    # === TAB 1: EXECUTIVE DASHBOARD ===
    with tab1:
        if df_f.empty: st.warning(tr("Tidak ada data ditemukan untuk filter ini.", "No data found for the selected criteria."))
        else:
            try:
                top_emp = df_f.groupby('Nama')['Durasi'].sum().idxmax()
                most_late_day = df_f[df_f['Is_Late']==1]['Hari'].mode()[0] if df_f['Is_Late'].sum() > 0 else "None"
                avg_prod = df_f[df_f['Durasi']>0]['Durasi'].mean()
                
                t_insight = tr("Wawasan", "Insights")
                t_top = tr("Karyawan Terbaik", "Top Performer")
                t_late = tr("Hari Paling Sering Terlambat", "Most Late Day")
                t_prod = tr("Rata-rata Produktivitas", "Avg Productivity")
                
                st.info(f"💡 **{t_insight}:** {t_top}: **{top_emp}** | {t_late}: **{most_late_day}** | {t_prod}: **{avg_prod:.2f} {tr('jam/hari','hrs/day')}**")
            except:
                st.info(tr("💡 Wawasan: Data belum cukup.", "💡 Insights: Data not sufficient."))

            # KEY METRICS
            total_days_log = len(df_f)
            total_alpha = len(df_f[df_f['Status'].isin(['Alpha', 'Absent'])])
            total_cuti = len(df_f[df_f['Status'].isin(['Cuti', 'Leave'])])
            total_wfo = len(df_f[df_f['Status'].str.contains('WFO', na=False)])
            total_wfh = len(df_f[df_f['Status'].str.contains('WFH', na=False)])
            total_late_count = df_f['Is_Late'].sum()
            avg_hrs = df_f[df_f['Durasi']>0]['Durasi'].mean() if len(df_f[df_f['Durasi']>0]) > 0 else 0
            
            m1, m2, m3, m4, m5, m6, m7 = st.columns(7)
            m1.metric(tr("Total Karyawan", "Headcount"), df_f['Nama'].nunique())
            m2.metric(tr("Rata2 Jam", "Avg Hours"), f"{avg_hrs:.1f} H")
            m3.metric("WFO", total_wfo)
            m4.metric("WFH", total_wfh)
            m5.metric(tr("Cuti", "Leave"), total_cuti)
            m6.metric(tr("Alpha", "Absent"), total_alpha, delta_color="inverse")
            m7.metric(tr("Terlambat", "Late"), int(total_late_count), delta_color="inverse")

            st.markdown("---")

            c1, c2 = st.columns([1, 2])
            with c1:
                st.subheader(tr("Komposisi Kehadiran", "Attendance Composition"))
                df_pie = df_f['Status'].value_counts().reset_index()
                df_pie.columns = ['Status', 'Jumlah']
                fig_pie = px.pie(df_pie, values='Jumlah', names='Status', hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_pie.update_layout(margin=dict(t=0, b=0, l=0, r=0), showlegend=True, legend=dict(orientation="h", y=-0.1))
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with c2:
                st.subheader(tr("Tren Produktivitas Bulanan", "Monthly Productivity Trend"))
                df_monthly = df_f[df_f['Durasi']>0].groupby(['Bulan_Angka', 'Bulan'])['Durasi'].mean().reset_index().sort_values('Bulan_Angka')
                if not df_monthly.empty:
                    fig_trend = go.Figure()
                    fig_trend.add_trace(go.Scatter(x=df_monthly['Bulan'], y=df_monthly['Durasi'], mode='lines+markers', name=tr('Rata-rata Jam', 'Avg Hours'), line=dict(color='#3b82f6', width=3)))
                    fig_trend.add_trace(go.Scatter(x=df_monthly['Bulan'], y=[target_jam]*len(df_monthly), mode='lines', name='Target', line=dict(color='red', dash='dash')))
                    fig_trend.update_layout(xaxis_title=None, yaxis_title=tr("Jam", "Hours"), margin=dict(t=20, b=20, l=0, r=0), hovermode="x unified")
                    st.plotly_chart(fig_trend, use_container_width=True)

            c3, c4 = st.columns([2, 1])
            with c3:
                st.subheader(tr("Monitor Produktivitas Harian", "Daily Productivity Monitor"))
                df_daily = df_f[df_f['Durasi']>0].groupby('Tanggal')['Durasi'].mean().reset_index()
                fig_area = px.area(df_daily, x='Tanggal', y='Durasi', line_shape='spline')
                fig_area.add_hline(y=target_jam, line_dash="dash", line_color="red")
                fig_area.update_traces(line_color='#10b981', fillcolor='rgba(16, 185, 129, 0.1)')
                fig_area.update_layout(xaxis_title=None, yaxis_title=tr("Jam", "Hours"), margin=dict(t=0, b=0, l=0, r=0))
                st.plotly_chart(fig_area, use_container_width=True)
            
            with c4:
                st.subheader(tr("🚨 Analisa Keterlambatan", "🚨 Late Severity Breakdown"))
                df_late = df_f[df_f['Is_Late'] == 1]['Late_Category'].value_counts().reset_index()
                if not df_late.empty:
                    df_late.columns = ['Category', 'Count']
                    
                    color_map = {}
                    for cat in df_late['Category']:
                        if "Mild" in cat or "Ringan" in cat: color_map[cat] = "#fbbf24"
                        elif "Moderate" in cat or "Sedang" in cat: color_map[cat] = "#f97316"
                        else: color_map[cat] = "#ef4444"

                    fig_pie_late = px.pie(df_late, values='Count', names='Category', color='Category', 
                                          color_discrete_map=color_map, hole=0.6)
                    fig_pie_late.update_layout(showlegend=True, legend=dict(orientation="h", y=-0.2), 
                                              margin=dict(t=0, l=0, r=0, b=0))
                    st.plotly_chart(fig_pie_late, use_container_width=True)
                else:
                    st.success(tr("✅ Tidak ada keterlambatan!", "✅ Excellent! No late arrivals detected."))

            st.markdown(f"### 🏆 {tr('Papan Peringkat', 'Leaderboards')}")
            r1, r2, r3 = st.columns(3)
            
            with r1:
                st.markdown(f"**{tr('Kehadiran Tertinggi', 'Most Present')}**")
                df_pres = df_f[df_f['Status'].str.contains('WF|Lembur|Overtime', na=False)].groupby('Nama').size().reset_index(name='Days')
                df_top3_pres = df_pres.sort_values('Days', ascending=False).head(3)
                if not df_top3_pres.empty:
                    fig_r1 = px.bar(df_top3_pres, x='Days', y='Nama', orientation='h', text_auto=True, color_discrete_sequence=['#3b82f6'])
                    fig_r1.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(t=0, b=0, l=0, r=0), height=200)
                    st.plotly_chart(fig_r1, use_container_width=True)

            with r2:
                st.markdown(f"**{tr('Ketidakhadiran Tertinggi', 'Highest Absenteeism')}**")
                df_abs = df_f[df_f['Status'].isin(['Alpha', 'Absent'])].groupby('Nama').size().reset_index(name='Days')
                df_top3_abs = df_abs.sort_values('Days', ascending=False).head(3)
                if not df_top3_abs.empty:
                    fig_r2 = px.bar(df_top3_abs, x='Days', y='Nama', orientation='h', text_auto=True, color_discrete_sequence=['#ef4444'])
                    fig_r2.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(t=0, b=0, l=0, r=0), height=200)
                    st.plotly_chart(fig_r2, use_container_width=True)
                else:
                    st.success(tr("Absensi sempurna! Tidak ada Alpha.", "Perfect attendance! No Alpha."))

            with r3:
                st.markdown(f"**{tr('Jam Kerja Tertinggi', 'Highest Work Hours')}**")
                df_hrs = df_f.groupby('Nama')['Durasi'].sum().reset_index()
                df_top3_hrs = df_hrs.sort_values('Durasi', ascending=False).head(3)
                if not df_top3_hrs.empty:
                    fig_r3 = px.bar(df_top3_hrs, x='Durasi', y='Nama', orientation='h', text_auto='.0f', color_discrete_sequence=['#10b981'])
                    fig_r3.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(t=0, b=0, l=0, r=0), height=200)
                    st.plotly_chart(fig_r3, use_container_width=True)

            with st.expander(tr("📄 Detail Data Karyawan", "📄 Detailed Data Employee"), expanded=False):
                st.caption(tr("Keterangan Warna:", "Color Legend:"))
                st.markdown(f"""
                <div style="display: flex; gap: 15px; margin-bottom: 10px;">
                    <div style="display: flex; align-items: center;">
                        <span style="display: inline-block; width: 15px; height: 15px; background-color: #fca5a5; margin-right: 5px; border-radius: 3px;"></span>
                        <span style="font-size: 13px; color: #475569;"><b>{tr('Merah Pekat', 'Dark Red')}:</b> {tr('Alpha', 'Absent')}</span>
                    </div>
                    <div style="display: flex; align-items: center;">
                        <span style="display: inline-block; width: 15px; height: 15px; background-color: #fee2e2; margin-right: 5px; border-radius: 3px;"></span>
                        <span style="font-size: 13px; color: #475569;"><b>{tr('Merah Terang', 'Light Red')}:</b> {tr('Performa Rendah', 'Underperformance')} (< {target_jam}h)</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                df_display = df_f.copy()
                total_durasi = df_display['Durasi'].sum()
                
                total_row = {col: '' for col in df_display.columns}
                total_row['Nama'] = tr('TOTAL RINGKASAN', 'TOTAL SUMMARY')
                total_row['Durasi'] = total_durasi
                
                df_total = pd.DataFrame([total_row])
                df_final_table = pd.concat([df_display, df_total], ignore_index=True)
                
                def highlight_total(row):
                    if row['Nama'] == tr('TOTAL RINGKASAN', 'TOTAL SUMMARY'):
                        return ['background-color: #d1e7dd; font-weight: bold; color: #0f5132'] * len(row)
                    
                    try:
                        val_durasi = float(row['Durasi'])
                    except:
                        val_durasi = 0
                        
                    if val_durasi > 0 and val_durasi < target_jam:
                        return ['background-color: #fee2e2; color: #b91c1c'] * len(row) 
                    
                    if row['Status'] in ['Alpha', 'Absent']:
                          return ['background-color: #fca5a5; color: #7f1d1d'] * len(row)

                    return [''] * len(row)

                st.dataframe(
                    df_final_table.style.apply(highlight_total, axis=1).format({'Durasi': '{:.2f}'}),
                    use_container_width=True
                )

    # === TAB 2: PERFORMANCE REVIEW ===
    with tab2:
        st.write("")
        col_sel, col_dummy = st.columns([1, 2])
        with col_sel:
            target_emp = st.selectbox(tr("👤 Pilih Karyawan untuk Dinilai:", "👤 Select Employee for Review:"), sorted(df['Nama'].unique()))
        
        if target_emp:
            # === 1. DEFINE SCORING LOGIC & DISPLAY RULES ===
            with st.expander(tr("⚖️ Aturan & Breakdown Penilaian", "⚖️ Scoring Rules & Breakdown"), expanded=True):
                # RULE TEXT INDONESIAN
                rule_id = f"""
                **Sistem Penilaian KPI Otomatis**
                Penilaian dihitung berdasarkan data absensi harian dengan skema berikut:
                
                * **Hadir Tepat Waktu & Durasi Cukup:** :green[100 Poin]
                * **Hadir tapi Tidak Ada Log Jam (Manual):** :orange[70 Poin] (Nilai aman)
                * **Alpha (Tidak Hadir Tanpa Ket.):** :red[-50 Poin] (Penalti Fatal)
                
                **Pengurangan Poin (Penalti):**
                1.  **Terlambat Ringan (< 15 menit):** -5 Poin
                2.  **Terlambat Sedang (15 - 60 menit):** -15 Poin
                3.  **Terlambat Berat (> 60 menit):** -30 Poin
                4.  **Durasi Kerja Kurang (< {target_jam} Jam):** -20 Poin
                
                *Contoh: Datang terlambat 20 menit (-15) DAN pulang cepat/durasi kurang (-20) = Nilai Harian 65.*
                """
                
                # RULE TEXT ENGLISH
                rule_en = f"""
                **Automatic KPI Scoring System**
                Scores are calculated based on daily attendance data using the following scheme:
                
                * **Present On Time & Sufficient Duration:** :green[100 Points]
                * **Present but No Time Log (Manual):** :orange[70 Points] (Safe score)
                * **Absent (Alpha):** :red[-50 Points] (Fatal Penalty)
                
                **Point Deductions (Penalties):**
                1.  **Mild Late (< 15 mins):** -5 Points
                2.  **Moderate Late (15 - 60 mins):** -15 Points
                3.  **Severe Late (> 60 mins):** -30 Points
                4.  **Insufficient Work Duration (< {target_jam} Hours):** -20 Points
                
                *Example: Arrived 20 mins late (-15) AND left early/short duration (-20) = Daily Score 65.*
                """
                
                st.markdown(tr(rule_id, rule_en))

            df_emp = df_f[df_f['Nama'] == target_emp].copy()
            
            if not df_emp.empty:
                # Constants for Logic
                SCORE_BASE = 100
                SCORE_MANUAL = 70
                PENALTY_ALPHA = -50
                PENALTY_LATE_MILD = -5     # < 15 mins
                PENALTY_LATE_MOD = -15     # 15 - 60 mins
                PENALTY_LATE_SEV = -30     # > 60 mins
                PENALTY_SHORT_DUR = -20    # Duration < Target
                PENALTY_WEEKLY_WFH = -10
                PENALTY_DOMINANT_WFH = -30
                
                LIMIT_DURASI = target_jam
                
                kpi_log = [] 
                total_kpi_score = 0
                count_wfo = 0
                count_wfh = 0
                
                # Iterate rows
                for idx, row in df_emp.iterrows():
                    status = row['Status']
                    jam_masuk = row['Jam_Masuk']
                    durasi = row['Durasi']
                    tanggal = row['Tanggal']
                    
                    daily_points = 0
                    note = ""
                    
                    # 1. Check Alpha
                    if status in ['Alpha', 'Absent']:
                        total_kpi_score += PENALTY_ALPHA
                        kpi_log.append(f"{tanggal}: {tr('ALPHA', 'ABSENT')} (Fatal Penalty {PENALTY_ALPHA})")
                        continue
                    
                    # 2. Check Exclusions (Cuti, Libur, etc)
                    ignore_status = [
                        tr("Cuti", "Leave"), 
                        tr("Libur Nasional", "National Holiday"), 
                        tr("Libur Akhir Pekan", "Weekend")
                    ]
                    if status in ignore_status or "Lembur" in status or "Overtime" in status:
                        continue
                        
                    # 3. Process Presence
                    loc_code = "WFO" if "WFO" in status else ("WFH" if "WFH" in status else "LOC")
                    if "WFO" in status: count_wfo += 1
                    elif "WFH" in status: count_wfh += 1
                        
                    # 4. Scoring Logic
                    if pd.notnull(jam_masuk):
                        current_day_score = SCORE_BASE
                        deductions = []
                        
                        # A. Check Lateness (Using jam_masuk_kantor from sidebar)
                        if jam_masuk > jam_masuk_kantor:
                            dt_masuk = datetime.combine(date.min, jam_masuk)
                            dt_target = datetime.combine(date.min, jam_masuk_kantor)
                            diff_minutes = (dt_masuk - dt_target).total_seconds() / 60
                            
                            if diff_minutes <= 15:
                                current_day_score += PENALTY_LATE_MILD
                                deductions.append(f"Late <15m ({PENALTY_LATE_MILD})")
                            elif diff_minutes <= 60:
                                current_day_score += PENALTY_LATE_MOD
                                deductions.append(f"Late 15-60m ({PENALTY_LATE_MOD})")
                            else:
                                current_day_score += PENALTY_LATE_SEV
                                deductions.append(f"Late >60m ({PENALTY_LATE_SEV})")
                        
                        # B. Check Duration
                        if durasi < LIMIT_DURASI:
                            current_day_score += PENALTY_SHORT_DUR
                            deductions.append(f"Short Dur <{LIMIT_DURASI}h ({PENALTY_SHORT_DUR})")
                        
                        total_kpi_score += current_day_score
                        
                        if current_day_score == 100:
                            note = f"Perfect (+{current_day_score})"
                        else:
                            note = f"Score {current_day_score} [{', '.join(deductions)}]"
                            
                    else:
                        # Manual / No time log but present
                        total_kpi_score += SCORE_MANUAL
                        note = f"Manual Entry/No Log ({SCORE_MANUAL})"
                    
                    kpi_log.append(f"{tanggal} [{loc_code}]: {note}")

                # Weekly Penalties
                weekly_wfh = df_emp[df_emp['Status'].str.contains('WFH', na=False)].groupby('Minggu_Ke').size()
                for week_num, count in weekly_wfh.items():
                    if count > 1:
                        total_kpi_score += PENALTY_WEEKLY_WFH
                        kpi_log.append(f"{tr('Minggu', 'Week')} {week_num}: {tr('Penalti WFH > 1x', 'WFH Penalty > 1x')} ({PENALTY_WEEKLY_WFH})")

                if count_wfh > count_wfo:
                    total_kpi_score += PENALTY_DOMINANT_WFH
                    kpi_log.append(f"{tr('Penalti Bulanan: Total WFH > WFO', 'Monthly Penalty: Total WFH > WFO')} ({PENALTY_DOMINANT_WFH})")
                
                # Final Calculation
                total_hari_kerja_periode = len(df_emp[~df_emp['Status'].isin(ignore_status)])
                max_possible_score = total_hari_kerja_periode * 100
                
                # Safe division
                kpi_percentage = max(0, (total_kpi_score / max_possible_score) * 100) if max_possible_score > 0 else 0
                score_kpi_final = min(100, kpi_percentage)

                score_att = max(0, ((total_hari_kerja_periode - len(df_emp[df_emp['Status'].isin(['Alpha', 'Absent'])])) / max(1, total_hari_kerja_periode))*100)
                
                start_date = df_emp['Tanggal'].min()
                end_date = df_emp['Tanggal'].max()
                
                # Generate business days
                all_dates = pd.date_range(start_date, end_date, freq='B').date
                ideal_working_days = [d for d in all_dates if d not in libur_nasional]
                count_ideal_days = len(ideal_working_days)
                target_total_hours = count_ideal_days * target_jam
                actual_total_hours = df_emp['Durasi'].sum()
                
                if target_total_hours > 0:
                    score_project = (actual_total_hours / target_total_hours) * 100
                else:
                    score_project = 0
                score_project = min(100, score_project)

                c_left, c_right = st.columns([1, 1], gap="large")
                
                with c_left:
                    st.markdown(f"#### 📝 {tr('Input Penilaian Aktivitas', 'Input Activity Assessment')}")
                    
                    lbl_kom = tr("Komunikasi (10%)", "Communication (10%)")
                    lbl_prob = tr("Pemecahan Masalah (10%)", "Problem Solving (10%)")
                    lbl_wfo = tr("Kepatuhan WFO (20%)", "WFO Compliance (20%)")
                    lbl_qual = tr("Kualitas Kerja (15%)", "Work Quality (15%)")

                    v_kom = make_synced_input(lbl_kom, "v_kom", 80)
                    v_prob = make_synced_input(lbl_prob, "v_prob", 75)
                    v_wfo = make_synced_input(lbl_wfo, "v_wfo", 80)
                    v_qual = make_synced_input(lbl_qual, "v_qual", 80)
                    
                    st.divider()
                    st.markdown(f"#### {tr('Rincian KPI System', 'System KPI Details')}")
                    st.caption(tr("Poin ini dihitung otomatis oleh sistem berdasarkan absensi.", "Calculated automatically by the system."))
                    
                    kpi_data = {
                        tr("Metrik", "Metric"): [tr("Pencapaian KPI (20%)", "KPI Achievement (20%)"), 
                                                 tr("Kelengkapan Absensi (10%)", "Attendance Completeness (10%)"), 
                                                 tr("Proyek (15%)", "Project (15%)")],
                        tr("Skor", "Score"): [f"{score_kpi_final:.1f}", f"{score_att:.1f}", f"{score_project:.1f}"]
                    }
                    st.table(pd.DataFrame(kpi_data))
                    
                    with st.expander(tr("📜 Log Detail Pencapaian KPI", "📜 KPI Achievement Detail Log")):
                        st.write(f"{tr('Total Poin Akumulasi', 'Total Accumulated Points')}: {total_kpi_score} / {max_possible_score}")
                        for log in kpi_log:
                            if "Penalty" in log or "Alpha" in log or "Late" in log or "Short" in log: st.markdown(f":red[{log}]")
                            elif "Perfect" in log or "Sempurna" in log: st.markdown(f":green[{log}]")
                            else: st.text(log)

                with c_right:
                    final_score = (
                        (v_kom * 0.10) +             
                        (score_kpi_final * 0.20) +   
                        (score_att * 0.10) +        
                        (v_prob * 0.10) +            
                        (v_wfo * 0.20) +             
                        (v_qual * 0.15) +            
                        (score_project * 0.15)       
                    )
                    
                    if final_score >= 90: grade, color, bg = tr("A (Sangat Baik)", "A (Outstanding)"), "#10b981", "#d1fae5"
                    elif final_score >= 80: grade, color, bg = tr("B (Melampaui Ekspektasi)", "B (Exceeds Expectations)"), "#3b82f6", "#dbeafe"
                    elif final_score >= 70: grade, color, bg = tr("C (Memenuhi Ekspektasi)", "C (Meets Expectations)"), "#f59e0b", "#fef3c7"
                    elif final_score >= 50: grade, color, bg = tr("D (Perlu Perbaikan)", "D (Needs Improvement)"), "#f97316", "#ffedd5"
                    else: grade, color, bg = tr("E (Tidak Memuaskan)", "E (Unsatisfactory)"), "#ef4444", "#fee2e2"

                    st.markdown(f"""
                    <div style="background-color: {bg}; border: 2px solid {color}; padding: 30px; border-radius: 20px; text-align: center; margin-bottom: 20px;">
                        <h4 style="color: {color}; margin:0; letter-spacing: 2px;">{tr("SKOR AKHIR", "FINAL SCORE")}</h4>
                        <h1 style="color: {color}; font-size: 4.5em; margin: 0; font-weight: 800;">{final_score:.1f}</h1>
                        <h3 style="color: {color}; margin:0;">{grade}</h3>
                    </div>
                    """, unsafe_allow_html=True)

                    lbl_radar = [
                        tr('Komunikasi', 'Communication'), tr('KPI Achv', 'KPI Achv'), 
                        tr('Absensi', 'Attendance'), tr('Prob. Solv', 'Prob. Solv'), 
                        tr('WFO', 'WFO'), tr('Kualitas', 'Quality'), tr('Project', 'Project')
                    ]
                    df_r = pd.DataFrame({
                        'Metric': lbl_radar,
                        'Value': [v_kom, score_kpi_final, score_att, v_prob, v_wfo, v_qual, score_project]
                    })
                    fig_r = px.line_polar(df_r, r='Value', theta='Metric', line_close=True)
                    fig_r.update_traces(fill='toself', line_color=color)
                    fig_r.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), margin=dict(t=20, b=20))
                    st.plotly_chart(fig_r, use_container_width=True)
                    
                    report_content = textwrap.dedent(f"""
                        {tr("LAPORAN PENILAIAN KINERJA", "PERFORMANCE APPRAISAL REPORT")}
                        ----------------------------
                        {tr("Karyawan", "Employee")}: {target_emp}
                        {tr("Tanggal", "Date")}: {format_date_custom(datetime.now())}
                        
                        1. {tr("Komunikasi", "Communication")}: {v_kom} ({tr("Bobot", "Weight")} 10%)
                        2. {tr("Pencapaian KPI", "KPI Achievement")}: {score_kpi_final:.2f} ({tr("Bobot", "Weight")} 20%)
                        3. {tr("Kelengkapan Absensi", "Attendance Completeness")}: {score_att:.2f} ({tr("Bobot", "Weight")} 10%)
                        4. {tr("Pemecahan Masalah", "Problem Solving")}: {v_prob} ({tr("Bobot", "Weight")} 10%)
                        5. {tr("Kepatuhan WFO", "WFO Compliance")}: {v_wfo} ({tr("Bobot", "Weight")} 20%)
                        6. {tr("Kualitas Kerja", "Work Quality")}: {v_qual} ({tr("Bobot", "Weight")} 15%)
                        7. {tr("Pengembangan Proyek", "Project Development")}: {score_project:.2f} ({tr("Bobot", "Weight")} 15%)
                            - {tr("Total Jam Aktual", "Actual Total Hours")}: {actual_total_hours:.2f}
                            - {tr("Target Jam Ideal", "Ideal Target Hours")}: {target_total_hours:.2f}
                        
                        {tr("HASIL AKHIR:", "FINAL RESULT:")}
                        - Total Score: {final_score:.2f}
                        - Grade: {grade}
                    """).strip()
                    
                    st.download_button(tr("💾 Download Laporan (TXT)", "💾 Download Report (TXT)"), report_content, f"Appraisal_{target_emp}.txt", use_container_width=True)

else:
    st.info(tr("👋 Silakan upload file absensi di sidebar untuk memulai.", "👋 Please upload your attendance file in the sidebar to start."))