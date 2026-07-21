"""
00_Admin_Panel.py
Panel Admin: Manajemen Peran Pengguna
Aktor: Admin
Smart Contract: RoleManager.assignRole(), deactivateRole(), getRole(), getRoleData()
Theme: adminHMD Enterprise Admin System
"""

import streamlit as st
import sys
import os
from datetime import datetime

# Path setup
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import build_transaction, VALID_ROLES, SIMULATION_ACCOUNTS
from style_adminhmd import inject_adminhmd_theme

# Page Configuration
st.set_page_config(
    page_title="Admin Panel | CacaoTrace",
    page_icon="👑",
    layout="wide"
)

inject_adminhmd_theme()

# Auth Check Guard
def check_auth():
    if not st.session_state.get('is_logged_in'):
        st.warning("⚠️ Silakan login terlebih dahulu.")
        st.page_link("app.py", label="← Kembali ke Halaman Login", icon="🔑")
        return False
    if st.session_state.get('role') != "Admin":
        st.error("🚫 Akses Ditolak! Halaman ini khusus untuk Admin.")
        st.page_link("app.py", label="← Kembali ke Dashboard Utama", icon="🏠")
        return False
    return True

if not check_auth():
    st.stop()

# Helper Role Color
def get_role_badge(role: str) -> str:
    role_map = {
        'Admin': 'badge-admin',
        'Penangkar': 'badge-penangkar',
        'Petani': 'badge-petani',
        'Pengepul': 'badge-pengepul',
        'Perusahaan': 'badge-perusahaan'
    }
    return role_map.get(role, 'badge-admin')

# Top Navbar Header
st.markdown(f"""
<div class="admin-topbar">
    <div class="admin-topbar-title">
        <span style="font-size: 1.5rem;">👑</span> Panel Administrasi — Manajemen Peran
    </div>
    <div class="admin-topbar-meta">
        <span class="admin-badge badge-admin">RoleManager Contract</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Page Header
st.markdown("""
<div class="admin-page-header">
    <h1>Manajemen Otorisasi & Peran Pengguna</h1>
    <p>Penugasan dan penonaktifan peran pengguna dalam jaringan rantai pasok kakao berbasis Smart Contract RoleManager.</p>
</div>
""", unsafe_allow_html=True)

# Layout Columns
col_assign, col_info = st.columns([3, 2], gap="large")

with col_assign:
    # Card Assign Role
    st.markdown("""
    <div class="admin-card">
        <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 1.1rem; font-weight: 700; color: #1f2937; margin-bottom: 14px;">
            ➕ Assign Peran ke Pengguna Baru
        </div>
        <div style="font-size: 0.85rem; color: #6b7280; margin-bottom: 16px;">
            ℹ️ Pengguna yang sudah memiliki peran aktif harus dinonaktifkan terlebih dahulu jika ingin berganti peran. Riwayat tetap tersimpan di blockchain.
        </div>
    """, unsafe_allow_html=True)

    with st.form("form_assign_role"):
        target_address = st.text_input(
            "Wallet Address Target *",
            placeholder="0x...",
            help="Wallet address pengguna yang akan diberi peran"
        )

        selected_role = st.selectbox(
            "Pilih Peran *",
            options=["Penangkar", "Petani", "Pengepul", "Perusahaan"],
            help="Pilih peran yang akan diberikan"
        )

        submitted_assign = st.form_submit_button("👑 Assign Peran Pengguna", use_container_width=True)

        if submitted_assign:
            if not target_address.strip():
                st.error("❌ Wallet Address Target wajib diisi!")
            elif not st.session_state.get('private_key'):
                st.error("❌ Private Key Admin belum diinput!")
            else:
                from web3 import Web3
                try:
                    checksum = Web3.to_checksum_address(target_address.strip())
                except Exception:
                    st.error("❌ Format wallet address tidak valid!")
                    st.stop()

                with st.spinner(f"⏳ Mengirim transaksi assignRole ({selected_role})..."):
                    w3 = st.session_state.w3
                    contracts = st.session_state.contracts
                    role_manager = contracts['RoleManager']

                    try:
                        role_data = role_manager.functions.getRoleData(checksum).call()
                        is_active = role_data[1]
                        if is_active:
                            st.error("❌ Wallet address ini sudah memiliki peran aktif!")
                            st.stop()
                    except Exception:
                        pass

                    contract_func = role_manager.functions.assignRole(checksum, selected_role)
                    result = build_transaction(
                        w3, contract_func,
                        st.session_state.wallet_address,
                        st.session_state.private_key
                    )

                    if result['success']:
                        st.success(f"✅ Peran {selected_role} berhasil di-assign ke {checksum[:12]}...")
                    else:
                        st.error(f"❌ Gagal: {result['error']}")

    st.markdown("</div>", unsafe_allow_html=True)

    # Card Deactivate Role
    st.markdown("""
    <div class="admin-card">
        <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 1.1rem; font-weight: 700; color: #dc2626; margin-bottom: 10px;">
            🔒 Nonaktifkan Peran Pengguna
        </div>
        <div style="font-size: 0.85rem; color: #6b7280; margin-bottom: 16px;">
            ⚠️ Peran tidak akan dihapus dari blockchain (immutable). Status akan diubah menjadi <strong>isActive = false</strong>.
        </div>
    """, unsafe_allow_html=True)

    with st.form("form_deactivate_role"):
        remove_address = st.text_input(
            "Wallet Address Target *",
            placeholder="0x...",
            key="rm_addr"
        )

        submitted_remove = st.form_submit_button(
            "🔒 Nonaktifkan Peran",
            use_container_width=True,
        )

        if submitted_remove:
            if not remove_address.strip():
                st.error("❌ Wallet Address wajib diisi!")
            elif not st.session_state.get('private_key'):
                st.error("❌ Private Key Admin belum diinput!")
            else:
                from web3 import Web3
                try:
                    checksum = Web3.to_checksum_address(remove_address.strip())
                except Exception:
                    st.error("❌ Format wallet address tidak valid!")
                    st.stop()

                with st.spinner("⏳ Menonaktifkan peran pengguna..."):
                    w3 = st.session_state.w3
                    contracts = st.session_state.contracts
                    role_manager = contracts['RoleManager']

                    contract_func = role_manager.functions.deactivateRole(checksum)
                    result = build_transaction(
                        w3, contract_func,
                        st.session_state.wallet_address,
                        st.session_state.private_key
                    )

                    if result['success']:
                        st.success(f"✅ Peran dari {checksum[:12]}... berhasil dinonaktifkan!")
                    else:
                        st.error(f"❌ Gagal: {result['error']}")

    st.markdown("</div>", unsafe_allow_html=True)

with col_info:
    # Card Check Status
    st.markdown("""
    <div class="admin-card">
        <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 1.05rem; font-weight: 700; color: #1f2937; margin-bottom: 14px;">
            🔍 Cek Status Peran On-Chain
        </div>
    """, unsafe_allow_html=True)

    check_addr = st.text_input("Wallet Address", placeholder="0x...", key="check_role_addr")

    if st.button("🔍 Cek Peran", key="btn_check_role", use_container_width=True):
        if check_addr.strip() and st.session_state.get('ganache_connected'):
            from web3 import Web3
            try:
                checksum = Web3.to_checksum_address(check_addr.strip())
                contracts = st.session_state.contracts
                role_manager = contracts['RoleManager']

                role_data = role_manager.functions.getRoleData(checksum).call()
                role, is_active, assigned_at, deactivated_at = role_data

                display_role = role if role else "(Tidak Ada Peran)"
                badge_class = get_role_badge(role)
                status_html = '<span class="admin-badge badge-connected">● AKTIF</span>' if is_active else '<span class="admin-badge badge-disconnected">● NONAKTIF</span>'

                assigned_str = datetime.fromtimestamp(assigned_at).strftime("%d %b %Y, %H:%M") if assigned_at > 0 else "-"

                st.markdown(f"""
                <div style="background: #f8fafc; border: 1px solid #dbe4ef; border-radius: 10px; padding: 16px; margin-top: 14px;">
                    <div style="font-family: monospace; font-size: 0.75rem; color: #6b7280; word-break: break-all; margin-bottom: 10px;">
                        {checksum}
                    </div>
                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                        <span class="admin-badge {badge_class}">{display_role}</span>
                        {status_html}
                    </div>
                    <div style="font-size: 0.82rem; color: #4b5563;">
                        <div>📅 Waktu Assign: <strong>{assigned_str}</strong></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error: {str(e)}")

    st.markdown("</div>", unsafe_allow_html=True)

    # Simulation Accounts Listing Card
    st.markdown("""
    <div class="admin-card">
        <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 1.05rem; font-weight: 700; color: #1f2937; margin-bottom: 14px;">
            📋 Status Akun Simulasi Ganache
        </div>
    """, unsafe_allow_html=True)

    for role_name, addr in SIMULATION_ACCOUNTS.items():
        actual_role = ""
        is_active_flag = None
        if st.session_state.get('ganache_connected'):
            try:
                from web3 import Web3
                checksum = Web3.to_checksum_address(addr)
                role_data = st.session_state.contracts['RoleManager'].functions.getRoleData(checksum).call()
                actual_role, is_active_flag = role_data[0], role_data[1]
            except Exception:
                pass

        actual_display = actual_role if actual_role else "Belum di-assign"
        badge_cls = get_role_badge(role_name)

        st.markdown(f"""
        <div style="background: #f8fafc; border: 1px solid #dbe4ef; border-radius: 10px; padding: 12px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span class="admin-badge {badge_cls}">{role_name}</span>
                <div style="font-family: monospace; font-size: 0.7rem; color: #6b7280; margin-top: 4px;">
                    {addr[:14]}...{addr[-6:]}
                </div>
            </div>
            <div style="font-size: 0.8rem; font-weight: 600;">
                {actual_display}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
