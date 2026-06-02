"""
01_F1_Registrasi_Varietas.py
Fitur F1: Registrasi Aset Varietas Benih
Aktor: Penangkar
Smart Contract: MasterData.registerVariety()
"""

import streamlit as st
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import build_transaction, get_web3, get_contracts

# ============================================================
# KONFIGURASI HALAMAN
# ============================================================
st.set_page_config(
    page_title="F1 — Registrasi Varietas | CacaoTrace",
    page_icon="🌱",
    layout="wide"
)

# CSS Tambahan
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
:root {
    --primary: #059669; --accent: #34D399; --bg: #0A1A0F; 
    --card: rgba(5,150,105,0.08); --border: rgba(52,211,153,0.2);
    --text: #F0FDF4; --muted: #6EE7B7;
}
.stApp { background: linear-gradient(135deg, #0A1A0F 0%, #061209 100%) !important; color: var(--text) !important; }
[data-testid="stSidebar"] { background: #061209 !important; border-right: 1px solid var(--border) !important; }
.page-header {
    background: linear-gradient(135deg, rgba(5,150,105,0.2) 0%, rgba(52,211,153,0.08) 100%);
    border: 1px solid var(--border); border-radius: 20px; padding: 32px; margin-bottom: 24px;
    border-left: 4px solid var(--primary);
}
.form-card {
    background: var(--card); border: 1px solid var(--border); border-radius: 16px;
    padding: 28px; margin: 12px 0;
}
.info-card {
    background: rgba(52,211,153,0.05); border: 1px solid rgba(52,211,153,0.15);
    border-radius: 12px; padding: 16px;
}
.tx-success {
    background: linear-gradient(135deg, rgba(5,150,105,0.15), rgba(52,211,153,0.08));
    border: 1px solid rgba(52,211,153,0.4); border-radius: 12px; padding: 20px;
    font-family: 'Space Grotesk', sans-serif;
}
.result-card {
    background: rgba(5,150,105,0.05); border: 1px solid rgba(5,150,105,0.2);
    border-radius: 12px; padding: 16px; margin: 8px 0;
}
.stTextInput > div > div > input, .stNumberInput > div > div > input {
    background: rgba(5,150,105,0.05) !important; border: 1px solid rgba(52,211,153,0.2) !important;
    border-radius: 10px !important; color: #F0FDF4 !important;
}
.stButton > button {
    background: linear-gradient(135deg, #059669, #10B981) !important; color: #F0FDF4 !important;
    border: none !important; border-radius: 10px !important; font-weight: 600 !important;
    padding: 0.6rem 2rem !important; transition: all 0.3s !important;
}
.stButton > button:hover { transform: translateY(-2px) !important; box-shadow: 0 8px 24px rgba(52,211,153,0.3) !important; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# GUARD: CEK SESSION STATE
# ============================================================
def check_auth(required_role: str = "Penangkar") -> bool:
    if not st.session_state.get('is_logged_in'):
        st.warning("⚠️ Silakan login terlebih dahulu melalui halaman utama.")
        st.page_link("app.py", label="← Kembali ke Dashboard", icon="🏠")
        return False
    if st.session_state.get('role') != required_role:
        st.error(f"🚫 Akses Ditolak! Halaman ini hanya untuk **{required_role}**. Role Anda: **{st.session_state.get('role', 'Tidak Diketahui')}**")
        st.page_link("app.py", label="← Kembali ke Dashboard", icon="🏠")
        return False
    return True

# ============================================================
# HEADER HALAMAN
# ============================================================
st.markdown("""
<div class="page-header">
    <div style="font-size: 2rem; margin-bottom: 8px;">🌱</div>
    <div style="font-family: 'Space Grotesk', sans-serif; font-size: 1.8rem; font-weight: 700; color: #34D399;">
        F1 — Registrasi Varietas Benih
    </div>
    <div style="color: #6EE7B7; font-size: 0.95rem; margin-top: 8px;">
        Mendaftarkan aset varietas benih kakao ke blockchain. Data tersimpan permanen dan tidak dapat diubah.
    </div>
    <div style="margin-top: 12px; font-size: 0.75rem; color: #4ADE80;">
        📋 Smart Contract: <code style="background: rgba(52,211,153,0.1); padding: 2px 8px; border-radius: 4px;">MasterData.registerVariety()</code>
        &nbsp;|&nbsp; 👤 Aktor: <strong>Penangkar</strong>
    </div>
</div>
""", unsafe_allow_html=True)

if not check_auth("Penangkar"):
    st.stop()

# ============================================================
# LAYOUT UTAMA: 2 KOLOM
# ============================================================
col_form, col_info = st.columns([3, 2], gap="large")

with col_form:
    st.markdown("""
    <div class="form-card">
        <div style="font-family: 'Space Grotesk', sans-serif; font-size: 1.1rem; font-weight: 600; 
             color: #34D399; margin-bottom: 20px;">📝 Form Registrasi Varietas</div>
    """, unsafe_allow_html=True)
    
    with st.form("form_registrasi_varietas", clear_on_submit=False):
        id_varietas = st.text_input(
            "🏷️ ID Varietas *",
            placeholder="Contoh: VAR-LINDAK-001",
            help="ID unik untuk varietas benih ini. Tidak boleh duplikat di blockchain."
        )
        
        sk_pelepasan = st.text_input(
            "📄 Nomor SK Pelepasan *",
            placeholder="Contoh: SK.123/BPSB/2024",
            help="Nomor Surat Keputusan Pelepasan varietas dari instansi berwenang."
        )
        
        masa_edar = st.number_input(
            "📅 Masa Edar (Tahun) *",
            min_value=1,
            max_value=50,
            value=5,
            step=1,
            help="Jangka waktu validitas edar benih dalam tahun."
        )
        
        st.markdown("---")
        st.markdown(f"""
        <div style="font-size: 0.8rem; color: #6EE7B7; margin-bottom: 8px;">
            🔑 Transaksi akan dikirim dari wallet:<br>
            <code style="font-size: 0.75rem;">{st.session_state.get('wallet_address', 'N/A')}</code>
        </div>
        """, unsafe_allow_html=True)
        
        submitted = st.form_submit_button(
            "🌱 Daftarkan Varietas ke Blockchain",
            use_container_width=True
        )
        
        if submitted:
            # Validasi Input
            errors = []
            if not id_varietas.strip():
                errors.append("ID Varietas wajib diisi.")
            if not sk_pelepasan.strip():
                errors.append("Nomor SK Pelepasan wajib diisi.")
            if masa_edar < 1:
                errors.append("Masa Edar minimal 1 tahun.")
            
            if errors:
                for err in errors:
                    st.error(f"❌ {err}")
            elif not st.session_state.get('private_key'):
                st.error("❌ Private Key belum diinput! Kembali ke halaman utama dan isi Private Key.")
            else:
                with st.spinner("⏳ Mengirim transaksi ke blockchain..."):
                    try:
                        w3 = st.session_state.w3
                        contracts = st.session_state.contracts
                        master_data = contracts['MasterData']
                        
                        # Bangun function call
                        contract_func = master_data.functions.registerVariety(
                            id_varietas.strip(),
                            sk_pelepasan.strip(),
                            int(masa_edar)
                        )
                        
                        # Kirim transaksi
                        result = build_transaction(
                            w3,
                            contract_func,
                            st.session_state.wallet_address,
                            st.session_state.private_key
                        )
                        
                        if result['success']:
                            st.markdown(f"""
                            <div class="tx-success">
                                <div style="font-size: 1.2rem; color: #34D399; margin-bottom: 12px;">✅ Varietas Berhasil Didaftarkan!</div>
                                <div style="font-size: 0.8rem; color: #6EE7B7;">
                                    <div>🏷️ ID Varietas: <strong>{id_varietas}</strong></div>
                                    <div>📄 SK Pelepasan: <strong>{sk_pelepasan}</strong></div>
                                    <div>📅 Masa Edar: <strong>{masa_edar} Tahun</strong></div>
                                    <div style="margin-top: 10px; font-family: monospace; font-size: 0.7rem;">
                                        🔗 TX Hash: {result['tx_hash'][:20]}...{result['tx_hash'][-10:]}
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            st.balloons()
                        else:
                            st.error(f"❌ Transaksi Gagal: {result['error']}")
                    except Exception as e:
                        st.error(f"❌ Error tidak terduga: {str(e)}")
    
    st.markdown("</div>", unsafe_allow_html=True)

with col_info:
    # Panel Cek Varietas
    st.markdown("""
    <div class="form-card">
        <div style="font-family: 'Space Grotesk', sans-serif; font-size: 1rem; font-weight: 600; 
             color: #34D399; margin-bottom: 16px;">🔍 Cek Data Varietas</div>
    """, unsafe_allow_html=True)
    
    check_id = st.text_input(
        "Cari berdasarkan ID Varietas",
        placeholder="VAR-LINDAK-001",
        key="check_varietas_id"
    )
    
    if st.button("🔍 Cek Varietas", key="btn_check_var"):
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
                    <div class="result-card">
                        <div style="font-weight: 600; color: #34D399; margin-bottom: 12px;">✅ Varietas Ditemukan</div>
                        <table style="width: 100%; font-size: 0.8rem; color: #D1FAE5;">
                            <tr><td style="color: #6EE7B7; padding: 4px 0;">🏷️ ID Varietas</td><td><strong>{id_var}</strong></td></tr>
                            <tr><td style="color: #6EE7B7; padding: 4px 0;">📄 SK Pelepasan</td><td>{sk_pep}</td></tr>
                            <tr><td style="color: #6EE7B7; padding: 4px 0;">📅 Masa Edar</td><td>{masa} Tahun</td></tr>
                            <tr><td style="color: #6EE7B7; padding: 4px 0;">👤 Penangkar</td><td style="font-family: monospace; font-size: 0.7rem;">{penangkar_addr}</td></tr>
                            <tr><td style="color: #6EE7B7; padding: 4px 0;">🕐 Timestamp</td><td>{reg_time}</td></tr>
                        </table>
                    </div>
                    """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Panel Informasi
    st.markdown("""
    <div class="info-card" style="margin-top: 16px;">
        <div style="font-size: 0.85rem; font-weight: 600; color: #34D399; margin-bottom: 10px;">ℹ️ Informasi Penting</div>
        <ul style="font-size: 0.8rem; color: #6EE7B7; margin: 0; padding-left: 18px; line-height: 1.8;">
            <li>ID Varietas harus unik — tidak bisa didaftarkan dua kali</li>
            <li>Data bersifat <strong>immutable</strong> setelah tersimpan di blockchain</li>
            <li>Varietas yang terdaftar dapat digunakan sebagai referensi saat registrasi Lahan (F2)</li>
            <li>Transaksi memerlukan gas fee dari saldo Ganache</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Tampilkan Akun Penangkar
    st.markdown(f"""
    <div class="info-card" style="margin-top: 12px;">
        <div style="font-size: 0.8rem; color: #6EE7B7;">
            <div style="font-weight: 600; margin-bottom: 8px;">👤 Sesi Aktif</div>
            <div>Role: <span style="color: #34D399; font-weight: 600;">Penangkar</span></div>
            <div style="font-family: monospace; font-size: 0.7rem; word-break: break-all; margin-top: 4px; color: #A7F3D0;">
                {st.session_state.get('wallet_address', 'N/A')}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
