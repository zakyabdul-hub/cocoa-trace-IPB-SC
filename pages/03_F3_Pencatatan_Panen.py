"""
03_F3_Pencatatan_Panen.py
Fitur F3: Pencatatan Aset Panen Petani
Aktor: Petani
Smart Contract: Traceability.createHarvestBatch()
"""

import streamlit as st
import sys
import os
from datetime import datetime

from config import build_transaction

# Path setup
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from style_adminhmd import inject_adminhmd_theme

# ============================================================
# KONFIGURASI HALAMAN
# ============================================================
st.set_page_config(
    page_title="F3 — Pencatatan Panen | CacaoTrace",
    page_icon="🌾",
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
        st.error(f"🚫 Akses Ditolak! Halaman ini hanya untuk **Petani**.")
        st.page_link("app.py", label="← Kembali ke Dashboard", icon="🏠")
        return False
    return True

# Top Navbar Header
st.markdown("""
<div class="admin-topbar">
    <div class="admin-topbar-title">
        <span style="font-size: 1.5rem;">🌾</span> F3 — Pencatatan Hasil Panen Kakao
    </div>
    <div class="admin-topbar-meta">
        <span class="admin-badge badge-petani">Aktor: Petani</span>
        <span class="admin-badge badge-connected">Traceability.createHarvestBatch()</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Page Header
st.markdown("""
<div class="admin-page-header">
    <h1>Pencatatan Hasil Panen Petani</h1>
    <p>Catat hasil panen harian dari lahan terdaftar ke blockchain sebagai aset batch panen awal yang terverifikasi.</p>
</div>
""", unsafe_allow_html=True)

if not check_auth():
    st.stop()

# ============================================================
# LAYOUT
# ============================================================
col_form, col_info = st.columns([3, 2], gap="large")

with col_form:
    st.markdown('<div class="form-card">', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-family: 'Space Grotesk', sans-serif; font-size: 1.1rem; font-weight: 600; 
         color: #4ADE80; margin-bottom: 20px;">📝 Form Pencatatan Batch Panen</div>
    """, unsafe_allow_html=True)
    
    # Tampilkan daftar lahan milik petani ini
    with st.expander("📊 Lihat Daftar Lahan Saya (F2)", expanded=False):
        if st.session_state.get('ganache_connected') and st.session_state.get('wallet_address'):
            try:
                from web3 import Web3
                my_addr = Web3.to_checksum_address(st.session_state.wallet_address)
                lahan_ids = st.session_state.contracts['MasterData'].functions.getLahanByPetani(my_addr).call()
                if lahan_ids:
                    data_lahan = []
                    for lid in lahan_ids:
                        ldata = st.session_state.contracts['MasterData'].functions.dataLahan(lid).call()
                        data_lahan.append({
                            "ID Lahan": ldata[0],
                            "No STDB": ldata[1],
                            "Luas (m²)": ldata[4],
                            "Var Utama": ldata[5]
                        })
                    st.dataframe(data_lahan, use_container_width=True, hide_index=True)
                else:
                    st.info("Anda belum mendaftarkan lahan apapun.")
            except Exception as e:
                st.error(f"Gagal memuat lahan: {e}")

    # Ambil daftar lahan milik petani ini
    lahan_list = []
    if st.session_state.get('ganache_connected') and st.session_state.get('wallet_address'):
        try:
            from web3 import Web3
            my_addr = Web3.to_checksum_address(st.session_state.wallet_address)
            lahan_list = st.session_state.contracts['MasterData'].functions.getLahanByPetani(my_addr).call()
        except Exception:
            pass

    # Form Pencatatan Panen (Tanpa st.form untuk respon real-time ID)
    st.markdown("**📋 Data Panen Dasar**")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        tgl_panen = st.date_input("Tanggal Panen *", value=datetime.today(), key="panen_date")
    with col_p2:
        id_lahan_ref = st.selectbox(
            "🗺️ ID Lahan Asal *",
            options=[""] + lahan_list,
            format_func=lambda x: "Pilih Lahan..." if x == "" else x,
            help="Pilih lahan Anda yang sudah terdaftar di blockchain (F2).",
            disabled=len(lahan_list) == 0,
            key="panen_lahan_ref"
        )
    if not lahan_list:
        st.caption("⚠️ Anda belum memiliki lahan terdaftar. Silakan daftar di F2.")

    col_qty, col_ferm = st.columns([2, 1])
    with col_qty:
        qty_panen = st.number_input(
            "⚖️ Kuantitas Panen (Kg) *",
            min_value=1,
            max_value=100_000,
            value=500,
            step=10,
            help="Jumlah biji kakao yang dipanen dalam kilogram."
        )
    with col_ferm:
        st.markdown("<br>", unsafe_allow_html=True)
        is_fermented = st.checkbox(
            "🧪 Sudah Difermentasi",
            value=False,
            help="Centang jika biji kakao sudah melalui proses fermentasi."
        )

    # Preview status fermentasi
    if is_fermented:
        st.markdown("""
        <div class="ferment-badge-yes">🧪 Status: Sudah Difermentasi ✅</div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="ferment-badge-no">⏳ Status: Belum Difermentasi</div>
        """, unsafe_allow_html=True)

    # Dynamic real-time ID calculation
    id_batch = ""
    if id_lahan_ref.strip():
        from utils import generate_panen_id
        ddmmyy = tgl_panen.strftime("%d%m%y")
        id_batch = generate_panen_id(ddmmyy, id_lahan_ref.strip())

    st.text_input(
        "🏷️ ID Batch Panen Baru (Otomatis) *",
        value=id_batch,
        disabled=True,
        help="ID unik untuk batch panen ini yang dihasilkan secara otomatis dari tanggal dan lahan asal."
    )

    st.markdown("---")
    st.markdown(f"""
    <div style="font-size: 0.8rem; color: #86EFAC; margin-bottom: 8px;">
        🔑 Transaksi dari: <code>{st.session_state.get('wallet_address', 'N/A')[:20]}...</code>
    </div>
    """, unsafe_allow_html=True)
    
    submitted = st.button("🌾 Catat Panen ke Blockchain", use_container_width=True)
    
    if submitted:
        errors = []
        if not id_lahan_ref.strip():
            errors.append("ID Lahan wajib diisi.")
        if qty_panen < 1:
            errors.append("Kuantitas minimal 1 Kg.")
        if not id_batch:
            errors.append("Gagal membuat ID Batch. Pilih Lahan Asal terlebih dahulu.")
        
        if errors:
            for err in errors:
                st.error(f"❌ {err}")
        elif not st.session_state.get('private_key'):
            st.error("❌ Private Key belum diinput!")
        else:
            with st.spinner("⏳ Mencatat panen ke blockchain..."):
                try:
                    w3 = st.session_state.w3
                    contracts = st.session_state.contracts
                    traceability = contracts['Traceability']
                    
                    contract_func = traceability.functions.createHarvestBatch(
                        id_batch,
                        id_lahan_ref.strip(),
                        int(qty_panen),
                        bool(is_fermented)
                    )
                    
                    result = build_transaction(
                        w3,
                        contract_func,
                        st.session_state.wallet_address,
                        st.session_state.private_key
                    )
                    
                    if result['success']:
                        ferment_str = "✅ Sudah Difermentasi" if is_fermented else "⏳ Belum Difermentasi"
                        st.markdown(f"""
                        <div class="tx-success">
                            <div style="font-size: 1.2rem; color: #4ADE80; margin-bottom: 12px;">✅ Batch Panen Berhasil Dicatat!</div>
                            <table style="font-size: 0.8rem; color: #BBF7D0; width: 100%;">
                                <tr><td style="color: #86EFAC; padding: 3px 0;">🏷️ ID Batch</td><td><strong>{id_batch}</strong></td></tr>
                                <tr><td style="color: #86EFAC; padding: 3px 0;">🗺️ ID Lahan</td><td>{id_lahan_ref}</td></tr>
                                <tr><td style="color: #86EFAC; padding: 3px 0;">⚖️ Kuantitas</td><td><strong>{qty_panen:,} Kg</strong></td></tr>
                                <tr><td style="color: #86EFAC; padding: 3px 0;">🧪 Fermentasi</td><td>{ferment_str}</td></tr>
                                <tr><td style="color: #86EFAC; padding: 3px 0;">🔗 TX Hash</td>
                                    <td style="font-family: monospace; font-size: 0.7rem;">{result['tx_hash']}</td>
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

with col_info:
    # Panel Cek Data Panen
    st.markdown('<div class="form-card">', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-family: 'Space Grotesk', sans-serif; font-size: 1rem; font-weight: 600; 
         color: #4ADE80; margin-bottom: 16px;">🔍 Cek Data Batch Panen</div>
    """, unsafe_allow_html=True)
    
    check_batch_id = st.text_input("ID Batch Panen", placeholder="BTC-PETANI-001", key="check_panen")
    
    if st.button("🔍 Cek Batch", key="btn_check_batch"):
        if check_batch_id.strip() and st.session_state.get('ganache_connected'):
            try:
                contracts = st.session_state.contracts
                data = contracts['Traceability'].functions.dataPanen(check_batch_id.strip()).call()
                id_b, id_l, qty, is_ferm, petani, is_agg, ts = data
                
                if ts == 0:
                    st.warning(f"⚠️ Batch `{check_batch_id}` belum terdaftar.")
                else:
                    reg_time = datetime.fromtimestamp(ts).strftime("%d %b %Y, %H:%M")
                    ferm_str = "✅ Ya" if is_ferm else "❌ Belum"
                    agg_str = "🔒 Sudah Diagregasi" if is_agg else "🟢 Tersedia"
                    st.markdown(f"""
                    <div class="result-card">
                        <div style="color: #4ADE80; font-weight: 600; margin-bottom: 10px;">✅ Batch Ditemukan</div>
                        <div style="font-size: 0.78rem; color: #BBF7D0; line-height: 1.8;">
                            <div>🏷️ ID Batch: <strong>{id_b}</strong></div>
                            <div>🗺️ ID Lahan: {id_l}</div>
                            <div>⚖️ Kuantitas: <strong>{qty:,} Kg</strong></div>
                            <div>🧪 Fermentasi: {ferm_str}</div>
                            <div>📊 Status: {agg_str}</div>
                            <div style="font-family: monospace; font-size: 0.7rem; word-break: break-all;">
                                👤 Petani: {petani}
                            </div>
                            <div>🕐 Waktu: {reg_time}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Informasi Alur
    st.markdown("""
    <div style="background: rgba(5,150,105,0.05); border: 1px solid rgba(74,222,128,0.1); 
         border-radius: 12px; padding: 16px; margin-top: 12px; font-size: 0.8rem; color: #86EFAC;">
        <div style="font-weight: 600; color: #4ADE80; margin-bottom: 10px;">ℹ️ Alur Rantai Pasok</div>
        <div style="line-height: 2;">
            🌱 Varietas Benih (Penangkar)<br>
            &nbsp;&nbsp;-&gt;<br>
            🗺️ Registrasi Lahan (Petani) [F2]<br>
            &nbsp;&nbsp;-&gt;<br>
            🌾 <strong style="color: #4ADE80;">Catat Panen (Petani) -- Anda di sini</strong><br>
            &nbsp;&nbsp;-&gt;<br>
            📦 Agregasi Pengepul [F4]<br>
            &nbsp;&nbsp;-&gt;<br>
            🏭 Agregasi Perusahaan [F5]
        </div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# PANEL DAFTAR SEMUA BATCH PANEN (Full Width)
# ============================================================
st.markdown("---")
st.markdown("""
<div style="font-family: 'Space Grotesk', sans-serif; font-size: 1.2rem; font-weight: 700;
     color: #4ADE80; margin-bottom: 16px;">
    📋 Daftar Semua Batch Panen
</div>
""", unsafe_allow_html=True)

col_ref3, col_cnt3, col_flt3 = st.columns([1, 2, 2])
with col_ref3:
    refresh_panen = st.button("🔄 Muat / Refresh", key="btn_refresh_panen")
with col_flt3:
    filter_panen_saya = st.checkbox("👤 Batch Saya Saja", key="chk_panen_saya")

if refresh_panen or st.session_state.get('panen_list_loaded'):
    if st.session_state.get('ganache_connected'):
        try:
            contracts = st.session_state.contracts
            traceability = contracts['Traceability']

            if filter_panen_saya and st.session_state.get('wallet_address'):
                from web3 import Web3
                my_addr = Web3.to_checksum_address(st.session_state.wallet_address)
                all_ids = traceability.functions.getMyHarvestBatches(my_addr).call()
                filter_label = "milik wallet Anda"
            else:
                all_ids = traceability.functions.getAllHarvestBatchIds().call()
                filter_label = "seluruh blockchain"

            total = traceability.functions.getTotalHarvestBatches().call()
            st.session_state['panen_list_loaded'] = True

            with col_cnt3:
                st.markdown(f"""
                <div style="background: rgba(5,150,105,0.08); border: 1px solid rgba(52,211,153,0.2);
                     border-radius: 10px; padding: 10px 16px; font-size: 0.85rem; color: #86EFAC;">
                    📊 Ditampilkan ({filter_label}): <strong style="color: #4ADE80;">{len(all_ids)}</strong>
                    &nbsp;|&nbsp; Total: <strong>{total}</strong>
                </div>
                """, unsafe_allow_html=True)

            if not all_ids:
                st.info("📭 Belum ada batch panen yang terdaftar.")
            else:
                rows = []
                for bid in all_ids:
                    try:
                        data = traceability.functions.getHarvestBatchDetail(bid).call()
                        id_b, id_l, qty, is_ferm, petani, is_agg, ts = data
                        rows.append({
                            "ID Batch": id_b,
                            "ID Lahan": id_l,
                            "Qty (Kg)": f"{qty:,}",
                            "Fermentasi": "Ya" if is_ferm else "Tidak",
                            "Status": "Diagregasi" if is_agg else "Tersedia",
                            "Petani": f"{petani[:8]}...{petani[-4:]}",
                            "Waktu": datetime.fromtimestamp(ts).strftime("%d %b %Y"),
                        })
                    except Exception:
                        rows.append({"ID Batch": bid, "ID Lahan": "-", "Qty (Kg)": "-",
                                     "Fermentasi": "-", "Status": "Error", "Petani": "-", "Waktu": "-"})

                import pandas as pd
                df = pd.DataFrame(rows)

                def highlight_status(val):
                    if val == "Diagregasi":
                        return "color: #FCD34D"
                    elif val == "Tersedia":
                        return "color: #4ADE80"
                    return ""

                st.dataframe(df, use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"❌ Gagal memuat daftar batch panen: {str(e)}")
    else:
        st.warning("⚠️ Tidak terhubung ke blockchain.")

