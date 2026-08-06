"""
01_F1_Registrasi_Varietas.py
Fitur F1: Registrasi Aset Varietas Benih
Aktor: Penangkar
Smart Contract: MasterData.registerVariety()
Theme: adminHMD Enterprise Admin System
"""

import streamlit as st
import sys
import os
from datetime import datetime

# Path setup
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import build_transaction, get_web3, get_contracts
from style_adminhmd import inject_adminhmd_theme

# Page Configuration
st.set_page_config(
    page_title="F1 — Registrasi Varietas | CacaoTrace",
    page_icon="🌱",
    layout="wide"
)

inject_adminhmd_theme()

# Auth Check Guard
def check_auth(required_role: str = "Penangkar") -> bool:
    if not st.session_state.get('is_logged_in'):
        st.warning("⚠️ Silakan login terlebih dahulu.")
        st.page_link("app.py", label="← Kembali ke Halaman Login", icon="🔑")
        return False
    if st.session_state.get('role') != required_role:
        st.error(f"🚫 Akses Ditolak! Halaman ini hanya untuk **{required_role}**.")
        st.page_link("app.py", label="← Kembali ke Dashboard Utama", icon="🏠")
        return False
    return True

if not check_auth("Penangkar"):
    st.stop()

# Top Navbar Header
st.markdown("""
<div class="admin-topbar">
    <div class="admin-topbar-title">
        <span style="font-size: 1.5rem;">🌱</span> F1 — Registrasi Varietas Benih Kakao
    </div>
    <div class="admin-topbar-meta">
        <span class="admin-badge badge-penangkar">Aktor: Penangkar</span>
        <span class="admin-badge badge-connected">MasterData.registerVariety()</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Page Header
st.markdown("""
<div class="admin-page-header">
    <h1>Registrasi Aset Varietas Benih</h1>
    <p>Daftarkan aset varietas benih kakao ke blockchain beserta nomor SK Pelepasan dan masa edar valid.</p>
</div>
""", unsafe_allow_html=True)

col_form, col_info = st.columns([3, 2], gap="large")

with col_form:
    st.markdown("""
    <div class="admin-card">
        <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 1.1rem; font-weight: 700; color: #1f2937; margin-bottom: 16px;">
            📝 Form Registrasi Varietas
        </div>
    """, unsafe_allow_html=True)
    
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        jenis_varietas = st.text_input("Nama/Jenis Varietas *", placeholder="Contoh: MCC02", key="var_jenis")
    with col_v2:
        mmyy_varietas = st.text_input("Bulan-Tahun Edar (MMYY) *", placeholder="Contoh: 0722", max_chars=4, key="var_mmyy")
        
    sk_pelepasan = st.text_input(
        "📄 Nomor SK Pelepasan *",
        placeholder="Contoh: KPTS.12/XI/2025",
        help="Nomor SK Pelepasan varietas dari instansi berwenang."
    )
    
    masa_edar = st.number_input(
        "📅 Masa Edar (Tahun) *",
        min_value=1,
        max_value=50,
        value=5,
        step=1
    )

    from utils import generate_varietas_id
    if jenis_varietas.strip() and mmyy_varietas.strip():
        id_varietas = generate_varietas_id(jenis_varietas.strip(), mmyy_varietas.strip(), int(masa_edar))
    else:
        id_varietas = ""

    st.text_input(
        "🏷️ ID Varietas Tergenerate (Otomatis) *",
        value=id_varietas,
        disabled=True
    )

    st.markdown("<br>", unsafe_allow_html=True)
    submitted = st.button("🌱 Daftarkan Varietas ke Blockchain", use_container_width=True)
    
    if submitted:
        errors = []
        if not jenis_varietas.strip():
            errors.append("Nama/Jenis Varietas wajib diisi.")
        if not mmyy_varietas.strip() or len(mmyy_varietas.strip()) != 4:
            errors.append("Bulan-Tahun Edar (MMYY) harus 4 karakter.")
        if not sk_pelepasan.strip():
            errors.append("Nomor SK Pelepasan wajib diisi.")
        if not id_varietas:
            errors.append("Gagal membuat ID Varietas. Lengkapi Jenis dan Bulan-Tahun Edar.")
        
        if errors:
            for err in errors:
                st.error(f"❌ {err}")
        elif not st.session_state.get('private_key'):
            st.error("❌ Private Key belum diinput!")
        else:
            with st.spinner("⏳ Mengirim transaksi ke blockchain..."):
                try:
                    w3 = st.session_state.w3
                    contracts = st.session_state.contracts
                    master_data = contracts['MasterData']
                    
                    contract_func = master_data.functions.registerVariety(
                        id_varietas,
                        sk_pelepasan.strip(),
                        int(masa_edar)
                    )
                    
                    result = build_transaction(
                        w3, contract_func,
                        st.session_state.wallet_address,
                        st.session_state.private_key
                    )
                    
                    if result['success']:
                        st.markdown(f"""
                        <div class="tx-success" style="background:#ccfbf1;border:1px solid #99f6e4;border-radius:12px;padding:18px;">
                            <div style="font-size: 1.25rem; font-weight: 700; color: #0f766e; margin-bottom: 14px;">✅ Varietas Berhasil Didaftarkan!</div>
                            <table style="font-size: 0.88rem; color: #1e293b; width: 100%; border-collapse: collapse;">
                                <tr style="border-bottom: 1px solid #99f6e4;"><td style="color: #0f766e; font-weight: 600; padding: 6px 0; width: 35%;">🌱 ID Varietas</td><td style="color: #0f172a; padding: 6px 0;"><strong>{id_varietas}</strong></td></tr>
                                <tr style="border-bottom: 1px solid #99f6e4;"><td style="color: #0f766e; font-weight: 600; padding: 6px 0;">📄 SK Pelepasan</td><td style="color: #0f172a; padding: 6px 0;">{sk_pelepasan.strip()}</td></tr>
                                <tr style="border-bottom: 1px solid #99f6e4;"><td style="color: #0f766e; font-weight: 600; padding: 6px 0;">📅 Masa Edar</td><td style="color: #0f172a; padding: 6px 0;"><strong>{masa_edar} Tahun</strong></td></tr>
                                <tr><td style="color: #0f766e; font-weight: 600; padding: 6px 0;">🔗 TX Hash</td>
                                    <td style="font-family: monospace; font-size: 0.75rem; color: #334155; word-break: break-all; padding: 6px 0;">{result['tx_hash']}</td>
                                </tr>
                            </table>
                        </div>
                        """, unsafe_allow_html=True)
                        st.balloons()
                    else:
                        st.error(f"❌ Transaksi Gagal: {result['error']}")
                except Exception as e:
                    st.error(f"❌ Error tidak terduga: {str(e)}")

    st.markdown("</div>", unsafe_allow_html=True)

with col_info:
    st.markdown("""
    <div class="admin-card">
        <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 1.05rem; font-weight: 700; color: #1f2937; margin-bottom: 14px;">
            🔍 Cek Data Varietas On-Chain
        </div>
    """, unsafe_allow_html=True)
    
    check_id = st.text_input("Cari ID Varietas", placeholder="VAR-MCC02-0722-5", key="check_varietas_id")
    
    if st.button("🔍 Cek Data Varietas", key="btn_check_var", use_container_width=True):
        if check_id.strip() and st.session_state.get('ganache_connected'):
            try:
                contracts = st.session_state.contracts
                master_data = contracts['MasterData']
                data = master_data.functions.dataVarietas(check_id.strip()).call()
                
                id_var, sk_pep, masa, penangkar_addr, timestamp = data
                
                if timestamp == 0:
                    st.warning(f"⚠️ Varietas `{check_id}` belum terdaftar di blockchain.")
                else:
                    reg_time = datetime.fromtimestamp(timestamp).strftime("%d %b %Y, %H:%M:%S")
                    st.markdown(f"""
                    <div style="background: #f8fafc; border: 1px solid #dbe4ef; border-radius: 10px; padding: 16px; margin-top: 12px;">
                        <div style="font-weight: 700; color: #0f766e; margin-bottom: 10px;">✅ Varietas Ditemukan</div>
                        <div style="font-size: 0.85rem; color: #1f2937; line-height: 1.8;">
                            <div>🏷️ ID Varietas: <strong>{id_var}</strong></div>
                            <div>📄 SK Pelepasan: <strong>{sk_pep}</strong></div>
                            <div>📅 Masa Edar: <strong>{masa} Tahun</strong></div>
                            <div>👤 Penangkar: <code style="font-size: 0.72rem;">{penangkar_addr}</code></div>
                            <div>🕐 Reg. Waktu: <strong>{reg_time}</strong></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    st.markdown("</div>", unsafe_allow_html=True)

# Tabel Semua Varietas
st.markdown("""
<div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 1.2rem; font-weight: 700; color: #1f2937; margin-top: 20px; margin-bottom: 16px;">
    📋 Daftar Semua Varietas Terdaftar
</div>
""", unsafe_allow_html=True)

if st.button("🔄 Muat / Refresh Daftar Varietas", key="btn_refresh_varietas"):
    st.session_state['varietas_list_loaded'] = True

if st.session_state.get('varietas_list_loaded') and st.session_state.get('ganache_connected'):
    try:
        contracts = st.session_state.contracts
        master_data = contracts['MasterData']
        all_ids = master_data.functions.getAllVarietasIds().call()
        total = master_data.functions.getTotalVarietas().call()

        st.caption(f"Total Varietas Terdaftar: {total}")

        if not all_ids:
            st.info("📭 Belum ada varietas yang terdaftar.")
        else:
            rows = []
            for vid in all_ids:
                try:
                    data = master_data.functions.dataVarietas(vid).call()
                    id_var, sk_pep, masa, penangkar_addr, ts = data
                    reg_time = datetime.fromtimestamp(ts).strftime("%d %b %Y")
                    rows.append({
                        "ID Varietas": id_var,
                        "SK Pelepasan": sk_pep,
                        "Masa Edar (Thn)": masa,
                        "Penangkar": f"{penangkar_addr[:10]}...{penangkar_addr[-4:]}",
                        "Tgl Daftar": reg_time,
                    })
                except Exception:
                    pass

            import pandas as pd
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)
    except Exception as e:
        st.error(f"❌ Gagal memuat data: {str(e)}")
