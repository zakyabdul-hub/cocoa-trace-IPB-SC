"""
app.py - Halaman Utama Aplikasi Ketertelusuran Kakao Berbasis Blockchain
Sistem manajemen rantai pasok kakao dari hulu ke hilir menggunakan Streamlit + Web3.py
"""

# pyrefly: ignore [missing-import]
import streamlit as st
# pyrefly: ignore [missing-import]
from web3 import Web3
import sys
import os
from datetime import datetime

# Tambahkan root directory ke path
sys.path.insert(0, os.path.dirname(__file__))
from config import (
    GANACHE_RPC, CONTRACT_ADDRESSES, SIMULATION_ACCOUNTS, 
    VALID_ROLES, get_web3, get_contracts
)

# ============================================================
# KONFIGURASI HALAMAN STREAMLIT
# ============================================================
st.set_page_config(
    page_title="CacaoTrace | Sistem Ketertelusuran Kakao",
    page_icon="🍫",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "**CacaoTrace** - Sistem Ketertelusuran Rantai Pasok Kakao Berbasis Blockchain"
    }
)

# ============================================================
# CUSTOM CSS PREMIUM
# ============================================================
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');
    
    /* Root Variables */
    :root {
        --primary: #6C3D14;
        --primary-light: #8B5E34;
        --primary-dark: #4A2A0C;
        --accent: #D4A853;
        --accent-light: #F0C878;
        --success: #22C55E;
        --danger: #EF4444;
        --warning: #F59E0B;
        --bg-dark: #0F0A06;
        --bg-card: #1A1108;
        --bg-glass: rgba(108, 61, 20, 0.08);
        --border: rgba(212, 168, 83, 0.2);
        --text-primary: #F5F0E8;
        --text-secondary: #B8A890;
        --text-muted: #7A6A58;
    }
    
    /* Global Styles */
    .stApp {
        background: linear-gradient(135deg, #0F0A06 0%, #1A0F05 50%, #0D0804 100%) !important;
        font-family: 'Inter', sans-serif !important;
        color: var(--text-primary) !important;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1A0F05 0%, #0F0A06 100%) !important;
        border-right: 1px solid var(--border) !important;
    }
    
    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: var(--accent) !important;
    }
    
    /* Main Header */
    .main-header {
        background: linear-gradient(135deg, rgba(108,61,20,0.3) 0%, rgba(212,168,83,0.15) 100%);
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: 40px;
        margin-bottom: 30px;
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(10px);
    }
    
    .main-header::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -20%;
        width: 400px;
        height: 400px;
        background: radial-gradient(circle, rgba(212,168,83,0.08) 0%, transparent 70%);
        border-radius: 50%;
        animation: pulse 4s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 0.5; transform: scale(1); }
        50% { opacity: 1; transform: scale(1.05); }
    }
    
    .main-title {
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 2.8rem !important;
        font-weight: 700 !important;
        background: linear-gradient(135deg, #F5F0E8 0%, #D4A853 50%, #F0C878 100%) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        margin-bottom: 8px !important;
    }
    
    .main-subtitle {
        color: var(--text-secondary);
        font-size: 1rem;
        font-weight: 400;
    }
    
    /* Status Cards */
    .status-card {
        background: var(--bg-glass);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 20px;
        margin: 8px 0;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }
    
    .status-card:hover {
        border-color: rgba(212, 168, 83, 0.4);
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(212,168,83,0.1);
    }
    
    .status-connected {
        border-left: 4px solid var(--success) !important;
    }
    
    .status-disconnected {
        border-left: 4px solid var(--danger) !important;
    }
    
    /* Role Badge */
    .role-badge {
        display: inline-block;
        padding: 4px 14px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }
    
    .role-admin { background: linear-gradient(135deg, #7C3AED, #A855F7); color: white; }
    .role-penangkar { background: linear-gradient(135deg, #059669, #10B981); color: white; }
    .role-petani { background: linear-gradient(135deg, #0284C7, #38BDF8); color: white; }
    .role-pengepul { background: linear-gradient(135deg, #D97706, #F59E0B); color: white; }
    .role-perusahaan { background: linear-gradient(135deg, #DC2626, #EF4444); color: white; }
    .role-unknown { background: linear-gradient(135deg, #4B5563, #6B7280); color: white; }
    
    /* Feature Cards */
    .feature-card {
        background: linear-gradient(135deg, rgba(26,17,8,0.8) 0%, rgba(26,17,8,0.4) 100%);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 24px;
        margin: 8px 0;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
        cursor: pointer;
    }
    
    .feature-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, var(--primary), var(--accent));
        border-radius: 16px 16px 0 0;
    }
    
    .feature-card:hover {
        border-color: rgba(212, 168, 83, 0.5);
        transform: translateY(-3px);
        box-shadow: 0 12px 40px rgba(0,0,0,0.3);
    }
    
    .feature-icon {
        font-size: 2rem;
        margin-bottom: 12px;
    }
    
    .feature-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--accent);
        margin-bottom: 6px;
    }
    
    .feature-desc {
        font-size: 0.85rem;
        color: var(--text-secondary);
        line-height: 1.5;
    }
    
    .feature-role {
        margin-top: 12px;
        font-size: 0.7rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    
    /* Blockchain Info Box */
    .blockchain-info {
        background: linear-gradient(135deg, rgba(34,197,94,0.05) 0%, rgba(34,197,94,0.02) 100%);
        border: 1px solid rgba(34,197,94,0.2);
        border-radius: 12px;
        padding: 16px;
        font-family: 'Space Mono', monospace;
        font-size: 0.75rem;
    }
    
    /* Wallet Address Display */
    .wallet-display {
        background: rgba(0,0,0,0.3);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 10px 14px;
        font-family: monospace;
        font-size: 0.8rem;
        color: var(--accent-light);
        word-break: break-all;
        margin: 8px 0;
    }
    
    /* Divider */
    .custom-divider {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--border), transparent);
        margin: 24px 0;
    }
    
    /* Alert Boxes Custom */
    .alert-success {
        background: linear-gradient(135deg, rgba(34,197,94,0.1), rgba(34,197,94,0.05));
        border: 1px solid rgba(34,197,94,0.3);
        border-radius: 12px;
        padding: 16px;
        color: #4ADE80;
    }
    
    .alert-danger {
        background: linear-gradient(135deg, rgba(239,68,68,0.1), rgba(239,68,68,0.05));
        border: 1px solid rgba(239,68,68,0.3);
        border-radius: 12px;
        padding: 16px;
        color: #FCA5A5;
    }
    
    .alert-warning {
        background: linear-gradient(135deg, rgba(245,158,11,0.1), rgba(245,158,11,0.05));
        border: 1px solid rgba(245,158,11,0.3);
        border-radius: 12px;
        padding: 16px;
        color: #FCD34D;
    }
    
    /* Streamlit element overrides */
    .stTextInput > div > div > input {
        background: rgba(26,17,8,0.8) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        color: var(--text-primary) !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 2px rgba(212,168,83,0.15) !important;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, var(--primary), var(--primary-light)) !important;
        color: var(--accent-light) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        letter-spacing: 0.02em !important;
        transition: all 0.3s ease !important;
        padding: 0.5rem 1.5rem !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, var(--primary-light), var(--accent)) !important;
        color: var(--bg-dark) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(212,168,83,0.3) !important;
    }
    
    .stSelectbox > div > div {
        background: rgba(26,17,8,0.8) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
    }
    
    .stNumberInput > div > div > input {
        background: rgba(26,17,8,0.8) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        color: var(--text-primary) !important;
    }
    
    /* Metrics */
    [data-testid="metric-container"] {
        background: var(--bg-glass) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        padding: 16px !important;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(26,17,8,0.5) !important;
        border-radius: 12px !important;
        padding: 4px !important;
        gap: 4px !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px !important;
        color: var(--text-secondary) !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, var(--primary), var(--primary-light)) !important;
        color: var(--accent-light) !important;
    }
    
    /* Scrollbar custom */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: var(--bg-dark); }
    ::-webkit-scrollbar-thumb { background: var(--primary); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--accent); }
    
    /* Hide Streamlit branding */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# INISIALISASI SESSION STATE
# ============================================================
def init_session_state():
    """Inisialisasi semua session state yang diperlukan."""
    defaults = {
        'wallet_address': '',
        'private_key': '',
        'role': '',
        'is_connected': False,
        'is_logged_in': False,
        'w3': None,
        'contracts': None,
        'ganache_connected': False,
        'block_number': 0,
        'network_id': 0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session_state()


# ============================================================
# FUNGSI KONEKSI
# ============================================================
def connect_to_ganache():
    """Menghubungkan ke Ganache dan menyimpan ke session state."""
    try:
        w3 = get_web3()
        if w3.is_connected():
            contracts = get_contracts(w3)
            st.session_state.w3 = w3
            st.session_state.contracts = contracts
            st.session_state.ganache_connected = True
            st.session_state.block_number = w3.eth.block_number
            st.session_state.network_id = w3.eth.chain_id
            return True, "✅ Terhubung ke Ganache"
        else:
            st.session_state.ganache_connected = False
            return False, "❌ Gagal terhubung ke Ganache"
    except Exception as e:
        st.session_state.ganache_connected = False
        return False, f"❌ Error: {str(e)}"


def login_user(wallet_address: str, private_key: str) -> dict:
    """
    Login pengguna berdasarkan wallet address.
    Memanggil RoleManager.getRole() untuk mendapatkan peran.
    """
    if not st.session_state.ganache_connected:
        return {'success': False, 'error': 'Tidak terhubung ke Ganache.'}
    
    try:
        # Validasi format wallet address
        checksum_addr = Web3.to_checksum_address(wallet_address)
        
        # Panggil getRole dari RoleManager
        role_manager = st.session_state.contracts['RoleManager']
        role = role_manager.functions.getRole(checksum_addr).call()
        
        # Verifikasi apakah ini adalah admin
        admin_addr = role_manager.functions.admin().call()
        is_admin = checksum_addr.lower() == admin_addr.lower()
        
        if is_admin and (not role or role == ""):
            role = "Admin"
        
        if not role or role == "":
            return {
                'success': False,
                'error': f'Wallet address ini belum memiliki peran. Hubungi Admin untuk mendapatkan akses.'
            }
        
        return {
            'success': True,
            'role': role,
            'address': checksum_addr,
            'is_admin': is_admin,
        }
    except ValueError as e:
        return {'success': False, 'error': f'Format wallet address tidak valid: {str(e)}'}
    except Exception as e:
        return {'success': False, 'error': f'Error saat login: {str(e)}'}


def get_role_color(role: str) -> str:
    """Mengembalikan kelas CSS untuk role badge."""
    role_colors = {
        'Admin': 'role-admin',
        'Penangkar': 'role-penangkar',
        'Petani': 'role-petani',
        'Pengepul': 'role-pengepul',
        'Perusahaan': 'role-perusahaan',
    }
    return role_colors.get(role, 'role-unknown')


def get_role_emoji(role: str) -> str:
    """Mengembalikan emoji untuk setiap role."""
    role_emojis = {
        'Admin': '👑',
        'Penangkar': '🌱',
        'Petani': '🌾',
        'Pengepul': '📦',
        'Perusahaan': '🏭',
    }
    return role_emojis.get(role, '👤')


# ============================================================
# SIDEBAR - LOGIN PANEL
# ============================================================
with st.sidebar:
    # Logo & Branding
    st.markdown("""
    <div style="text-align: center; padding: 20px 0 10px 0;">
        <div style="font-size: 3.5rem; margin-bottom: 8px;">🍫</div>
        <div style="font-family: 'Space Grotesk', sans-serif; font-size: 1.4rem; font-weight: 700; 
             background: linear-gradient(135deg, #F5F0E8, #D4A853); -webkit-background-clip: text; 
             -webkit-text-fill-color: transparent; background-clip: text;">
            CacaoTrace
        </div>
        <div style="font-size: 0.7rem; color: #7A6A58; letter-spacing: 0.15em; text-transform: uppercase; margin-top: 4px;">
            Blockchain Traceability
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<hr style="border: none; height: 1px; background: linear-gradient(90deg, transparent, rgba(212,168,83,0.3), transparent);">', unsafe_allow_html=True)
    
    # Status Koneksi Ganache
    col_conn1, col_conn2 = st.columns([3, 1])
    with col_conn1:
        st.markdown("**🔗 Koneksi Ganache**")
    with col_conn2:
        if st.button("🔄", key="btn_reconnect", help="Refresh koneksi ke Ganache"):
            success, msg = connect_to_ganache()
    
    # Auto-connect saat pertama kali
    if not st.session_state.ganache_connected:
        success, msg = connect_to_ganache()
    
    if st.session_state.ganache_connected:
        st.markdown("""
        <div class="status-card status-connected">
            <span style="color: #22C55E; font-size: 0.8rem;">🟢 Terhubung ke Ganache</span><br>
            <span style="color: #7A6A58; font-size: 0.7rem;">http://127.0.0.1:7545</span>
        </div>
        """, unsafe_allow_html=True)
        
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            st.metric("Block", f"#{st.session_state.block_number}", label_visibility="collapsed")
        with col_b2:
            st.metric("Chain ID", st.session_state.network_id, label_visibility="collapsed")
    else:
        st.markdown("""
        <div class="status-card status-disconnected">
            <span style="color: #EF4444; font-size: 0.8rem;">🔴 Ganache Tidak Tersedia</span><br>
            <span style="color: #7A6A58; font-size: 0.7rem;">Pastikan Ganache berjalan di port 7545</span>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('<hr style="border: none; height: 1px; background: linear-gradient(90deg, transparent, rgba(212,168,83,0.3), transparent); margin: 16px 0;">', unsafe_allow_html=True)
    
    # Panel Login
    st.markdown("**🔐 Login Identitas**")
    
    wallet_input = st.text_input(
        "Wallet Address",
        placeholder="0x...",
        value=st.session_state.wallet_address,
        key="wallet_input",
        help="Masukkan Ethereum wallet address (dari Ganache)"
    )
    
    private_key_input = st.text_input(
        "Private Key",
        type="password",
        placeholder="0x...",
        value=st.session_state.private_key,
        key="pk_input",
        help="Private key untuk menandatangani transaksi (hanya untuk PoC lokal)"
    )
    
    # Quick select akun simulasi
    with st.expander("🔖 Akun Simulasi Cepat"):
        st.caption("Klik untuk mengisi otomatis (Private Key harus diisi manual dari Ganache)")
        for role_name, addr in SIMULATION_ACCOUNTS.items():
            if st.button(f"{get_role_emoji(role_name)} {role_name}: ...{addr[-6:]}", key=f"quick_{role_name}"):
                st.session_state.wallet_address = addr
                st.rerun()
    
    # Tombol Login
    if st.button("🚀 Login / Verifikasi Peran", key="btn_login", use_container_width=True):
        if not wallet_input:
            st.error("Masukkan wallet address terlebih dahulu!")
        elif not st.session_state.ganache_connected:
            st.error("Koneksi ke Ganache gagal!")
        else:
            with st.spinner("Memverifikasi identitas..."):
                result = login_user(wallet_input, private_key_input)
                
                if result['success']:
                    st.session_state.wallet_address = wallet_input
                    st.session_state.private_key = private_key_input
                    st.session_state.role = result['role']
                    st.session_state.is_logged_in = True
                    st.success(f"Login berhasil sebagai **{result['role']}**!")
                    st.rerun()
                else:
                    st.error(result['error'])
    
    # Status Login
    if st.session_state.is_logged_in and st.session_state.role:
        st.markdown('<hr style="border: none; height: 1px; background: linear-gradient(90deg, transparent, rgba(212,168,83,0.3), transparent); margin: 16px 0;">', unsafe_allow_html=True)
        
        role_class = get_role_color(st.session_state.role)
        role_emoji = get_role_emoji(st.session_state.role)
        
        st.markdown(f"""
        <div style="text-align: center; padding: 10px 0;">
            <div style="font-size: 0.7rem; color: #7A6A58; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 8px;">
                Sesi Aktif
            </div>
            <span class="role-badge {role_class}">{role_emoji} {st.session_state.role}</span>
        </div>
        <div class="wallet-display">{st.session_state.wallet_address}</div>
        """, unsafe_allow_html=True)
        
        if st.button("🚪 Logout", key="btn_logout", use_container_width=True):
            st.session_state.wallet_address = ''
            st.session_state.private_key = ''
            st.session_state.role = ''
            st.session_state.is_logged_in = False
            st.rerun()
    
    st.markdown('<br>', unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align: center; font-size: 0.65rem; color: #4A3A2A;">
        CacaoTrace v2.1 | PoC Blockchain<br>
        🔗 Solidity ^0.8.0 | 🐍 Web3.py 6.x
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# KONTEN UTAMA - DASHBOARD
# ============================================================

# Header Utama
st.markdown("""
<div class="main-header">
    <div class="main-title">🍫 CacaoTrace</div>
    <div class="main-subtitle">
        Sistem Ketertelusuran Rantai Pasok Kakao Berbasis Blockchain
        <br><span style="color: #7A6A58; font-size: 0.85rem;">
            Proof of Concept | Ganache Local EVM | Solidity Smart Contracts
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

# Status Bar
col_s1, col_s2, col_s3, col_s4 = st.columns(4)

with col_s1:
    if st.session_state.ganache_connected:
        st.metric(
            label="🔗 Status Jaringan",
            value="Terhubung",
            delta="Ganache Local",
            delta_color="normal"
        )
    else:
        st.metric(label="🔗 Status Jaringan", value="Terputus", delta="Ganache Offline")

with col_s2:
    st.metric(
        label="📦 Block Terkini",
        value=f"#{st.session_state.block_number}" if st.session_state.ganache_connected else "N/A"
    )

with col_s3:
    st.metric(
        label="👤 Role Aktif",
        value=f"{get_role_emoji(st.session_state.role)} {st.session_state.role}" if st.session_state.role else "Belum Login"
    )

with col_s4:
    st.metric(
        label="📋 Kontrak Aktif",
        value="3 Kontrak" if st.session_state.ganache_connected else "0 Kontrak"
    )

st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

# Grid Fitur
st.markdown("""
<div style="font-family: 'Space Grotesk', sans-serif; font-size: 1.3rem; font-weight: 600; 
     color: #D4A853; margin-bottom: 20px;">
    📱 Fitur Sistem
</div>
""", unsafe_allow_html=True)

features = [
    {
        "icon": "🌱",
        "title": "F1 — Registrasi Varietas Benih",
        "desc": "Daftarkan aset varietas benih kakao beserta SK Pelepasan dan masa edar. Data tersimpan permanen di blockchain.",
        "role": "Penangkar",
        "page": "01_F1_Registrasi_Varietas",
        "color": "#059669",
    },
    {
        "icon": "🗺️",
        "title": "F2 — Registrasi Lahan",
        "desc": "Registrasi lahan pertanian dengan validasi geospasial otomatis untuk memastikan bebas kawasan hutan.",
        "role": "Petani",
        "page": "02_F2_Registrasi_Lahan",
        "color": "#0284C7",
    },
    {
        "icon": "🌾",
        "title": "F3 — Pencatatan Panen",
        "desc": "Catat hasil panen harian dari lahan terdaftar, termasuk status fermentasi dan kuantitas.",
        "role": "Petani",
        "page": "03_F3_Pencatatan_Panen",
        "color": "#0EA5E9",
    },
    {
        "icon": "📦",
        "title": "F4 — Agregasi Pengepul",
        "desc": "Gabungkan beberapa batch panen dari berbagai petani menjadi satu batch pengepul dengan chaining validation.",
        "role": "Pengepul",
        "page": "04_F4_Agregasi_Pengepul",
        "color": "#D97706",
    },
    {
        "icon": "🏭",
        "title": "F5 — Agregasi Perusahaan",
        "desc": "Proses agregasi berjenjang sesuai hierarki: GudangKab → GudangPelabuhan → Pusat.",
        "role": "Perusahaan",
        "page": "05_F5_Agregasi_Perusahaan",
        "color": "#DC2626",
    },
    {
        "icon": "🔍",
        "title": "F6 — Riwayat Ketertelusuran",
        "desc": "Lacak riwayat lengkap dari hulu ke hilir secara rekursif. Export laporan PDF dengan satu klik.",
        "role": "Semua Pengguna",
        "page": "06_F6_Riwayat_Ketertelusuran",
        "color": "#7C3AED",
    },
]

# CSS tambahan: styling tombol navigasi st.page_link agar premium
st.markdown("""
<style>
/* Override st.page_link button di dashboard */
div[data-testid="stPageLink"] > a {
    background: linear-gradient(135deg, rgba(108,61,20,0.4), rgba(212,168,83,0.15)) !important;
    border: 1px solid rgba(212,168,83,0.35) !important;
    border-radius: 10px !important;
    color: var(--accent-light, #F0C878) !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    padding: 10px 16px !important;
    transition: all 0.3s ease !important;
    text-decoration: none !important;
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
    width: 100% !important;
    margin-top: 4px !important;
}
div[data-testid="stPageLink"] > a:hover {
    background: linear-gradient(135deg, rgba(212,168,83,0.25), rgba(212,168,83,0.12)) !important;
    border-color: rgba(212,168,83,0.7) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(212,168,83,0.2) !important;
    color: #F0C878 !important;
}
div[data-testid="stPageLink"] > a > p {
    color: inherit !important;
    font-weight: 600 !important;
    margin: 0 !important;
}
</style>
""", unsafe_allow_html=True)

# Tampilkan feature cards dalam 2 kolom — setiap card punya tombol navigasi
col_pairs = [(0, 1), (2, 3), (4, 5)]
for pair in col_pairs:
    cols = st.columns(2)
    for i, col_idx in enumerate(pair):
        if col_idx < len(features):
            feat = features[col_idx]
            with cols[i]:
                # Visual card (dekoratif)
                st.markdown(f"""
                <div class="feature-card" style="margin-bottom: 0px; border-bottom-left-radius: 0; border-bottom-right-radius: 0;">
                    <div class="feature-icon">{feat['icon']}</div>
                    <div class="feature-title" style="color: {feat['color']};">{feat['title']}</div>
                    <div class="feature-desc">{feat['desc']}</div>
                    <div class="feature-role">
                        <span style="color: {feat['color']};">●</span> Aktor: {feat['role']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Tombol navigasi nyata — bisa diklik
                st.page_link(
                    f"pages/{feat['page']}.py",
                    label=f"→ Buka {feat['title']}",
                    use_container_width=True,
                )
                st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

# Informasi Kontrak
st.markdown("""
<div style="font-family: 'Space Grotesk', sans-serif; font-size: 1.1rem; font-weight: 600; 
     color: #D4A853; margin-bottom: 16px;">
    🔗 Informasi Smart Contract
</div>
""", unsafe_allow_html=True)

col_c1, col_c2, col_c3 = st.columns(3)
contract_info = [
    ("🔐 RoleManager", CONTRACT_ADDRESSES['RoleManager'], "Manajemen peran & otorisasi pengguna"),
    ("📋 MasterData", CONTRACT_ADDRESSES['MasterData'], "Registrasi varietas benih dan lahan"),
    ("📊 Traceability", CONTRACT_ADDRESSES['Traceability'], "Batch panen dan agregasi rantai pasok"),
]

for col, (name, addr, desc) in zip([col_c1, col_c2, col_c3], contract_info):
    with col:
        is_connected = st.session_state.ganache_connected
        status_color = "#22C55E" if is_connected else "#EF4444"
        status_text = "Aktif" if is_connected else "Tidak Tersedia"
        
        st.markdown(f"""
        <div class="status-card">
            <div style="font-size: 0.9rem; font-weight: 600; color: #D4A853; margin-bottom: 8px;">{name}</div>
            <div style="font-size: 0.65rem; font-family: monospace; color: #B8A890; word-break: break-all; margin-bottom: 8px;">
                {addr[:10]}...{addr[-8:]}
            </div>
            <div style="font-size: 0.75rem; color: #7A6A58;">{desc}</div>
            <div style="margin-top: 10px; font-size: 0.7rem;">
                <span style="color: {status_color};">● {status_text}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

# Catatan untuk pengguna baru
if not st.session_state.is_logged_in:
    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
    st.info("""
    **👋 Cara Memulai:**
    1. Pastikan **Ganache** berjalan di `http://127.0.0.1:7545`
    2. Masukkan **Wallet Address** dan **Private Key** di sidebar kiri
    3. Klik **Login / Verifikasi Peran** untuk memulai sesi
    4. Navigasi ke halaman fitur yang sesuai dengan peran Anda
    """)

# Footer
st.markdown("""
<div style="text-align: center; padding: 30px 0 10px; color: #4A3A2A; font-size: 0.75rem;">
    <span style="color: #7A6A58;">CacaoTrace</span> — Sistem Ketertelusuran Rantai Pasok Kakao Berbasis Blockchain<br>
    Proof of Concept | Dibangun dengan Streamlit + Web3.py + Solidity
</div>
""", unsafe_allow_html=True)
