"""
04_F4_Agregasi_Pengepul.py
Fitur F4: Agregasi Batch Petani ke Pengepul
Aktor: Pengepul
Smart Contract: Traceability.createCollectorBatch()
"""

import streamlit as st
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import build_transaction

# ============================================================
# KONFIGURASI HALAMAN
# ============================================================
st.set_page_config(
    page_title="F4 — Agregasi Pengepul | CacaoTrace",
    page_icon="📦",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
.stApp { background: linear-gradient(135deg, #0F0A00 0%, #0A0700 100%) !important; color: #FFFBEB !important; }
[data-testid="stSidebar"] { background: #0A0700 !important; border-right: 1px solid rgba(245,158,11,0.2) !important; }
.page-header {
    background: linear-gradient(135deg, rgba(217,119,6,0.15) 0%, rgba(245,158,11,0.08) 100%);
    border: 1px solid rgba(245,158,11,0.2); border-radius: 20px; padding: 32px; margin-bottom: 24px;
    border-left: 4px solid #D97706;
}
.form-card {
    background: rgba(217,119,6,0.05); border: 1px solid rgba(245,158,11,0.15);
    border-radius: 16px; padding: 28px; margin: 12px 0;
}
.batch-chip {
    display: inline-block; margin: 4px; padding: 4px 12px;
    background: rgba(217,119,6,0.15); border: 1px solid rgba(245,158,11,0.3);
    border-radius: 20px; font-size: 0.75rem; color: #FCD34D;
}
.batch-chip.valid { border-color: rgba(52,211,153,0.5); color: #34D399; background: rgba(5,150,105,0.1); }
.batch-chip.invalid { border-color: rgba(239,68,68,0.5); color: #F87171; background: rgba(239,68,68,0.08); }
.tx-success {
    background: linear-gradient(135deg, rgba(217,119,6,0.15), rgba(245,158,11,0.08));
    border: 1px solid rgba(245,158,11,0.4); border-radius: 12px; padding: 20px;
}
.stTextInput > div > div > input, .stNumberInput > div > div > input {
    background: rgba(217,119,6,0.05) !important; border: 1px solid rgba(245,158,11,0.2) !important;
    border-radius: 10px !important; color: #FFFBEB !important;
}
.stButton > button {
    background: linear-gradient(135deg, #D97706, #F59E0B) !important; color: #0A0700 !important;
    border: none !important; border-radius: 10px !important; font-weight: 700 !important;
    padding: 0.6rem 2rem !important; transition: all 0.3s !important;
}
.stButton > button:hover { transform: translateY(-2px) !important; box-shadow: 0 8px 24px rgba(245,158,11,0.3) !important; }
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
    if st.session_state.get('role') != "Pengepul":
        st.error(f"🚫 Akses Ditolak! Halaman ini hanya untuk **Pengepul**.")
        st.page_link("app.py", label="← Kembali ke Dashboard", icon="🏠")
        return False
    return True

# ============================================================
# FUNGSI HELPER
# ============================================================
def validasi_batch_panen(batch_ids: list) -> dict:
    """Memvalidasi daftar ID Batch Panen ke blockchain."""
    if not st.session_state.get('ganache_connected'):
        return {}
    
    results = {}
    contracts = st.session_state.contracts
    for bid in batch_ids:
        bid = bid.strip()
        if not bid:
            continue
        try:
            data = contracts['Traceability'].functions.dataPanen(bid).call()
            _, _, qty, is_ferm, _, is_agg, ts = data
            results[bid] = {
                'exists': ts != 0,
                'is_aggregated': is_agg,
                'qty': qty,
                'is_fermented': is_ferm,
                'valid': ts != 0 and not is_agg,
            }
        except Exception:
            results[bid] = {'exists': False, 'valid': False}
    return results

# ============================================================
# HEADER
# ============================================================
st.markdown("""
<div class="page-header">
    <div style="font-size: 2rem; margin-bottom: 8px;">📦</div>
    <div style="font-family: 'Space Grotesk', sans-serif; font-size: 1.8rem; font-weight: 700; color: #FCD34D;">
        F4 — Agregasi Batch Pengepul
    </div>
    <div style="color: #FDE68A; font-size: 0.95rem; margin-top: 8px;">
        Menggabungkan beberapa Batch Panen dari Petani menjadi satu Batch Pengepul. 
        Sistem memvalidasi setiap batch (tidak boleh sudah diagregasi/double-spending).
    </div>
    <div style="margin-top: 12px; font-size: 0.75rem; color: #FCD34D;">
        📋 Smart Contract: <code style="background: rgba(245,158,11,0.1); padding: 2px 8px; border-radius: 4px;">Traceability.createCollectorBatch()</code>
        &nbsp;|&nbsp; 👤 Aktor: <strong>Pengepul</strong>
    </div>
</div>
""", unsafe_allow_html=True)

if not check_auth():
    st.stop()

# ============================================================
# SESSION STATE untuk batch list
# ============================================================
if 'selected_batches' not in st.session_state:
    st.session_state.selected_batches = []
if 'batch_validation' not in st.session_state:
    st.session_state.batch_validation = {}

# ============================================================
# LAYOUT
# ============================================================
col_form, col_batch = st.columns([5, 3], gap="large")

with col_form:
    st.markdown('<div class="form-card">', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-family: 'Space Grotesk', sans-serif; font-size: 1.1rem; font-weight: 600; 
         color: #FCD34D; margin-bottom: 20px;">📝 Form Agregasi Pengepul</div>
    """, unsafe_allow_html=True)
    
    # BAGIAN 1: Info Batch Pengepul
    st.markdown("**📋 Informasi Batch Pengepul Baru**")
    col_id, col_qty = st.columns(2)
    with col_id:
        id_batch_baru = st.text_input(
            "🏷️ ID Batch Pengepul Baru *",
            placeholder="COL-POLMAN-001",
            help="ID unik untuk batch agregasi pengepul ini"
        )
    with col_qty:
        total_qty = st.number_input(
            "⚖️ Total Kuantitas (Kg) *",
            min_value=1,
            max_value=1_000_000,
            value=1000,
            step=50,
            help="Total bobot kakao yang diaregasi"
        )
    
    st.markdown("---")
    
    # BAGIAN 2: Pilih Batch Panen Sumber
    st.markdown("**🌾 Pilih Batch Panen Sumber**")
    st.caption("Tambahkan ID Batch Panen satu per satu dan validasi sebelum submit.")
    
    col_add, col_btn = st.columns([4, 1])
    with col_add:
        new_batch_input = st.text_input(
            "Tambah ID Batch Panen",
            placeholder="BTC-PETANI-001",
            key="new_batch_add",
            label_visibility="collapsed"
        )
    with col_btn:
        if st.button("➕ Tambah", key="btn_tambah_batch"):
            bid = new_batch_input.strip()
            if bid and bid not in st.session_state.selected_batches:
                st.session_state.selected_batches.append(bid)
                st.rerun()
            elif bid in st.session_state.selected_batches:
                st.warning(f"ID `{bid}` sudah ada dalam daftar.")
    
    # Tampilkan daftar batch yang dipilih
    if st.session_state.selected_batches:
        st.markdown("**Daftar Batch Terpilih:**")
        batch_to_remove = None
        for i, bid in enumerate(st.session_state.selected_batches):
            col_b, col_r = st.columns([5, 1])
            with col_b:
                vd = st.session_state.batch_validation.get(bid, {})
                if vd:
                    if vd.get('valid'):
                        qty_info = f" ({vd.get('qty',0):,} Kg)"
                        st.markdown(f'<span class="batch-chip valid">✅ {bid}{qty_info}</span>', unsafe_allow_html=True)
                    else:
                        reason = "tidak ada" if not vd.get('exists') else "sudah diagregasi"
                        st.markdown(f'<span class="batch-chip invalid">❌ {bid} ({reason})</span>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<span class="batch-chip">⏳ {bid}</span>', unsafe_allow_html=True)
            with col_r:
                if st.button("🗑️", key=f"rm_{i}_{bid}", help=f"Hapus {bid}"):
                    batch_to_remove = bid
        
        if batch_to_remove:
            st.session_state.selected_batches.remove(batch_to_remove)
            if batch_to_remove in st.session_state.batch_validation:
                del st.session_state.batch_validation[batch_to_remove]
            st.rerun()
        
        col_vld, col_clr = st.columns(2)
        with col_vld:
            if st.button("🔍 Validasi Semua Batch", key="btn_validasi"):
                with st.spinner("Memvalidasi ke blockchain..."):
                    results = validasi_batch_panen(st.session_state.selected_batches)
                    st.session_state.batch_validation = results
                    st.rerun()
        with col_clr:
            if st.button("🗑️ Bersihkan Semua", key="btn_clear_all"):
                st.session_state.selected_batches = []
                st.session_state.batch_validation = {}
                st.rerun()
    else:
        st.info("📋 Belum ada batch panen yang dipilih. Tambahkan ID Batch Panen di atas.")
    
    st.markdown("---")
    
    # TOMBOL SUBMIT
    all_valid = (
        len(st.session_state.selected_batches) > 0 and
        all(st.session_state.batch_validation.get(b, {}).get('valid', False) 
            for b in st.session_state.selected_batches)
    )
    
    if st.session_state.batch_validation and not all_valid:
        st.warning("⚠️ Ada batch yang tidak valid atau belum divalidasi. Pastikan semua batch valid sebelum submit.")
    
    st.markdown(f"""
    <div style="font-size: 0.8rem; color: #FDE68A; margin-bottom: 12px;">
        🔑 Transaksi dari: <code>{st.session_state.get('wallet_address', 'N/A')[:20]}...</code>
    </div>
    """, unsafe_allow_html=True)
    
    submit_disabled = not (id_batch_baru and len(st.session_state.selected_batches) > 0)
    
    if st.button(
        f"📦 Buat Batch Pengepul ({len(st.session_state.selected_batches)} batch sumber)",
        key="btn_submit_agregasi",
        use_container_width=True,
        disabled=submit_disabled
    ):
        if not id_batch_baru.strip():
            st.error("❌ ID Batch Pengepul wajib diisi.")
        elif len(st.session_state.selected_batches) == 0:
            st.error("❌ Pilih minimal 1 Batch Panen sebagai sumber.")
        elif not st.session_state.get('private_key'):
            st.error("❌ Private Key belum diinput!")
        else:
            with st.spinner("⏳ Mengirim transaksi agregasi ke blockchain..."):
                try:
                    w3 = st.session_state.w3
                    contracts = st.session_state.contracts
                    traceability = contracts['Traceability']
                    
                    batch_list = [b.strip() for b in st.session_state.selected_batches]
                    
                    contract_func = traceability.functions.createCollectorBatch(
                        id_batch_baru.strip(),
                        batch_list,
                        int(total_qty)
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
                            <div style="font-size: 1.2rem; color: #FCD34D; margin-bottom: 12px;">✅ Batch Pengepul Berhasil Dibuat!</div>
                            <table style="font-size: 0.8rem; color: #FDE68A; width: 100%;">
                                <tr><td style="color: #FCD34D; padding: 3px 0;">📦 ID Batch Pengepul</td><td><strong>{id_batch_baru}</strong></td></tr>
                                <tr><td style="color: #FCD34D; padding: 3px 0;">🌾 Jumlah Batch Sumber</td><td><strong>{len(batch_list)} Batch</strong></td></tr>
                                <tr><td style="color: #FCD34D; padding: 3px 0;">⚖️ Total Kuantitas</td><td><strong>{total_qty:,} Kg</strong></td></tr>
                                <tr><td style="color: #FCD34D; padding: 3px 0;">📊 Tingkat Proses</td><td>Pengepul (Level 0)</td></tr>
                                <tr><td style="color: #FCD34D; padding: 3px 0;">🔗 TX Hash</td>
                                    <td style="font-family: monospace; font-size: 0.7rem;">{result['tx_hash'][:24]}...{result['tx_hash'][-8:]}</td>
                                </tr>
                            </table>
                        </div>
                        """, unsafe_allow_html=True)
                        # Reset state
                        st.session_state.selected_batches = []
                        st.session_state.batch_validation = {}
                        st.balloons()
                    else:
                        st.error(f"❌ Transaksi Gagal: {result['error']}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    st.markdown("</div>", unsafe_allow_html=True)

with col_batch:
    # Panel Ringkasan
    st.markdown("""
    <div class="form-card">
        <div style="font-family: 'Space Grotesk', sans-serif; font-size: 1rem; font-weight: 600; 
             color: #FCD34D; margin-bottom: 16px;">📊 Ringkasan Agregasi</div>
    """, unsafe_allow_html=True)
    
    total_valid = sum(1 for b in st.session_state.selected_batches 
                      if st.session_state.batch_validation.get(b, {}).get('valid', False))
    total_invalid = len(st.session_state.selected_batches) - total_valid
    total_qty_calculated = sum(
        st.session_state.batch_validation.get(b, {}).get('qty', 0) 
        for b in st.session_state.selected_batches 
        if st.session_state.batch_validation.get(b, {}).get('valid', False)
    )
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.metric("Total Batch", len(st.session_state.selected_batches))
    with col_m2:
        st.metric("Batch Valid", total_valid, delta=f"-{total_invalid} invalid" if total_invalid > 0 else None)
    
    if total_qty_calculated > 0:
        st.metric("Est. Qty dari Blockchain", f"{total_qty_calculated:,} Kg")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Panel Cek Batch Pengepul
    st.markdown("""
    <div class="form-card" style="margin-top: 12px;">
        <div style="font-family: 'Space Grotesk', sans-serif; font-size: 1rem; font-weight: 600; 
             color: #FCD34D; margin-bottom: 16px;">🔍 Cek Batch Pengepul</div>
    """, unsafe_allow_html=True)
    
    check_col_id = st.text_input("ID Batch Pengepul", placeholder="COL-POLMAN-001", key="check_col")
    
    if st.button("🔍 Cek", key="btn_check_col"):
        if check_col_id.strip() and st.session_state.get('ganache_connected'):
            try:
                contracts = st.session_state.contracts
                data = contracts['Traceability'].functions.dataAgregasi(check_col_id.strip()).call()
                # ABI returns: idBatchBaru, tingkat, totalQty, parameterMutu, pemilik, isAggregated, timestamp
                id_b, tingkat, qty, mutu, pemilik, is_agg, ts = data
                
                if ts == 0:
                    st.warning(f"⚠️ Batch `{check_col_id}` belum terdaftar.")
                else:
                    from config import TINGKAT_PROSES_MAP
                    reg_time = datetime.fromtimestamp(ts).strftime("%d %b %Y, %H:%M")
                    agg_str = "🔒 Sudah Diagregasi" if is_agg else "🟢 Tersedia"
                    
                    # Ambil sumber
                    sumber = contracts['Traceability'].functions.getSumberAgregasi(check_col_id.strip()).call()
                    
                    st.markdown(f"""
                    <div style="background: rgba(217,119,6,0.05); border: 1px solid rgba(245,158,11,0.15); 
                         border-radius: 12px; padding: 14px; font-size: 0.78rem; color: #FDE68A;">
                        <div style="color: #FCD34D; font-weight: 600; margin-bottom: 8px;">✅ Batch Ditemukan</div>
                        <div>📦 ID: <strong>{id_b}</strong></div>
                        <div>📊 Tingkat: {TINGKAT_PROSES_MAP.get(tingkat, 'Unknown')}</div>
                        <div>⚖️ Qty: <strong>{qty:,} Kg</strong></div>
                        <div>🔧 Mutu: {mutu}</div>
                        <div>📋 Sumber ({len(sumber)} batch):</div>
                        <div style="margin-left: 12px; font-family: monospace; font-size: 0.7rem;">
                            {"<br>".join(f"• {s}" for s in sumber[:5])}
                            {"..." if len(sumber) > 5 else ""}
                        </div>
                        <div>📊 Status: {agg_str}</div>
                        <div>🕐 Waktu: {reg_time}</div>
                    </div>
                    """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error: {str(e)}")

    st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# PANEL DAFTAR SEMUA BATCH PENGEPUL (Full Width)
# ============================================================
st.markdown("---")
st.markdown("""
<div style="font-family: 'Space Grotesk', sans-serif; font-size: 1.2rem; font-weight: 700;
     color: #FCD34D; margin-bottom: 16px;">
    📋 Daftar Semua Batch Pengepul (Level 0)
</div>
""", unsafe_allow_html=True)

col_ref4, col_cnt4, col_flt4 = st.columns([1, 2, 2])
with col_ref4:
    refresh_pengepul = st.button("🔄 Muat / Refresh", key="btn_refresh_pengepul")
with col_flt4:
    filter_pengepul_saya = st.checkbox("👤 Batch Saya Saja", key="chk_pengepul_saya")

if refresh_pengepul or st.session_state.get('pengepul_list_loaded'):
    if st.session_state.get('ganache_connected'):
        try:
            contracts = st.session_state.contracts
            traceability = contracts['Traceability']

            if filter_pengepul_saya and st.session_state.get('wallet_address'):
                from web3 import Web3
                my_addr = Web3.to_checksum_address(st.session_state.wallet_address)
                all_ids = traceability.functions.getMyAgregasiBatches(my_addr).call()
                # Filter hanya level 0 (Pengepul)
                filtered = []
                for bid in all_ids:
                    try:
                        data = traceability.functions.dataAgregasi(bid).call()
                        if data[1] == 0:  # tingkat == 0 (Pengepul)
                            filtered.append(bid)
                    except Exception:
                        pass
                all_ids = filtered
                filter_label = "milik wallet Anda"
            else:
                all_ids = traceability.functions.getBatchIdsByLevel(0).call()
                filter_label = "seluruh blockchain"

            total = traceability.functions.getTotalBatchByLevel(0).call()
            st.session_state['pengepul_list_loaded'] = True

            with col_cnt4:
                st.markdown(f"""
                <div style="background: rgba(217,119,6,0.08); border: 1px solid rgba(245,158,11,0.2);
                     border-radius: 10px; padding: 10px 16px; font-size: 0.85rem; color: #FDE68A;">
                    📊 Ditampilkan ({filter_label}): <strong style="color: #FCD34D;">{len(all_ids)}</strong>
                    &nbsp;|&nbsp; Total: <strong>{total}</strong>
                </div>
                """, unsafe_allow_html=True)

            if not all_ids:
                st.info("📭 Belum ada batch pengepul yang terdaftar.")
            else:
                from config import TINGKAT_PROSES_MAP
                rows = []
                for bid in all_ids:
                    try:
                        data = traceability.functions.dataAgregasi(bid).call()
                        id_b, tingkat, qty, mutu, pemilik, is_agg, ts = data
                        sumber = traceability.functions.getSumberAgregasi(bid).call()
                        rows.append({
                            "ID Batch": id_b,
                            "Tingkat": TINGKAT_PROSES_MAP.get(tingkat, "?"),
                            "Total Qty (Kg)": f"{qty:,}",
                            "Jml Sumber": len(sumber),
                            "Status": "Diagregasi" if is_agg else "Tersedia",
                            "Pemilik": f"{pemilik[:8]}...{pemilik[-4:]}",
                            "Waktu": datetime.fromtimestamp(ts).strftime("%d %b %Y"),
                        })
                    except Exception:
                        rows.append({"ID Batch": bid, "Tingkat": "-", "Total Qty (Kg)": "-",
                                     "Jml Sumber": "-", "Status": "Error", "Pemilik": "-", "Waktu": "-"})

                import pandas as pd
                df = pd.DataFrame(rows)
                st.dataframe(df, use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"❌ Gagal memuat daftar batch pengepul: {str(e)}")
    else:
        st.warning("⚠️ Tidak terhubung ke blockchain.")

