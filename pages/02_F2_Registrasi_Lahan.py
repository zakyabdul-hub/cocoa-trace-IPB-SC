"""
02_F2_Registrasi_Lahan.py
Fitur F2: Registrasi Aset Lahan & Validasi Geospasial
Aktor: Petani
Smart Contract: MasterData.registerLand()
Geospatial: KLHK API Integration (ArcGIS REST) + Folium
"""

import sys
import os
import requests
import urllib3
from datetime import datetime
import streamlit as st

from config import build_transaction

# Nonaktifkan warning SSL Certificate karena server pemerintah sering unverified
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Path setup
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from style_adminhmd import inject_adminhmd_theme

# ============================================================
# KONFIGURASI HALAMAN
# ============================================================
st.set_page_config(
    page_title="F2 — Registrasi Lahan | CacaoTrace",
    page_icon="🗺️",
    layout="wide"
)

inject_adminhmd_theme()

# ============================================================
# GUARD
# ============================================================
def check_auth():
    if not st.session_state.get('is_logged_in'):
        st.warning("⚠️ Silakan login terlebih dahulu.")
        st.page_link("app.py", label="← Kembali ke Dashboard", icon="🏠")
        return False
    if st.session_state.get('role') != "Petani":
        st.error(f"🚫 Akses Ditolak! Halaman ini hanya untuk **Petani**. Role Anda: **{st.session_state.get('role', 'Tidak Diketahui')}**")
        st.page_link("app.py", label="← Kembali ke Dashboard", icon="🏠")
        return False
    return True

# ============================================================
# FUNGSI GEOSPASIAL (KLHK API Connector)
# ============================================================
def cek_status_klhk(lat, lon):
    """
    Melakukan pengecekan ke API Geoportal KLHK.
    Return: dict {'status': 'VALID'|'INVALID'|'ERROR', 'message': str, 'fungsi_kws': str, 'nama_kws': str}
    """
    url = "https://geoportal.menlhk.go.id/server/rest/services/SIGAP_Interaktif/Kawasan_Hutan/MapServer/0/query"
    params = {
        'geometry': f"{lon},{lat}",
        'geometryType': 'esriGeometryPoint',
        'spatialRel': 'esriSpatialRelIntersects',
        'outFields': 'FUNGSI_KWS,NAMA_KWS',
        'returnGeometry': 'false',
        'f': 'json'
    }
    
    try:
        response = requests.get(url, params=params, timeout=10, verify=False)
        response.raise_for_status()
        data = response.json()
        
        if 'error' in data:
            code = data['error'].get('code', 'Unknown')
            msg = data['error'].get('message', 'No details')
            return {
                'status': 'ERROR',
                'message': f"⚠️ API KLHK menolak akses (Error {code}: {msg}).",
                'fungsi_kws': None,
                'nama_kws': None
            }
            
        features = data.get('features', [])
        if len(features) == 0:
            return {
                'status': 'VALID',
                'message': '✅ Lahan Berada di Area Penggunaan Lain (APL) / Luar Kawasan Hutan',
                'fungsi_kws': None,
                'nama_kws': None
            }
        else:
            attr = features[0].get('attributes', {})
            fungsi = attr.get('FUNGSI_KWS', 'Kawasan Hutan')
            nama = attr.get('NAMA_KWS', 'Tidak Diketahui')
            return {
                'status': 'INVALID',
                'message': f"❌ Lahan Terindikasi Masuk Kawasan Hutan: {fungsi}",
                'fungsi_kws': fungsi,
                'nama_kws': nama
            }
            
    except requests.exceptions.Timeout:
        return {'status': 'ERROR', 'message': '⏳ Timeout: Server KLHK tidak merespons dalam 10 detik. Silakan coba lagi.'}
    except Exception as e:
        return {'status': 'ERROR', 'message': f'⚠️ Gagal terhubung ke server KLHK: {str(e)}'}

def cek_status_lahan_lokal(lat, lon):
    """
    Melakukan pengecekan ke file SHP lokal sebagai fallback.
    """
    try:
        import geopandas as gpd
        from shapely.geometry import Point
        
        shp_path = os.path.join(os.path.dirname(__file__), '..', 'forest_zone', 'kawasan_hutan_092017.shp')
        if not os.path.exists(shp_path):
            return {'status': 'ERROR', 'message': '⚠️ File SHP lokal tidak ditemukan. Pastikan file SHP berada di folder forest_zone.'}
        
        # Bounding box query
        gdf = gpd.read_file(shp_path, bbox=(lon-0.001, lat-0.001, lon+0.001, lat+0.001))
        
        if gdf.empty:
            return {
                'status': 'VALID',
                'message': '✅ Lahan Berada di APL / Luar Kawasan Hutan (Hasil Cek SHP Lokal)',
                'fungsi_kws': None,
                'nama_kws': None
            }
            
        point = Point(lon, lat)
        intersects = gdf.contains(point)
        matched = gdf[intersects]
        
        if matched.empty:
            return {
                'status': 'VALID',
                'message': '✅ Lahan Berada di APL / Luar Kawasan Hutan (Hasil Cek SHP Lokal)',
                'fungsi_kws': None,
                'nama_kws': None
            }
        else:
            row = matched.iloc[0]
            fungsi = str(row.get('legend_in', 'Kawasan Hutan')).strip()
            nama = str(row.get('namobj', 'Tidak Diketahui'))
            if nama.lower() == 'none' or nama == '':
                nama = 'Tidak Diketahui'
                
            # Jika merupakan Areal Penggunaan Lain (APL), maka statusnya adalah VALID (bukan kawasan hutan)
            if fungsi.upper() == 'AREAL PENGGUNAAN LAIN':
                return {
                    'status': 'VALID',
                    'message': f'✅ Lahan Berada di Areal Penggunaan Lain (APL) / Luar Kawasan Hutan (Hasil Cek SHP Lokal)',
                    'fungsi_kws': fungsi,
                    'nama_kws': nama
                }
            
            return {
                'status': 'INVALID',
                'message': f"❌ Lahan Terindikasi Masuk Kawasan Hutan: {fungsi} (Hasil Cek SHP Lokal)",
                'fungsi_kws': fungsi,
                'nama_kws': nama
            }
    except ImportError:
        return {'status': 'ERROR', 'message': '⚠️ Modul geopandas atau shapely belum terinstall. Hubungi Admin.'}
    except Exception as e:
        return {'status': 'ERROR', 'message': f'⚠️ Gagal membaca SHP lokal: {str(e)}'}

# ============================================================
# HEADER HALAMAN
# Top Navbar Header
st.markdown("""
<div class="admin-topbar">
    <div class="admin-topbar-title">
        <span style="font-size: 1.5rem;">🗺️</span> F2 — Registrasi Lahan (Validasi Geospasial KLHK)
    </div>
    <div class="admin-topbar-meta">
        <span class="admin-badge badge-petani">Aktor: Petani</span>
        <span class="admin-badge badge-connected">MasterData.registerLand()</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Page Header
st.markdown("""
<div class="admin-page-header">
    <h1>Registrasi Aset Lahan & Validasi Geospasial</h1>
    <p>Validasi koordinat lahan secara realtime menggunakan ArcGIS REST API Geoportal KLHK sebelum dicatat permanen di blockchain.</p>
</div>
""", unsafe_allow_html=True)

if not check_auth():
    st.stop()

# ============================================================
# LAYOUT UTAMA
# ============================================================
col_form, col_map = st.columns([3, 2], gap="large")

with col_form:
    st.markdown("""
    <div class="form-card">
        <div style="font-family:'Space Grotesk',sans-serif;font-size:1.1rem;font-weight:600;
             color:#38BDF8;margin-bottom:8px;">STEP 1: Validasi Koordinat Lahan</div>
    </div>
    """, unsafe_allow_html=True)

    # Tampilkan daftar varietas yang sudah terdaftar
    with st.expander("📊 Lihat Daftar Varietas Terdaftar (F1)", expanded=False):
        if st.session_state.get('ganache_connected'):
            try:
                varietas_ids = st.session_state.contracts['MasterData'].functions.getAllVarietasIds().call()
                if varietas_ids:
                    data_var = []
                    for vid in varietas_ids:
                        vdata = st.session_state.contracts['MasterData'].functions.dataVarietas(vid).call()
                        data_var.append({
                            "ID Varietas": vdata[0],
                            "SK Pelepasan": vdata[1],
                            "Masa Edar": vdata[2],
                            "Keterangan": vdata[4]
                        })
                    st.dataframe(data_var, use_container_width=True, hide_index=True)
                else:
                    st.info("Belum ada varietas yang terdaftar.")
            except Exception as e:
                st.error(f"Gagal memuat varietas: {e}")

    # 1. FORM INPUT KOORDINAT (STEP 1)
    col_lat, col_lon = st.columns(2)
    with col_lat:
        latitude = st.number_input(
            "🌐 Latitude *",
            min_value=-90.0, max_value=90.0, value=-5.5, step=0.0001, format="%.6f"
        )
    with col_lon:
        longitude = st.number_input(
            "🌐 Longitude *",
            min_value=-180.0, max_value=180.0, value=119.5, step=0.0001, format="%.6f"
        )

    # Tombol Validasi
    if st.button("🌍 Validasi Koordinat Lahan", use_container_width=True):
        with st.spinner("Menghubungi Server Geoportal KLHK..."):
            result_state = cek_status_klhk(latitude, longitude)
            
        if result_state['status'] == 'ERROR':
            st.warning(result_state['message'])
            with st.spinner("⏳ KLHK Error. Beralih memindai data SHP lokal (sekitar 15 detik)..."):
                result_state = cek_status_lahan_lokal(latitude, longitude)
                
        st.session_state['klhk_result'] = result_state
        st.session_state['klhk_lat'] = latitude
        st.session_state['klhk_lon'] = longitude

    # Tampilkan Hasil Validasi Step 1
    klhk_result = st.session_state.get('klhk_result')
    val_lat = st.session_state.get('klhk_lat', latitude)
    val_lon = st.session_state.get('klhk_lon', longitude)

    # Cek apakah parameter input berbeda dengan yang sudah divalidasi
    if klhk_result and (latitude != val_lat or longitude != val_lon):
        st.warning("⚠️ Koordinat telah diubah. Silakan tekan tombol 'Validasi Koordinat Lahan' kembali.")
        val_done = False
    elif klhk_result:
        val_done = True
        if klhk_result['status'] == 'VALID':
            st.markdown(f"""
            <div class="geo-success" style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:12px;padding:16px;margin-top:12px;">
                <div style="color:#15803d;font-weight:700;font-size:1.1rem;">✅ Validasi Lolos</div>
                <div style="color:#166534;font-size:0.9rem;margin-top:4px;">{klhk_result['message']}</div>
            </div>
            """, unsafe_allow_html=True)
        elif klhk_result['status'] == 'INVALID':
            st.markdown(f"""
            <div class="geo-danger" style="background:#fef2f2;border:1px solid #fecdd3;border-radius:12px;padding:16px;margin-top:12px;">
                <div style="color:#b91c1c;font-weight:700;font-size:1.1rem;">🚫 Validasi Gagal</div>
                <div style="color:#991b1b;font-size:0.9rem;margin-top:4px;">{klhk_result['message']}</div>
                <div style="color:#7f1d1d;font-size:0.85rem;margin-top:8px;font-weight:600;">Kawasan: {klhk_result.get('nama_kws','-')}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:12px;padding:16px;margin-top:12px;">
                <div style="color:#b45309;font-weight:700;">⚠️ Terjadi Kesalahan</div>
                <div style="color:#92400e;font-size:0.9rem;">{klhk_result['message']}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        val_done = False


    # 2. FORM INPUT DATA LAHAN & BLOCKCHAIN (STEP 2)
    step2_header_color = "#38BDF8" if val_done and klhk_result['status'] == 'VALID' else "#475569"
    step2_label = "STEP 2: Detail & Registrasi (Terkunci)" if not val_done or klhk_result['status'] != 'VALID' else "STEP 2: Detail Lahan & Registrasi Blockchain"
    
    st.markdown(f"""
    <div class="form-card" style="margin-top:24px;">
        <div style="font-family:'Space Grotesk',sans-serif;font-size:1.1rem;font-weight:600;
             color:{step2_header_color};margin-bottom:8px;">{step2_label}</div>
    </div>
    """, unsafe_allow_html=True)

    # Inisialisasi session state jika belum ada
    if 'prefilled_no_stdb' not in st.session_state:
        st.session_state.prefilled_no_stdb = ""

    # Form Registrasi Lahan (Tanpa st.form untuk respon real-time ID)
    st.markdown("**📋 Informasi Dasar Lahan**")
    col_id1, col_id2 = st.columns(2)
    with col_id1:
        nama_petani = st.text_input("Nama Petani *", placeholder="Contoh: AGUS", key="lahan_nama_petani")
    with col_id2:
        no_stdb = st.text_input("📄 No. STDB *", placeholder="Contoh: 1234567", key="lahan_no_stdb")
    
    luas = st.number_input("📐 Luas Lahan (m²) *", min_value=1, max_value=10_000_000, value=10000, step=100)
    
    st.markdown("**🌱 Varietas Benih yang Digunakan**")
    # Ambil daftar varietas dari blockchain
    varietas_list = []
    if st.session_state.get('ganache_connected'):
        try:
            varietas_list = st.session_state.contracts['MasterData'].functions.getAllVarietasIds().call()
        except Exception:
            pass
            
    col_var1, col_var2 = st.columns(2)
    with col_var1:
        id_var1 = st.selectbox("🌱 ID Varietas Utama *", options=[""] + varietas_list, disabled=len(varietas_list) == 0)
    with col_var2:
        id_var2 = st.selectbox("🌿 ID Varietas Opsional", options=[""] + varietas_list, disabled=len(varietas_list) == 0)

    # Dynamic real-time sequence and ID calculation
    id_lahan = ""
    seq = ""
    if nama_petani.strip() and no_stdb.strip():
        from utils import get_next_sequence_lahan, generate_lahan_id
        if st.session_state.get('ganache_connected'):
            master_data = st.session_state.contracts['MasterData']
            seq = get_next_sequence_lahan(master_data, no_stdb.strip())
            id_lahan = generate_lahan_id(nama_petani.strip(), no_stdb.strip(), seq)
        else:
            id_lahan = "LAHAN-[Petani]-[STDB]-001"

    st.text_input(
        "🏷️ ID Lahan Tergenerate (Otomatis) *",
        value=id_lahan,
        disabled=True,
        help="ID unik lahan ini yang dihasilkan secara otomatis dari Nama Petani, No STDB, dan urutan database."
    )
    if seq:
        st.caption(f"ℹ️ Nomor Urut STDB terdeteksi di blockchain: **#{seq}**")
    
    st.markdown("---")
    
    is_disabled = not val_done or klhk_result['status'] != 'VALID'
    
    submitted = st.button(
        "🔗 Daftarkan Lahan ke Blockchain",
        use_container_width=True,
        disabled=is_disabled
    )
    
    if submitted:
        errors = []
        if not nama_petani.strip(): errors.append("Nama Petani wajib diisi.")
        if not no_stdb.strip(): errors.append("No. STDB wajib diisi.")
        if not id_var1.strip(): errors.append("ID Varietas Utama wajib diisi.")
        if not id_lahan: errors.append("Gagal membuat ID Lahan. Lengkapi data di atas.")
        
        if errors:
            for err in errors: st.error(f"❌ {err}")
        elif not st.session_state.get('private_key'):
            st.error("❌ Private Key belum diinput pada sidebar!")
        else:
            # Kirim ke blockchain
            with st.spinner("⏳ Mendaftarkan lahan ke blockchain..."):
                try:
                    w3 = st.session_state.w3
                    master_data = st.session_state.contracts['MasterData']
                    koordinat_str = f"{val_lat:.6f},{val_lon:.6f}"
                    is_bebas = True  # Karena sudah lolos validasi step 1
                    
                    contract_func = master_data.functions.registerLand(
                        id_lahan,
                        no_stdb.strip().upper(),
                        koordinat_str,
                        int(luas),
                        id_var1.strip(),
                        id_var2.strip() if id_var2 else "",
                        is_bebas
                    )
                    
                    result_tx = build_transaction(
                        w3, contract_func,
                        st.session_state.wallet_address,
                        st.session_state.private_key
                    )
                    
                    if result_tx['success']:
                        st.markdown(f"""
                        <div class="tx-success" style="background:#f0f9ff;border:1px solid #bae6fd;border-radius:12px;padding:18px;">
                            <div style="font-size:1.25rem;font-weight:700;color:#0369a1;margin-bottom:14px;">✅ Lahan Berhasil Didaftarkan!</div>
                            <table style="font-size:0.88rem;color:#1e293b;width:100%;border-collapse:collapse;">
                                <tr style="border-bottom:1px solid #e0f2fe;"><td style="color:#0284c7;font-weight:600;padding:6px 0;width:35%;">🏷️ ID Lahan</td><td style="color:#0f172a;padding:6px 0;"><strong>{id_lahan}</strong></td></tr>
                                <tr style="border-bottom:1px solid #e0f2fe;"><td style="color:#0284c7;font-weight:600;padding:6px 0;">📄 No. STDB</td><td style="color:#0f172a;padding:6px 0;">{no_stdb.upper()}</td></tr>
                                <tr style="border-bottom:1px solid #e0f2fe;"><td style="color:#0284c7;font-weight:600;padding:6px 0;">📍 Koordinat</td><td style="color:#0f172a;padding:6px 0;">{koordinat_str}</td></tr>
                                <tr><td style="color:#0284c7;font-weight:600;padding:6px 0;">🔗 TX Hash</td>
                                    <td style="font-family:monospace;font-size:0.75rem;color:#334155;word-break:break-all;padding:6px 0;">{result_tx['tx_hash']}</td>
                                </tr>
                            </table>
                        </div>
                        """, unsafe_allow_html=True)
                        st.balloons()
                    else:
                        st.error(f"❌ Transaksi Gagal: {result_tx['error']}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# ============================================================
# KOLOM KANAN — PETA INTERAKTIF
# ============================================================
with col_map:
    st.markdown("""
    <div class="form-card">
        <div style="font-family:'Space Grotesk',sans-serif;font-size:1.1rem;font-weight:600;
             color:#38BDF8;margin-bottom:14px;">🌍 Peta Lokasi Lahan</div>
    """, unsafe_allow_html=True)
    
    try:
        import folium
        from streamlit_folium import st_folium
        
        # Penentuan warna marker berdasarkan status
        if not val_done:
            marker_color = "blue"
            popup_html = f"<b>Belum Divalidasi</b><br>Lat: {latitude}<br>Lon: {longitude}"
            map_lat = latitude
            map_lon = longitude
        else:
            map_lat = val_lat
            map_lon = val_lon
            if klhk_result['status'] == 'VALID':
                marker_color = "green"
                popup_html = f"<b>✅ APL (Aman)</b><br>Lat: {map_lat}<br>Lon: {map_lon}"
            elif klhk_result['status'] == 'INVALID':
                marker_color = "red"
                popup_html = f"<b>🚫 Kawasan Hutan</b><br>Fungsi: {klhk_result.get('fungsi_kws','-')}<br>Lat: {map_lat}<br>Lon: {map_lon}"
            else:
                marker_color = "orange"
                popup_html = f"<b>⚠️ Error KLHK</b><br>Lat: {map_lat}<br>Lon: {map_lon}"

        # Bangun Peta
        m = folium.Map(location=[map_lat, map_lon], zoom_start=12, tiles="CartoDB dark_matter")
        folium.Marker(
            location=[map_lat, map_lon],
            popup=folium.Popup(popup_html, max_width=200),
            icon=folium.Icon(color=marker_color, icon="map-marker", prefix="fa"),
        ).add_to(m)
        
        # Lingkaran radius 500m
        circle_color = "#0284C7" if marker_color == "blue" else ("#10B981" if marker_color == "green" else ("#EF4444" if marker_color == "red" else "#F59E0B"))
        folium.Circle(
            location=[map_lat, map_lon],
            radius=500,
            color=circle_color, fill=True, fill_opacity=0.1, weight=1.5
        ).add_to(m)
        
        st_folium(m, width=None, height=320, returned_objects=[])
        
    except ImportError:
        st.warning("⚠️ Module 'folium' atau 'streamlit-folium' belum terinstall.")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # ── Panel Cek Lahan di Blockchain ──────────────────────
    st.markdown("""
    <div class="form-card" style="margin-top: 12px;">
        <div style="font-family: 'Space Grotesk', sans-serif; font-size: 1rem; font-weight: 600; 
             color: #38BDF8; margin-bottom: 16px;">🔍 Cek Data Lahan Tersimpan</div>
    """, unsafe_allow_html=True)
    
    check_lahan_id = st.text_input("Cari ID Lahan", placeholder="LHN-POLMAN-001", key="check_lahan")
    
    if st.button("🔍 Cek Lahan", key="btn_check_lahan"):
        if check_lahan_id.strip() and st.session_state.get('ganache_connected'):
            try:
                data_lahan = st.session_state.contracts['MasterData'].functions.dataLahan(check_lahan_id.strip()).call()
                id_l, no_s, koor, luas_l, v1, v2, is_bebas_def, petani, ts = data_lahan
                
                if ts == 0:
                    st.warning(f"⚠️ Lahan `{check_lahan_id}` belum terdaftar.")
                else:
                    reg_time = datetime.fromtimestamp(ts).strftime("%d %b %Y, %H:%M")
                    bebas_str = "✅ Ya" if is_bebas_def else "❌ Tidak"
                    bebas_color = "#4ADE80" if is_bebas_def else "#F87171"
                    st.markdown(f"""
                    <div style="background: rgba(2,132,199,0.05); border: 1px solid rgba(56,189,248,0.2); 
                         border-radius: 12px; padding: 14px; font-size: 0.78rem; color: #BAE6FD;">
                        <div style="color: #38BDF8; font-weight: 600; margin-bottom: 10px;">✅ Lahan Ditemukan</div>
                        <div>🏷️ ID: <strong>{id_l}</strong></div>
                        <div>📄 STDB: {no_s}</div>
                        <div>📍 Koordinat: {koor}</div>
                        <div>📐 Luas: {luas_l:,} m²</div>
                        <div>🌱 Var 1: {v1}</div>
                        <div>🌲 Bebas Def.: <span style="color: {bebas_color}; font-weight: bold;">{bebas_str}</span></div>
                        <div>🕐 Terdaftar: {reg_time}</div>
                    </div>
                    """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# PANEL DAFTAR SEMUA LAHAN (Full Width)
# ============================================================
st.markdown("---")
st.markdown("""
<div style="font-family: 'Space Grotesk', sans-serif; font-size: 1.2rem; font-weight: 700;
     color: #38BDF8; margin-bottom: 16px;">
    📋 Daftar Semua Lahan Terdaftar
</div>
""", unsafe_allow_html=True)

col_ref2, col_cnt2, col_filter2 = st.columns([1, 2, 2])
with col_ref2:
    refresh_lahan = st.button("🔄 Muat / Refresh", key="btn_refresh_lahan")
with col_filter2:
    filter_milik_saya = st.checkbox("👤 Tampilkan Lahan Saya Saja", key="chk_lahan_saya")

if refresh_lahan or st.session_state.get('lahan_list_loaded'):
    if st.session_state.get('ganache_connected'):
        try:
            contracts = st.session_state.contracts
            master_data = contracts['MasterData']

            # Pilih fungsi berdasarkan filter
            if filter_milik_saya and st.session_state.get('wallet_address'):
                from web3 import Web3
                my_addr = Web3.to_checksum_address(st.session_state.wallet_address)
                all_ids = master_data.functions.getLahanByPetani(my_addr).call()
                filter_label = "milik wallet Anda"
            else:
                all_ids = master_data.functions.getAllLahanIds().call()
                filter_label = "seluruh blockchain"

            total = master_data.functions.getTotalLahan().call()
            st.session_state['lahan_list_loaded'] = True

            with col_cnt2:
                st.markdown(f"""
                <div style="background: rgba(2,132,199,0.08); border: 1px solid rgba(56,189,248,0.2);
                     border-radius: 10px; padding: 10px 16px; font-size: 0.85rem; color: #7DD3FC;">
                    📊 Total Lahan ({filter_label}): <strong style="color: #38BDF8; font-size: 1.1rem;">{len(all_ids)}</strong>
                    &nbsp;|&nbsp; Total Keseluruhan: <strong>{total}</strong>
                </div>
                """, unsafe_allow_html=True)

            if not all_ids:
                st.info("📭 Belum ada lahan yang terdaftar.")
            else:
                rows = []
                for lid in all_ids:
                    try:
                        data = master_data.functions.dataLahan(lid).call()
                        id_l, no_s, koor, luas_lahan, v1, v2, is_bebas_def, petani, ts = data
                        reg_time = datetime.fromtimestamp(ts).strftime("%d %b %Y")
                        rows.append({
                            "ID Lahan": id_l,
                            "No. STDB": no_s,
                            "Koordinat": koor,
                            "Luas (m2)": f"{luas_lahan:,}",
                            "Var. Utama": v1,
                            "Bebas Def.": "Ya" if is_bebas_def else "Tidak",
                            "Petani": f"{petani[:8]}...{petani[-4:]}",
                            "Tgl Daftar": reg_time,
                        })
                    except Exception:
                        rows.append({"ID Lahan": lid, "No. STDB": "Error", "Koordinat": "-",
                                     "Luas (m2)": "-", "Var. Utama": "-", "Bebas Def.": "-",
                                     "Petani": "-", "Tgl Daftar": "-"})

                import pandas as pd
                df = pd.DataFrame(rows)
                st.dataframe(df, use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"❌ Gagal memuat daftar lahan: {str(e)}")
    else:
        st.warning("⚠️ Tidak terhubung ke blockchain.")
