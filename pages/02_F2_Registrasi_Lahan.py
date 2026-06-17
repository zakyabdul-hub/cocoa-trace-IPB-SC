"""
02_F2_Registrasi_Lahan.py
Fitur F2: Registrasi Aset Lahan & Validasi Geospasial
Aktor: Petani
Smart Contract: MasterData.registerLand()
Geospatial: geopandas + shapely
"""

import streamlit as st
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import build_transaction, SHAPEFILE_PATH

# ============================================================
# KONFIGURASI HALAMAN
# ============================================================
st.set_page_config(
    page_title="F2 — Registrasi Lahan | CacaoTrace",
    page_icon="🗺️",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
.stApp { background: linear-gradient(135deg, #0A0F1A 0%, #060912 100%) !important; color: #F0F4FF !important; }
[data-testid="stSidebar"] { background: #060912 !important; border-right: 1px solid rgba(56,189,248,0.2) !important; }
.page-header {
    background: linear-gradient(135deg, rgba(2,132,199,0.2) 0%, rgba(56,189,248,0.08) 100%);
    border: 1px solid rgba(56,189,248,0.2); border-radius: 20px; padding: 32px; margin-bottom: 24px;
    border-left: 4px solid #0284C7;
}
.form-card {
    background: rgba(2,132,199,0.05); border: 1px solid rgba(56,189,248,0.15);
    border-radius: 16px; padding: 28px; margin: 12px 0;
}
.geo-success {
    background: linear-gradient(135deg, rgba(34,197,94,0.1), rgba(34,197,94,0.05));
    border: 1px solid rgba(34,197,94,0.3); border-radius: 12px; padding: 16px;
}
.geo-danger {
    background: linear-gradient(135deg, rgba(239,68,68,0.15), rgba(239,68,68,0.05));
    border: 1px solid rgba(239,68,68,0.4); border-radius: 12px; padding: 16px;
    animation: pulse-danger 2s ease-in-out infinite;
}
@keyframes pulse-danger {
    0%, 100% { box-shadow: 0 0 0 0 rgba(239,68,68,0); }
    50% { box-shadow: 0 0 20px 4px rgba(239,68,68,0.15); }
}
.tx-success {
    background: linear-gradient(135deg, rgba(2,132,199,0.15), rgba(56,189,248,0.08));
    border: 1px solid rgba(56,189,248,0.4); border-radius: 12px; padding: 20px;
}
.stTextInput > div > div > input, .stNumberInput > div > div > input {
    background: rgba(2,132,199,0.05) !important; border: 1px solid rgba(56,189,248,0.2) !important;
    border-radius: 10px !important; color: #F0F4FF !important;
}
.stButton > button {
    background: linear-gradient(135deg, #0284C7, #0EA5E9) !important; color: white !important;
    border: none !important; border-radius: 10px !important; font-weight: 600 !important;
    padding: 0.6rem 2rem !important; transition: all 0.3s !important;
}
.stButton > button:hover { transform: translateY(-2px) !important; box-shadow: 0 8px 24px rgba(56,189,248,0.3) !important; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

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
# FUNGSI GEOSPASIAL
# ============================================================
@st.cache_data(show_spinner=False)
def load_kawasan_hutan():
    """
    Memuat file shapefile kawasan hutan.
    Menggunakan st.cache_data agar tidak reload setiap render.
    """
    try:
        import geopandas as gpd
        shapefile = str(SHAPEFILE_PATH)
        if not os.path.exists(shapefile):
            return None, "FILE_NOT_FOUND"
        
        gdf = gpd.read_file(shapefile)
        # Pastikan CRS adalah WGS84 (EPSG:4326)
        if gdf.crs is None or gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs("EPSG:4326")
        return gdf, "OK"
    except ImportError:
        return None, "IMPORT_ERROR"
    except Exception as e:
        return None, f"ERROR: {str(e)}"


def cek_bebas_deforestasi(lat: float, lon: float) -> tuple:
    """
    Memeriksa apakah koordinat berada di luar kawasan hutan.
    
    Returns:
        tuple: (is_bebas: bool, status_message: str, detail: str)
    """
    try:
        from shapely.geometry import Point
        
        gdf, status = load_kawasan_hutan()
        
        if status == "FILE_NOT_FOUND":
            return True, "FALLBACK", "⚠️ File peta kawasan hutan tidak ditemukan. Mode fallback: semua lahan dianggap bebas deforestasi."
        
        if status == "IMPORT_ERROR":
            return True, "FALLBACK", "⚠️ Library geospasial tidak tersedia. Mode fallback aktif."
        
        if status.startswith("ERROR"):
            return True, "FALLBACK", f"⚠️ Error memuat peta: {status}"
        
        # Buat Point dari koordinat petani
        titik_lahan = Point(lon, lat)  # shapely: (x=lon, y=lat)
        
        # Cek apakah titik berada di dalam poligon kawasan hutan
        for _, kawasan in gdf.iterrows():
            if kawasan.geometry.contains(titik_lahan) or kawasan.geometry.intersects(titik_lahan):
                nama = kawasan.get('nama_kawasan', 'Kawasan Hutan')
                return False, "DALAM_HUTAN", f"❌ Koordinat berada di dalam **{nama}**"
        
        return True, "BEBAS", "✅ Koordinat berada di luar kawasan hutan"
    except Exception as e:
        return True, "FALLBACK", f"⚠️ Error validasi geospasial: {str(e)}. Mode fallback aktif."


# ============================================================
# HEADER HALAMAN
# ============================================================
st.markdown("""
<div class="page-header">
    <div style="font-size: 2rem; margin-bottom: 8px;">🗺️</div>
    <div style="font-family: 'Space Grotesk', sans-serif; font-size: 1.8rem; font-weight: 700; color: #38BDF8;">
        F2 — Registrasi Lahan
    </div>
    <div style="color: #7DD3FC; font-size: 0.95rem; margin-top: 8px;">
        Registrasi lahan pertanian kakao dengan validasi geospasial otomatis terhadap kawasan hutan.
    </div>
    <div style="margin-top: 12px; font-size: 0.75rem; color: #38BDF8;">
        📋 Smart Contract: <code style="background: rgba(56,189,248,0.1); padding: 2px 8px; border-radius: 4px;">MasterData.registerLand()</code>
        &nbsp;|&nbsp; 👤 Aktor: <strong>Petani</strong>
    </div>
</div>
""", unsafe_allow_html=True)

if not check_auth():
    st.stop()

# ============================================================
# LAYOUT UTAMA
# ============================================================
col_form, col_map = st.columns([3, 2], gap="large")

# State untuk hasil validasi geospasial
if 'geo_result' not in st.session_state:
    st.session_state.geo_result = None
if 'is_bebas' not in st.session_state:
    st.session_state.is_bebas = None

with col_form:
    st.markdown("""
    <div class="form-card">
        <div style="font-family: 'Space Grotesk', sans-serif; font-size: 1.1rem; font-weight: 600; 
             color: #38BDF8; margin-bottom: 20px;">📝 Form Registrasi Lahan</div>
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

    with st.form("form_registrasi_lahan"):
        st.markdown("**📋 Informasi Dasar Lahan**")
        col_id1, col_id2 = st.columns(2)
        with col_id1:
            id_lahan = st.text_input(
                "🏷️ ID Lahan *",
                placeholder="LHN-POLMAN-001",
                help="ID unik untuk lahan ini"
            )
        with col_id2:
            no_stdb = st.text_input(
                "📄 No. STDB *",
                placeholder="STDB-123/2024",
                help="Nomor Surat Tanda Daftar Budidaya"
            )
        
        st.markdown("**📍 Koordinat GPS Lahan**")
        col_lat, col_lon = st.columns(2)
        with col_lat:
            latitude = st.number_input(
                "🌐 Latitude *",
                min_value=-90.0,
                max_value=90.0,
                value=-5.5,
                step=0.0001,
                format="%.6f",
                help="Koordinat lintang (contoh: -5.5 untuk 5.5° LS)"
            )
        with col_lon:
            longitude = st.number_input(
                "🌐 Longitude *",
                min_value=-180.0,
                max_value=180.0,
                value=119.5,
                step=0.0001,
                format="%.6f",
                help="Koordinat bujur (contoh: 119.5 untuk 119.5° BT)"
            )
        
        luas = st.number_input(
            "📐 Luas Lahan (m²) *",
            min_value=1,
            max_value=10_000_000,
            value=10000,
            step=100,
            help="Luas lahan dalam meter persegi"
        )
        
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
            id_var1 = st.selectbox(
                "🌱 ID Varietas Utama *",
                options=[""] + varietas_list,
                format_func=lambda x: "Pilih Varietas..." if x == "" else x,
                help="Harus terdaftar di MasterData oleh Penangkar",
                disabled=len(varietas_list) == 0,
            )
            if not varietas_list:
                st.caption("⚠️ Belum ada Varietas terdaftar di F1")
        with col_var2:
            id_var2 = st.selectbox(
                "🌿 ID Varietas Opsional",
                options=[""] + varietas_list,
                format_func=lambda x: "(Kosongkan jika tidak ada)" if x == "" else x,
                help="Varietas benih kedua (opsional)",
                disabled=len(varietas_list) == 0,
            )
        
        st.markdown("---")
        st.markdown(f"""
        <div style="font-size: 0.8rem; color: #7DD3FC; margin-bottom: 12px;">
            🔑 Transaksi dari wallet: <code>{st.session_state.get('wallet_address', 'N/A')[:20]}...</code>
        </div>
        """, unsafe_allow_html=True)
        
        submitted = st.form_submit_button(
            "🗺️ Validasi Geospasial & Daftarkan Lahan",
            use_container_width=True
        )
        
        if submitted:
            # Validasi form
            errors = []
            if not id_lahan.strip():
                errors.append("ID Lahan wajib diisi.")
            if not no_stdb.strip():
                errors.append("No. STDB wajib diisi.")
            if not id_var1.strip():
                errors.append("ID Varietas Utama wajib diisi.")
            
            if errors:
                for err in errors:
                    st.error(f"❌ {err}")
            elif not st.session_state.get('private_key'):
                st.error("❌ Private Key belum diinput!")
            else:
                # STEP 1: Validasi Geospasial
                with st.spinner("🌍 Memvalidasi koordinat terhadap peta kawasan hutan..."):
                    is_bebas, geo_status, geo_message = cek_bebas_deforestasi(latitude, longitude)
                    st.session_state.geo_result = {
                        'is_bebas': is_bebas,
                        'status': geo_status,
                        'message': geo_message,
                        'lat': latitude,
                        'lon': longitude,
                    }
                    st.session_state.is_bebas = is_bebas
                
                # STEP 2: Tampilkan hasil validasi
                if not is_bebas:
                    st.markdown(f"""
                    <div class="geo-danger">
                        <div style="font-size: 1.1rem; color: #FCA5A5; font-weight: 700; margin-bottom: 8px;">
                            🚫 Transaksi DITOLAK — Lahan Masuk Kawasan Hutan
                        </div>
                        <div style="color: #FCA5A5; font-size: 0.85rem;">{geo_message}</div>
                        <div style="margin-top: 10px; font-size: 0.8rem; color: #F87171;">
                            Koordinat ({latitude}, {longitude}) terindikasi berada di dalam kawasan hutan.<br>
                            <strong>Transaksi tidak dikirim ke blockchain.</strong>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # Tampilkan status geo
                    if geo_status == "FALLBACK":
                        st.markdown(f"""
                        <div class="geo-success">
                            <div style="color: #FCD34D; font-size: 0.85rem;">⚠️ {geo_message}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="geo-success">
                            <div style="color: #4ADE80; font-weight: 600;">{geo_message}</div>
                            <div style="color: #86EFAC; font-size: 0.8rem; margin-top: 4px;">
                                ✅ Koordinat ({latitude:.6f}, {longitude:.6f}) — Bebas kawasan hutan
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # STEP 3: Kirim ke blockchain
                    with st.spinner("⏳ Mendaftarkan lahan ke blockchain..."):
                        try:
                            w3 = st.session_state.w3
                            contracts = st.session_state.contracts
                            master_data = contracts['MasterData']
                            
                            # Format koordinat sebagai string
                            koordinat_str = f"{latitude:.6f},{longitude:.6f}"
                            
                            contract_func = master_data.functions.registerLand(
                                id_lahan.strip(),
                                no_stdb.strip(),
                                koordinat_str,
                                int(luas),
                                id_var1.strip(),
                                id_var2.strip() if id_var2 else "",
                                is_bebas
                            )
                            
                            result = build_transaction(
                                w3,
                                contract_func,
                                st.session_state.wallet_address,
                                st.session_state.private_key
                            )
                            
                            if result['success']:
                                st.markdown(f"""
                                <div class="tx-success">
                                    <div style="font-size: 1.2rem; color: #38BDF8; margin-bottom: 12px;">✅ Lahan Berhasil Didaftarkan!</div>
                                    <table style="font-size: 0.8rem; color: #BAE6FD; width: 100%;">
                                        <tr><td style="color: #7DD3FC; padding: 3px 0;">🏷️ ID Lahan</td><td><strong>{id_lahan}</strong></td></tr>
                                        <tr><td style="color: #7DD3FC; padding: 3px 0;">📄 No. STDB</td><td>{no_stdb}</td></tr>
                                        <tr><td style="color: #7DD3FC; padding: 3px 0;">📍 Koordinat</td><td>{koordinat_str}</td></tr>
                                        <tr><td style="color: #7DD3FC; padding: 3px 0;">📐 Luas</td><td>{luas:,} m²</td></tr>
                                        <tr><td style="color: #7DD3FC; padding: 3px 0;">🌱 Varietas 1</td><td>{id_var1}</td></tr>
                                        <tr><td style="color: #7DD3FC; padding: 3px 0;">🌿 Varietas 2</td><td>{id_var2 or '-'}</td></tr>
                                        <tr><td style="color: #7DD3FC; padding: 3px 0;">🌲 Bebas Deforestasi</td><td style="color: #4ADE80; font-weight: bold;">✅ Ya</td></tr>
                                        <tr><td style="color: #7DD3FC; padding: 3px 0;">🔗 TX Hash</td>
                                            <td style="font-family: monospace; font-size: 0.7rem;">{result['tx_hash'][:24]}...{result['tx_hash'][-8:]}</td>
                                        </tr>
                                    </table>
                                </div>
                                """, unsafe_allow_html=True)
                                st.balloons()
                            else:
                                st.error(f"❌ Transaksi Gagal: {result['error']}")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
    
    st.markdown("</div>", unsafe_allow_html=True)

with col_map:
    # Status Geospasial
    st.markdown("""
    <div class="form-card">
        <div style="font-family: 'Space Grotesk', sans-serif; font-size: 1rem; font-weight: 600; 
             color: #38BDF8; margin-bottom: 16px;">🌍 Validasi Geospasial</div>
    """, unsafe_allow_html=True)
    
    # Status file .shp
    gdf, status = load_kawasan_hutan()
    if status == "OK" and gdf is not None:
        st.markdown(f"""
        <div style="background: rgba(34,197,94,0.08); border: 1px solid rgba(34,197,94,0.2); 
             border-radius: 10px; padding: 12px; font-size: 0.8rem; color: #86EFAC;">
            ✅ Peta kawasan hutan berhasil dimuat<br>
            📊 {len(gdf)} kawasan hutan terdaftar<br>
            🗺️ Sistem koordinat: WGS84 (EPSG:4326)
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background: rgba(245,158,11,0.08); border: 1px solid rgba(245,158,11,0.2); 
             border-radius: 10px; padding: 12px; font-size: 0.8rem; color: #FCD34D;">
            ⚠️ Mode Fallback Aktif<br>
            File peta kawasan hutan tidak ditemukan.<br>
            Jalankan: <code>python create_shapefile_simulasi.py</code>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Panel Cek Lahan
    st.markdown("""
    <div class="form-card" style="margin-top: 12px;">
        <div style="font-family: 'Space Grotesk', sans-serif; font-size: 1rem; font-weight: 600; 
             color: #38BDF8; margin-bottom: 16px;">🔍 Cek Data Lahan</div>
    """, unsafe_allow_html=True)
    
    check_lahan_id = st.text_input("Cari ID Lahan", placeholder="LHN-POLMAN-001", key="check_lahan")
    
    if st.button("🔍 Cek Lahan", key="btn_check_lahan"):
        if check_lahan_id.strip() and st.session_state.get('ganache_connected'):
            try:
                contracts = st.session_state.contracts
                data = contracts['MasterData'].functions.dataLahan(check_lahan_id.strip()).call()
                id_l, no_s, koor, luas, v1, v2, is_bebas, petani, ts = data
                
                if ts == 0:
                    st.warning(f"⚠️ Lahan `{check_lahan_id}` belum terdaftar.")
                else:
                    reg_time = datetime.fromtimestamp(ts).strftime("%d %b %Y, %H:%M")
                    bebas_str = "✅ Ya" if is_bebas else "❌ Tidak"
                    bebas_color = "#4ADE80" if is_bebas else "#F87171"
                    st.markdown(f"""
                    <div style="background: rgba(2,132,199,0.05); border: 1px solid rgba(56,189,248,0.2); 
                         border-radius: 12px; padding: 14px; font-size: 0.78rem; color: #BAE6FD;">
                        <div style="color: #38BDF8; font-weight: 600; margin-bottom: 10px;">✅ Lahan Ditemukan</div>
                        <div>🏷️ ID: <strong>{id_l}</strong></div>
                        <div>📄 STDB: {no_s}</div>
                        <div>📍 Koordinat: {koor}</div>
                        <div>📐 Luas: {luas:,} m²</div>
                        <div>🌱 Var 1: {v1}</div>
                        <div>🌿 Var 2: {v2 or '-'}</div>
                        <div>🌲 Bebas Def.: <span style="color: {bebas_color}; font-weight: bold;">{bebas_str}</span></div>
                        <div>🕐 Terdaftar: {reg_time}</div>
                    </div>
                    """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    st.markdown("</div>", unsafe_allow_html=True)

    # Panduan Koordinat Simulasi
    if gdf is not None and status == "OK":
        st.markdown("""
        <div style="background: rgba(2,132,199,0.05); border: 1px solid rgba(56,189,248,0.1); 
             border-radius: 12px; padding: 14px; margin-top: 12px; font-size: 0.78rem; color: #7DD3FC;">
            <div style="font-weight: 600; color: #38BDF8; margin-bottom: 8px;">📌 Koordinat Testing (Simulasi)</div>
            <div>✅ <strong>Bebas</strong>: Lat=-5.5, Lon=119.5</div>
            <div>❌ <strong>Kawasan Hutan A</strong>: Lat=-3.2, Lon=120.7</div>
            <div>❌ <strong>Kawasan Hutan B</strong>: Lat=-4.2, Lon=119.2</div>
        </div>
        """, unsafe_allow_html=True)

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
                        id_l, no_s, koor, luas, v1, v2, is_bebas, petani, ts = data
                        reg_time = datetime.fromtimestamp(ts).strftime("%d %b %Y")
                        rows.append({
                            "ID Lahan": id_l,
                            "No. STDB": no_s,
                            "Koordinat": koor,
                            "Luas (m2)": f"{luas:,}",
                            "Var. Utama": v1,
                            "Bebas Def.": "Ya" if is_bebas else "Tidak",
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

