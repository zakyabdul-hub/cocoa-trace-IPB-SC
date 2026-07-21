"""
app.py - Halaman Utama & Autentikasi Ketertelusuran Kakao Berbasis Blockchain
Sistem manajemen rantai pasok kakao dari hulu ke hilir menggunakan Streamlit + Web3.py
Theme: adminHMD Enterprise Admin System
"""

import streamlit as st
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
from style_adminhmd import inject_adminhmd_theme

# ============================================================
# KONFIGURASI HALAMAN STREAMLIT
# ============================================================
st.set_page_config(
    page_title="CacaoTrace | Enterprise Supply Chain Traceability",
    page_icon="🍫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Suntikkan CSS System adminHMD terpusat
inject_adminhmd_theme()

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
# FUNGSI KONEKSI & AUTH
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
    """Login pengguna berdasarkan wallet address."""
    if not st.session_state.ganache_connected:
        return {'success': False, 'error': 'Tidak terhubung ke jaringan Ganache.'}
    
    try:
        checksum_addr = Web3.to_checksum_address(wallet_address)
        role_manager = st.session_state.contracts['RoleManager']
        role = role_manager.functions.getRole(checksum_addr).call()
        
        admin_addr = role_manager.functions.admin().call()
        is_admin = checksum_addr.lower() == admin_addr.lower()
        
        if is_admin and (not role or role == ""):
            role = "Admin"
        
        if not role or role == "":
            return {
                'success': False,
                'error': f'Wallet address ini belum terdaftar di blockchain. Hubungi Admin untuk penugasan peran.'
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
        return {'success': False, 'error': f'Error saat verifikasi: {str(e)}'}

def get_role_badge_class(role: str) -> str:
    """Mengembalikan kelas badge adminHMD berdasarkan role."""
    role_map = {
        'Admin': 'badge-admin',
        'Penangkar': 'badge-penangkar',
        'Petani': 'badge-petani',
        'Pengepul': 'badge-pengepul',
        'Perusahaan': 'badge-perusahaan'
    }
    return role_map.get(role, 'badge-admin')

def get_role_emoji(role: str) -> str:
    """Mengembalikan emoji role."""
    role_emojis = {
        'Admin': '👑',
        'Penangkar': '🌱',
        'Petani': '🌾',
        'Pengepul': '📦',
        'Perusahaan': '🏭',
    }
    return role_emojis.get(role, '👤')

# Auto-connect Ganache
if not st.session_state.ganache_connected:
    connect_to_ganache()


# ============================================================
# SIDEBAR - NAVIGATION & USER FOOTPRINT
# ============================================================
with st.sidebar:
    # Sidebar Header / Brand Box (adminHMD style)
    st.markdown("""
    <div class="sidebar-brand-box">
        <div class="sidebar-brand-icon">🍫</div>
        <div>
            <div style="font-weight: 800; font-size: 1.1rem; color: #ffffff; line-height: 1.2;">CacaoTrace</div>
            <div style="font-size: 0.75rem; color: #9ca3af;">Enterprise Traceability</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Status Ganache
    if st.session_state.ganache_connected:
        st.markdown(f"""
        <div style="padding: 0.5rem 0.8rem; background: rgba(255,255,255,0.05); border-radius: 8px; margin-bottom: 1rem;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span class="admin-badge badge-connected">● Ganache Active</span>
                <span style="font-size: 0.75rem; color: #9ca3af;">#{st.session_state.block_number}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="padding: 0.5rem 0.8rem; background: rgba(239,68,68,0.1); border-radius: 8px; margin-bottom: 1rem;">
            <span class="admin-badge badge-disconnected">● Ganache Disconnected</span>
        </div>
        """, unsafe_allow_html=True)

    # Menampilkan User Card jika sudah login
    if st.session_state.is_logged_in and st.session_state.role:
        badge_cls = get_role_badge_class(st.session_state.role)
        emoji = get_role_emoji(st.session_state.role)
        
        st.markdown(f"""
        <div class="sidebar-user-card">
            <div style="font-size: 0.7rem; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px;">
                Identitas Aktif
            </div>
            <div style="margin-bottom: 8px;">
                <span class="admin-badge {badge_cls}">{emoji} {st.session_state.role}</span>
            </div>
            <div style="font-family: monospace; font-size: 0.72rem; color: #d1d5db; word-break: break-all;">
                {st.session_state.wallet_address}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚪 Keluar (Logout)", key="sidebar_logout_btn", use_container_width=True):
            st.session_state.wallet_address = ''
            st.session_state.private_key = ''
            st.session_state.role = ''
            st.session_state.is_logged_in = False
            st.rerun()

    st.markdown("""
    <div style="text-align: center; font-size: 0.7rem; color: #6b7280; margin-top: 2rem;">
        CacaoTrace v2.1 | adminHMD Theme<br>
        Web3.py & Solidity Smart Contracts
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# RENDER LOGIC: LOGIN PAGE TERPISAH VS DASHBOARD
# ============================================================

if not st.session_state.is_logged_in:
    # ------------------------------------------------------------
    # DEDICATED FULL-SCREEN LOGIN PAGE (adminHMD Auth)
    # ------------------------------------------------------------
    st.markdown("""
    <div class="login-wrapper">
        <div class="login-brand-header">
            <div class="login-brand-logo">🍫</div>
            <h1 class="login-title">Selamat Datang di CacaoTrace</h1>
            <p class="login-subtitle">Masukkan identitas Ethereum Wallet untuk mengakses Sistem Ketertelusuran Kakao</p>
        </div>
    """, unsafe_allow_html=True)
    
    col_l1, col_l2, col_l3 = st.columns([1, 8, 1])
    with col_l2:
        if not st.session_state.ganache_connected:
            st.error("⚠️ Jaringan Ganache (http://127.0.0.1:7545) tidak ditemukan. Mohon jalankan Ganache terlebih dahulu.")
            if st.button("🔄 Hubungkan Ulang Ganache", use_container_width=True):
                connect_to_ganache()
                st.rerun()
        
        wallet_input = st.text_input(
            "Ethereum Wallet Address",
            placeholder="0x...",
            value=st.session_state.wallet_address,
            key="login_wallet_input"
        )
        
        private_key_input = st.text_input(
            "Private Key (Opsional / Penandatangan Transaksi)",
            type="password",
            placeholder="0x...",
            value=st.session_state.private_key,
            key="login_pk_input"
        )
        
        with st.expander("🔖 Pilihan Cepat (Akun Simulasi Ganache)"):
            st.caption("Pilih salah satu peran terdaftar untuk pengisian otomatis:")
            for rname, raddr in SIMULATION_ACCOUNTS.items():
                if st.button(f"{get_role_emoji(rname)} {rname} ({raddr[:8]}...{raddr[-6:]})", key=f"quick_auth_{rname}"):
                    st.session_state.wallet_address = raddr
                    st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔑 Masuk Sistem CacaoTrace", key="login_submit_btn", use_container_width=True):
            if not wallet_input:
                st.warning("Silakan masukkan Wallet Address!")
            else:
                with st.spinner("Memverifikasi otorisasi akun..."):
                    res = login_user(wallet_input, private_key_input)
                    if res['success']:
                        st.session_state.wallet_address = wallet_input
                        st.session_state.private_key = private_key_input
                        st.session_state.role = res['role']
                        st.session_state.is_logged_in = True
                        st.success(f"Berhasil masuk sebagai {res['role']}!")
                        st.rerun()
                    else:
                        st.error(res['error'])
                        
    st.markdown("</div>", unsafe_allow_html=True)

else:
    # ------------------------------------------------------------
    # MAIN DASHBOARD PAGE (Setelah Login)
    # ------------------------------------------------------------
    
    # Top Navbar Header (adminHMD)
    st.markdown(f"""
    <div class="admin-topbar">
        <div class="admin-topbar-title">
            <span style="font-size: 1.5rem;">🍫</span> Dashboard Rantai Pasok Kakao
        </div>
        <div class="admin-topbar-meta">
            <span class="admin-badge {get_role_badge_class(st.session_state.role)}">
                {get_role_emoji(st.session_state.role)} {st.session_state.role}
            </span>
            <span class="admin-badge badge-connected">Block #{st.session_state.block_number}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Header Banner Page
    st.markdown("""
    <div class="admin-page-header">
        <h1>Sistem Ketertelusuran Rantai Pasok Kakao</h1>
        <p>Manajemen dan pencatatan rantai pasok kakao berbasis Smart Contracts Solidity & EVM Ganache (Hulu ke Hilir)</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Metric Widgets Grid
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown("""
        <div class="metric-widget">
            <div class="metric-icon-box metric-icon-blue">🌱</div>
            <div>
                <div class="metric-val">F1 — F6</div>
                <div class="metric-lbl">Modul Rantai Pasok</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="metric-widget">
            <div class="metric-icon-box metric-icon-green">⛓️</div>
            <div>
                <div class="metric-val">#{st.session_state.block_number}</div>
                <div class="metric-lbl">Block Terkini</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="metric-widget">
            <div class="metric-icon-box metric-icon-amber">👤</div>
            <div>
                <div class="metric-val">{st.session_state.role}</div>
                <div class="metric-lbl">Peran Sesi Aktif</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        st.markdown("""
        <div class="metric-widget">
            <div class="metric-icon-box metric-icon-purple">📝</div>
            <div>
                <div class="metric-val">3 Contract</div>
                <div class="metric-lbl">Solidity Active</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Feature Cards Grid
    st.markdown("""
    <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 1.3rem; font-weight: 700; color: #1f2937; margin-bottom: 16px;">
        📱 Fitur Ketertelusuran
    </div>
    """, unsafe_allow_html=True)
    
    features = [
        {
            "icon": "🌱",
            "title": "F1 — Registrasi Varietas Benih",
            "desc": "Daftarkan aset varietas benih kakao beserta SK Pelepasan dan masa edar.",
            "role": "Penangkar",
            "page": "01_F1_Registrasi_Varietas",
            "badge": "badge-penangkar"
        },
        {
            "icon": "🗺️",
            "title": "F2 — Registrasi Lahan",
            "desc": "Registrasi lahan pertanian dengan validasi geospasial otomatis bebas kawasan hutan.",
            "role": "Petani",
            "page": "02_F2_Registrasi_Lahan",
            "badge": "badge-petani"
        },
        {
            "icon": "🌾",
            "title": "F3 — Pencatatan Panen",
            "desc": "Catat hasil panen harian dari lahan terdaftar, fermentasi, dan kuantitas.",
            "role": "Petani",
            "page": "03_F3_Pencatatan_Panen",
            "badge": "badge-petani"
        },
        {
            "icon": "📦",
            "title": "F4 — Agregasi Pengepul",
            "desc": "Gabungkan beberapa batch panen menjadi batch pengepul baru (Level 0 s.d 4).",
            "role": "Pengepul",
            "page": "04_F4_Agregasi_Pengepul",
            "badge": "badge-pengepul"
        },
        {
            "icon": "🏭",
            "title": "F5 — Agregasi Perusahaan",
            "desc": "Proses agregasi perusahaan berjenjang (GudangKab L5 → Pelabuhan L6 → Pusat L7).",
            "role": "Perusahaan",
            "page": "05_F5_Agregasi_Perusahaan",
            "badge": "badge-perusahaan"
        },
        {
            "icon": "🔍",
            "title": "F6 — Riwayat Ketertelusuran",
            "desc": "Lacak riwayat lengkap dari hulu ke hilir secara rekursif dan export PDF.",
            "role": "Semua Peran",
            "page": "06_F6_Riwayat_Ketertelusuran",
            "badge": "badge-admin"
        },
    ]
    
    col_pairs = [(0, 1), (2, 3), (4, 5)]
    for pair in col_pairs:
        cols = st.columns(2)
        for i, col_idx in enumerate(pair):
            if col_idx < len(features):
                feat = features[col_idx]
                with cols[i]:
                    st.markdown(f"""
                    <div class="admin-card">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px;">
                            <span style="font-size: 2rem;">{feat['icon']}</span>
                            <span class="admin-badge {feat['badge']}">Aktor: {feat['role']}</span>
                        </div>
                        <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 1.1rem; font-weight: 700; color: #1f2937; margin-bottom: 6px;">
                            {feat['title']}
                        </div>
                        <div style="font-size: 0.88rem; color: #6b7280; line-height: 1.5; margin-bottom: 16px;">
                            {feat['desc']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.page_link(f"pages/{feat['page']}.py", label=f"→ Buka {feat['title']}", use_container_width=True)
                    st.markdown("<br>", unsafe_allow_html=True)

    # Section Informasi Smart Contract
    st.markdown("""
    <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 1.2rem; font-weight: 700; color: #1f2937; margin-bottom: 14px;">
        🔗 Informasional Smart Contract Solidity
    </div>
    """, unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    contracts_meta = [
        ("🔐 RoleManager", CONTRACT_ADDRESSES['RoleManager'], "Manajemen Peran & Otorisasi"),
        ("📋 MasterData", CONTRACT_ADDRESSES['MasterData'], "Registrasi Varietas & Lahan"),
        ("📊 Traceability", CONTRACT_ADDRESSES['Traceability'], "Batch Panen & Agregasi Supply Chain"),
    ]
    for col, (cname, caddr, cdesc) in zip([c1, c2, c3], contracts_meta):
        with col:
            st.markdown(f"""
            <div class="admin-card">
                <div style="font-weight: 700; color: #2563eb; margin-bottom: 6px;">{cname}</div>
                <div style="font-family: monospace; font-size: 0.72rem; color: #6b7280; word-break: break-all; margin-bottom: 8px;">
                    {caddr}
                </div>
                <div style="font-size: 0.82rem; color: #4b5563;">{cdesc}</div>
            </div>
            """, unsafe_allow_html=True)
