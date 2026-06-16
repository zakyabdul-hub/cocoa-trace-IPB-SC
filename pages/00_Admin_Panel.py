"""
00_Admin_Panel.py
Panel Admin: Manajemen Peran Pengguna
Aktor: Admin
Smart Contract: RoleManager.assignRole(), deactivateRole(), getRole(), getRoleData()
"""

import streamlit as st
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import build_transaction, VALID_ROLES, SIMULATION_ACCOUNTS

# ============================================================
# KONFIGURASI HALAMAN
# ============================================================
st.set_page_config(
    page_title="Admin Panel | CacaoTrace",
    page_icon="👑",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
.stApp { background: linear-gradient(135deg, #0A0A1A 0%, #06060F 100%) !important; color: #F5F0FF !important; }
[data-testid="stSidebar"] { background: #06060F !important; border-right: 1px solid rgba(124,58,237,0.2) !important; }
.page-header {
    background: linear-gradient(135deg, rgba(124,58,237,0.2) 0%, rgba(167,139,250,0.08) 100%);
    border: 1px solid rgba(124,58,237,0.3); border-radius: 20px; padding: 32px; margin-bottom: 24px;
    border-left: 4px solid #7C3AED;
}
.form-card {
    background: rgba(124,58,237,0.05); border: 1px solid rgba(124,58,237,0.15);
    border-radius: 16px; padding: 24px; margin: 12px 0;
}
.deactivate-card {
    background: rgba(239,68,68,0.04); border: 1px solid rgba(239,68,68,0.15);
    border-radius: 16px; padding: 24px; margin: 12px 0;
}
.account-card {
    background: rgba(124,58,237,0.05); border: 1px solid rgba(167,139,250,0.15);
    border-radius: 12px; padding: 14px; margin: 8px 0;
    display: flex; justify-content: space-between; align-items: center;
}
.role-pill {
    display: inline-block; padding: 3px 12px; border-radius: 12px;
    font-size: 0.72rem; font-weight: 600; text-transform: uppercase;
}
.status-active {
    display: inline-block; padding: 2px 10px; border-radius: 10px;
    background: rgba(52,211,153,0.15); border: 1px solid rgba(52,211,153,0.4);
    color: #4ADE80; font-size: 0.7rem; font-weight: 600;
}
.status-inactive {
    display: inline-block; padding: 2px 10px; border-radius: 10px;
    background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.3);
    color: #F87171; font-size: 0.7rem; font-weight: 600;
}
.stTextInput > div > div > input {
    background: rgba(124,58,237,0.05) !important; border: 1px solid rgba(124,58,237,0.2) !important;
    border-radius: 10px !important; color: #F5F0FF !important;
}
.stSelectbox > div > div {
    background: rgba(124,58,237,0.05) !important; border: 1px solid rgba(124,58,237,0.2) !important;
    border-radius: 10px !important;
}
.stButton > button {
    background: linear-gradient(135deg, #7C3AED, #8B5CF6) !important; color: white !important;
    border: none !important; border-radius: 10px !important; font-weight: 600 !important;
    transition: all 0.3s !important;
}
.stButton > button:hover { transform: translateY(-2px) !important; box-shadow: 0 8px 24px rgba(124,58,237,0.35) !important; }
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
    if st.session_state.get('role') != "Admin":
        st.error("🚫 Akses Ditolak! Halaman ini hanya untuk **Admin**.")
        st.page_link("app.py", label="← Kembali ke Dashboard", icon="🏠")
        return False
    return True

# ============================================================
# HELPER
# ============================================================
def get_role_color(role: str) -> tuple:
    colors = {
        'Admin': ('#7C3AED', '#DDD6FE'),
        'Penangkar': ('#059669', '#A7F3D0'),
        'Petani': ('#0284C7', '#BAE6FD'),
        'Pengepul': ('#D97706', '#FDE68A'),
        'Perusahaan': ('#DC2626', '#FEE2E2'),
        '': ('#4B5563', '#D1D5DB'),
    }
    return colors.get(role, ('#4B5563', '#D1D5DB'))

# ============================================================
# HEADER
# ============================================================
st.markdown("""
<div class="page-header">
    <div style="font-size: 2rem; margin-bottom: 8px;">👑</div>
    <div style="font-family: 'Space Grotesk', sans-serif; font-size: 1.8rem; font-weight: 700; color: #A78BFA;">
        Admin Panel - Manajemen Peran
    </div>
    <div style="color: #C4B5FD; font-size: 0.95rem; margin-top: 8px;">
        Assign dan kelola peran pengguna dalam sistem ketertelusuran kakao.
        Hanya Admin yang dapat mengakses panel ini.
    </div>
    <div style="margin-top: 12px; font-size: 0.75rem; color: #A78BFA;">
        📋 Smart Contract: <code style="background: rgba(124,58,237,0.1); padding: 2px 8px; border-radius: 4px;">RoleManager.assignRole() / deactivateRole()</code>
    </div>
</div>
""", unsafe_allow_html=True)

if not check_auth():
    st.stop()

# ============================================================
# LAYOUT
# ============================================================
col_assign, col_info = st.columns([3, 2], gap="large")

with col_assign:
    # ASSIGN ROLE
    st.markdown("""
    <div class="form-card">
        <div style="font-family: 'Space Grotesk', sans-serif; font-size: 1.1rem; font-weight: 600; 
             color: #A78BFA; margin-bottom: 20px;">➕ Assign Peran ke Pengguna</div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="font-size: 0.78rem; color: #C4B5FD; background: rgba(124,58,237,0.08); 
         border-radius: 8px; padding: 10px; margin-bottom: 16px;">
        ℹ️ Jika pengguna sudah memiliki peran aktif, peran lama akan otomatis <strong>dinonaktifkan</strong>
        dan digantikan peran baru. Riwayat tetap tersimpan di blockchain.
    </div>
    """, unsafe_allow_html=True)

    with st.form("form_assign_role"):
        target_address = st.text_input(
            "🏷️ Wallet Address Target *",
            placeholder="0x...",
            help="Wallet address pengguna yang akan diberi peran"
        )

        selected_role = st.selectbox(
            "👤 Pilih Peran *",
            options=["Penangkar", "Petani", "Pengepul", "Perusahaan"],
            help="Pilih peran yang akan diberikan (hanya role yang ada di whitelist kontrak)"
        )

        st.markdown(f"""
        <div style="font-size: 0.8rem; color: #C4B5FD; margin-bottom: 10px;">
            🔑 Admin Wallet: <code>{st.session_state.get('wallet_address','')[:20]}...</code>
        </div>
        """, unsafe_allow_html=True)

        submitted_assign = st.form_submit_button("👑 Assign Peran", use_container_width=True)

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

                with st.spinner(f"⏳ Assigning peran {selected_role} ke {checksum[:10]}..."):
                    w3 = st.session_state.w3
                    contracts = st.session_state.contracts
                    role_manager = contracts['RoleManager']

                    contract_func = role_manager.functions.assignRole(checksum, selected_role)
                    result = build_transaction(
                        w3, contract_func,
                        st.session_state.wallet_address,
                        st.session_state.private_key
                    )

                    if result['success']:
                        bg_color, text_color = get_role_color(selected_role)
                        st.markdown(f"""
                        <div style="background: rgba(52,211,153,0.1); border: 1px solid rgba(52,211,153,0.3);
                             border-radius: 12px; padding: 16px;">
                            <div style="color: #4ADE80; font-weight: 700; margin-bottom: 8px;">✅ Peran Berhasil Di-Assign!</div>
                            <div style="font-size: 0.85rem; color: #86EFAC;">
                                🏷️ Address: <code>{checksum}</code><br>
                                👤 Peran: <strong style="color: {bg_color};">{selected_role}</strong><br>
                                🔗 TX: <code style="font-size: 0.7rem;">{result['tx_hash'][:30]}...</code>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.error(f"❌ Gagal: {result['error']}")

    st.markdown("</div>", unsafe_allow_html=True)

    # DEACTIVATE ROLE (menggantikan removeRole)
    st.markdown("""
    <div class="deactivate-card" style="margin-top: 16px;">
        <div style="font-family: 'Space Grotesk', sans-serif; font-size: 1.1rem; font-weight: 600; 
             color: #F87171; margin-bottom: 8px;">🔒 Nonaktifkan Peran Pengguna</div>
        <div style="font-size: 0.75rem; color: #FCA5A5; margin-bottom: 16px; background: rgba(239,68,68,0.06);
             border-radius: 8px; padding: 10px;">
            ⚠️ Peran tidak akan dihapus dari blockchain (immutable). 
            Data peran lama tetap tersimpan dengan status <strong>isActive = false</strong>.
            Pengguna yang dinonaktifkan tidak bisa mengakses fungsi apapun sampai diberi peran baru.
        </div>
    """, unsafe_allow_html=True)

    with st.form("form_deactivate_role"):
        remove_address = st.text_input(
            "🏷️ Wallet Address Target *",
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

                with st.spinner("⏳ Menonaktifkan peran..."):
                    w3 = st.session_state.w3
                    contracts = st.session_state.contracts
                    role_manager = contracts['RoleManager']

                    # Panggil deactivateRole (bukan removeRole)
                    contract_func = role_manager.functions.deactivateRole(checksum)
                    result = build_transaction(
                        w3, contract_func,
                        st.session_state.wallet_address,
                        st.session_state.private_key
                    )

                    if result['success']:
                        st.success(f"✅ Peran dari `{checksum[:20]}...` berhasil dinonaktifkan!")
                        st.markdown(f"""
                        <div style="font-size: 0.78rem; color: #FCA5A5; margin-top: 8px;">
                            🔗 TX Hash: <code>{result['tx_hash'][:30]}...</code><br>
                            📝 Riwayat peran tetap tersimpan permanen di blockchain.
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.error(f"❌ Gagal: {result['error']}")

    st.markdown("</div>", unsafe_allow_html=True)

with col_info:
    # CEK ROLE + ROLE DATA
    st.markdown("""
    <div class="form-card">
        <div style="font-family: 'Space Grotesk', sans-serif; font-size: 1rem; font-weight: 600; 
             color: #A78BFA; margin-bottom: 16px;">🔍 Cek Peran & Status Pengguna</div>
    """, unsafe_allow_html=True)

    check_addr = st.text_input("Wallet Address", placeholder="0x...", key="check_role_addr")

    if st.button("🔍 Cek Peran", key="btn_check_role"):
        if check_addr.strip() and st.session_state.get('ganache_connected'):
            from web3 import Web3
            try:
                checksum = Web3.to_checksum_address(check_addr.strip())
                contracts = st.session_state.contracts
                role_manager = contracts['RoleManager']

                # Ambil data lengkap dari getRoleData()
                role_data = role_manager.functions.getRoleData(checksum).call()
                role, is_active, assigned_at, deactivated_at = role_data

                display_role = role if role else "(Tidak ada peran)"
                bg_color, text_color = get_role_color(role)

                status_html = '<span class="status-active">● AKTIF</span>' if is_active else '<span class="status-inactive">● NONAKTIF</span>'
                assigned_str = datetime.fromtimestamp(assigned_at).strftime("%d %b %Y, %H:%M") if assigned_at > 0 else "-"
                deact_str = datetime.fromtimestamp(deactivated_at).strftime("%d %b %Y, %H:%M") if deactivated_at > 0 else "-"

                st.markdown(f"""
                <div style="background: rgba(124,58,237,0.08); border: 1px solid rgba(167,139,250,0.2);
                     border-radius: 12px; padding: 16px;">
                    <div style="font-family: monospace; font-size: 0.75rem; color: #C4B5FD; margin-bottom: 10px; word-break: break-all;">
                        {checksum}
                    </div>
                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                        <span style="color: #A78BFA;">Peran:</span>
                        <span class="role-pill" style="background: {bg_color}20; color: {bg_color}; border: 1px solid {bg_color}50;">
                            {display_role}
                        </span>
                        {status_html}
                    </div>
                    <div style="font-size: 0.75rem; color: #C4B5FD; line-height: 1.8;">
                        <div>📅 Assign Terakhir: <strong>{assigned_str}</strong></div>
                        <div>🔒 Dinonaktifkan: <strong>{deact_str}</strong></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error: {str(e)}")

    st.markdown("</div>", unsafe_allow_html=True)

    # DAFTAR AKUN SIMULASI
    st.markdown("""
    <div class="form-card" style="margin-top: 16px;">
        <div style="font-family: 'Space Grotesk', sans-serif; font-size: 1rem; font-weight: 600; 
             color: #A78BFA; margin-bottom: 16px;">📋 Akun Simulasi</div>
    """, unsafe_allow_html=True)

    for role_name, addr in SIMULATION_ACCOUNTS.items():
        bg_color, text_color = get_role_color(role_name)

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
        status_dot = "🟢" if is_active_flag else ("🔴" if is_active_flag is False else "⚪")

        st.markdown(f"""
        <div class="account-card">
            <div>
                <div style="font-size: 0.8rem; font-weight: 600; color: {bg_color}; margin-bottom: 4px;">
                    {role_name}
                </div>
                <div style="font-family: monospace; font-size: 0.68rem; color: #7C6DAE;">
                    {addr[:18]}...{addr[-4:]}
                </div>
            </div>
            <div style="font-size: 0.7rem; color: #A78BFA; text-align: right;">
                {status_dot} <strong>{actual_display}</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # Panduan
    st.markdown("""
    <div style="background: rgba(124,58,237,0.05); border: 1px solid rgba(124,58,237,0.12);
         border-radius: 12px; padding: 14px; margin-top: 12px; font-size: 0.78rem; color: #C4B5FD;">
        <div style="font-weight: 600; color: #A78BFA; margin-bottom: 8px;">ℹ️ Catatan Penting</div>
        <ul style="margin: 0; padding-left: 16px; line-height: 1.8;">
            <li>Role valid: Penangkar, Petani, Pengepul, Perusahaan</li>
            <li>Satu wallet hanya bisa memiliki satu peran aktif</li>
            <li>Peran lama <strong>tidak dihapus</strong> saat di-assign ulang, hanya dinonaktifkan</li>
            <li>Peran yang dinonaktifkan tidak bisa mengakses fitur apapun</li>
            <li>Semua perubahan peran tercatat sebagai event di blockchain</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
