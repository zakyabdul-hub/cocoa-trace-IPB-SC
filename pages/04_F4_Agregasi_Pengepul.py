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

from config import build_transaction

# Path setup
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from style_adminhmd import inject_adminhmd_theme

# ============================================================
# KONFIGURASI HALAMAN
# ============================================================
st.set_page_config(
    page_title="F4 — Agregasi Pengepul | CacaoTrace",
    page_icon="📦",
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
    if st.session_state.get('role') != "Pengepul":
        st.error(f"🚫 Akses Ditolak! Halaman ini hanya untuk **Pengepul**.")
        st.page_link("app.py", label="← Kembali ke Dashboard", icon="🏠")
        return False
    return True

# ============================================================
# FUNGSI HELPER
# ============================================================
def validasi_sumber(batch_ids: list, tingkat_tujuan: int) -> dict:
    """Validasi sumber panen (jika tingkat_tujuan <= 1) atau sumber agregasi (jika tingkat_tujuan >= 2)."""
    if not st.session_state.get('ganache_connected'):
        return {}
    results = {}
    contracts = st.session_state.contracts
    traceability = contracts['Traceability']
    
    for bid in batch_ids:
        bid = bid.strip()
        if not bid:
            continue
        try:
            if tingkat_tujuan <= 1:
                # Sumber harus BatchPanen
                data = traceability.functions.dataPanen(bid).call()
                _, _, qty, is_ferm, _, is_agg, ts = data
                results[bid] = {
                    'exists': ts != 0,
                    'is_aggregated': is_agg,
                    'qty': qty,
                    'valid': ts != 0 and not is_agg,
                    'reason': "✅ Valid" if (ts != 0 and not is_agg) else ("sudah diagregasi" if is_agg else "belum terdaftar")
                }
            else:
                # Sumber harus BatchAgregasi
                data = traceability.functions.dataAgregasi(bid).call()
                id_b, tingkat_sumber, qty, mutu, pemilik, is_agg, ts = data
                
                # Cek validitas route dari tingkat_sumber ke tingkat_tujuan
                route_valid = traceability.functions.isValidRoute(tingkat_sumber, tingkat_tujuan).call()
                
                valid = (ts != 0) and (not is_agg) and route_valid
                results[bid] = {
                    'exists': ts != 0,
                    'is_aggregated': is_agg,
                    'qty': qty,
                    'valid': valid,
                    'reason': (
                        "✅ Valid" if valid else
                        "belum terdaftar" if ts == 0 else
                        "sudah diagregasi" if is_agg else
                        f"jalur tidak valid (level sumber: {tingkat_sumber})"
                    )
                }
        except Exception as e:
            results[bid] = {'exists': False, 'valid': False, 'reason': f"Error: {e}"}
    return results

# Top Navbar Header
st.markdown("""
<div class="admin-topbar">
    <div class="admin-topbar-title">
        <span style="font-size: 1.5rem;">📦</span> F4 — Agregasi Batch Pengepul (Level 0 - 4)
    </div>
    <div class="admin-topbar-meta">
        <span class="admin-badge badge-pengepul">Aktor: Pengepul</span>
        <span class="admin-badge badge-connected">Traceability.createCollectorBatch()</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Page Header
st.markdown("""
<div class="admin-page-header">
    <h1>Agregasi Batch Pengepul Berjenjang</h1>
    <p>Penggabungan beberapa batch panen atau agregasi sebelumnya menjadi batch pengepul baru dengan validasi rute otomatis.</p>
</div>
""", unsafe_allow_html=True)

if not check_auth():
    st.stop()

# ============================================================
# SESSION STATE untuk batch list & ID Generator
# ============================================================
if 'selected_batches' not in st.session_state:
    st.session_state.selected_batches = []
if 'batch_validation' not in st.session_state:
    st.session_state.batch_validation = {}
if 'selected_tingkat_pengepul' not in st.session_state:
    st.session_state.selected_tingkat_pengepul = 0
if 'generated_id_pengepul' not in st.session_state:
    st.session_state.generated_id_pengepul = ""
if 'prefilled_nama_pengepul' not in st.session_state:
    st.session_state.prefilled_nama_pengepul = ""

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
    
    # BAGIAN 0: Pilih Tingkat Pengepul
    st.markdown("**📊 Tingkat Proses Agregasi**")
    tingkat_label_options = {
        "Kelompok Tani (Level 0)": 0,
        "Pengepul Desa (Level 1)": 1,
        "Pengepul Kecamatan (Level 2)": 2,
        "Pengepul Kabupaten (Level 3)": 3,
        "Pengepul Luar Kabupaten (Level 4)": 4,
    }
    
    current_tingkat = st.selectbox(
        "Pilih Tingkatan Batch Baru *",
        options=list(tingkat_label_options.keys()),
        index=st.session_state.selected_tingkat_pengepul
    )
    tingkat_val = tingkat_label_options[current_tingkat]
    
    # Reset jika tingkatan berubah
    if tingkat_val != st.session_state.selected_tingkat_pengepul:
        st.session_state.selected_tingkat_pengepul = tingkat_val
        st.session_state.selected_batches = []
        st.session_state.batch_validation = {}
        st.session_state.generated_id_pengepul = ""
        st.rerun()

    st.markdown("**📋 Informasi Batch Pengepul Baru**")
    col_gen_name, col_gen_date = st.columns(2)
    with col_gen_name:
        g_nama = st.text_input("Nama Entitas / Kelompok / Pengepul *", placeholder="Contoh: CV_JAYA_MAJU", key="g_pengepul_nama")
    with col_gen_date:
        g_date = st.date_input("Tanggal Input *", value=datetime.today(), key="g_pengepul_date")

    # Dynamic real-time sequence and ID calculation
    id_batch_baru = ""
    seq = ""
    if g_nama.strip():
        from config import ID_PREFIX
        from utils import get_next_sequence_batch, generate_agregasi_id, normalize_name
        prefix = ID_PREFIX[tingkat_val]
        ddmmyy = g_date.strftime("%d%m%y")
        search_prefix = f"{prefix}-{normalize_name(g_nama.strip())}-{ddmmyy}-"
        
        if st.session_state.get('ganache_connected'):
            traceability = st.session_state.contracts['Traceability']
            seq = get_next_sequence_batch(traceability, tingkat_val, search_prefix)
            id_batch_baru = generate_agregasi_id(prefix, g_nama.strip(), ddmmyy, seq)
        else:
            id_batch_baru = f"{prefix}-{normalize_name(g_nama.strip())}-{ddmmyy}-001"

    col_id, col_qty = st.columns(2)
    with col_id:
        st.text_input(
            "🏷️ ID Batch Pengepul Baru (Otomatis) *",
            value=id_batch_baru,
            disabled=True,
            help="ID unik untuk batch agregasi pengepul ini yang dihasilkan secara otomatis."
        )
    with col_qty:
        total_qty = st.number_input(
            "⚖️ Total Kuantitas (Kg) *",
            min_value=1,
            max_value=1_000_000,
            value=1000,
            step=50,
            help="Total bobot kakao setelah diaregasi"
        )
    if seq:
        st.caption(f"ℹ️ Nomor Urut Batch terdeteksi di blockchain: **#{seq}**")

    st.markdown("---")
    
    # BAGIAN 3: Pilih Batch Sumber
    st.markdown("**🌾 Pilih Batch Sumber**")
    st.caption("Pilih batch sumber yang valid untuk tingkatan ini dan lakukan validasi.")

    # Ambil daftar batch sumber yang tersedia berdasarkan level
    available_batches = []
    if st.session_state.get('ganache_connected'):
        try:
            traceability = st.session_state.contracts['Traceability']
            
            if tingkat_val <= 1:
                # Sumber harus dari BatchPanen (Level Petani)
                all_ids = traceability.functions.getAllHarvestBatchIds().call()
                for bid in all_ids:
                    try:
                        bdata = traceability.functions.getHarvestBatchDetail(bid).call()
                        if not bdata[5] and bid not in st.session_state.selected_batches: # is_aggregated == False
                            available_batches.append(bid)
                    except Exception:
                        pass
            else:
                # Sumber harus dari BatchAgregasi
                # Tentukan level sumber yang valid berdasarkan VALID_ROUTES
                from config import VALID_ROUTES
                source_levels = []
                for lvl, targets in VALID_ROUTES.items():
                    if tingkat_val in targets:
                        source_levels.append(lvl)
                        
                for s_lvl in source_levels:
                    all_s_ids = traceability.functions.getBatchIdsByLevel(s_lvl).call()
                    for bid in all_s_ids:
                        try:
                            bdata = traceability.functions.getAgregasiBatchDetail(bid).call()
                            if not bdata[5] and bid not in st.session_state.selected_batches: # is_aggregated == False
                                available_batches.append(bid)
                        except Exception:
                            pass
        except Exception:
            pass
            
    col_add, col_btn = st.columns([4, 1])
    with col_add:
        new_batch_input = st.selectbox(
            "Tambah Batch Sumber",
            options=[""] + available_batches,
            format_func=lambda x: "Pilih Batch Sumber Tersedia..." if x == "" else x,
            key="new_batch_add",
            label_visibility="collapsed",
            disabled=len(available_batches) == 0
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
                        reason = vd.get('reason', 'tidak valid')
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
                    results = validasi_sumber(st.session_state.selected_batches, tingkat_val)
                    st.session_state.batch_validation = results
                    st.rerun()
        with col_clr:
            if st.button("🗑️ Bersihkan Semua", key="btn_clear_all"):
                st.session_state.selected_batches = []
                st.session_state.batch_validation = {}
                st.rerun()
    else:
        st.info("📋 Belum ada batch sumber yang dipilih. Tambahkan ID Batch di atas.")
    
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
            st.error("❌ Pilih minimal 1 Batch sebagai sumber.")
        elif not st.session_state.get('private_key'):
            st.error("❌ Private Key belum diinput!")
        else:
            with st.spinner("⏳ Mengirim transaksi agregasi ke blockchain..."):
                try:
                    w3 = st.session_state.w3
                    contracts = st.session_state.contracts
                    traceability = contracts['Traceability']
                    
                    batch_list = [b.strip() for b in st.session_state.selected_batches]
                    
                    # Bangun parameter dual source:
                    # tingkat <= 1 -> panenSources = batch_list, agregasiSources = []
                    # tingkat >= 2 -> panenSources = [], agregasiSources = batch_list
                    if tingkat_val <= 1:
                        panen_sources = batch_list
                        agregasi_sources = []
                    else:
                        panen_sources = []
                        agregasi_sources = batch_list
                        
                    contract_func = traceability.functions.createCollectorBatch(
                        id_batch_baru.strip(),
                        panen_sources,
                        agregasi_sources,
                        int(tingkat_val),
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
                                <tr><td style="color: #FCD34D; padding: 3px 0;">📊 Tingkat Proses</td><td>{current_tingkat}</td></tr>
                                <tr><td style="color: #FCD34D; padding: 3px 0;">🔗 TX Hash</td>
                                    <td style="font-family: monospace; font-size: 0.7rem;">{result['tx_hash'][:24]}...{result['tx_hash'][-8:]}</td>
                                </tr>
                            </table>
                        </div>
                        """, unsafe_allow_html=True)
                        # Reset state
                        st.session_state.selected_batches = []
                        st.session_state.batch_validation = {}
                        st.session_state.generated_id_pengepul = ""
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
    📋 Daftar Semua Batch Pengepul (Level 0 s.d 4)
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
            st.session_state['pengepul_list_loaded'] = True
            
            # Setup 5 tabs untuk tingkatan Pengepul
            tabs = st.tabs([
                "Kelompok Tani (L0)", 
                "Pengepul Desa (L1)", 
                "Kecamatan (L2)", 
                "Kabupaten (L3)", 
                "Luar Kabupaten (L4)"
            ])
            
            for tab_idx, tab in enumerate(tabs):
                with tab:
                    if filter_pengepul_saya and st.session_state.get('wallet_address'):
                        from web3 import Web3
                        my_addr = Web3.to_checksum_address(st.session_state.wallet_address)
                        all_ids_raw = traceability.functions.getMyAgregasiBatches(my_addr).call()
                        all_ids = []
                        for bid in all_ids_raw:
                            try:
                                data = traceability.functions.dataAgregasi(bid).call()
                                if data[1] == tab_idx:
                                    all_ids.append(bid)
                            except Exception:
                                pass
                        filter_label = "milik wallet Anda"
                    else:
                        all_ids = traceability.functions.getBatchIdsByLevel(tab_idx).call()
                        filter_label = "seluruh blockchain"

                    total = len(all_ids)
                    
                    st.caption(f"📊 Ditampilkan ({filter_label}): {total} batch")
                    
                    if not all_ids:
                        st.info(f"📭 Belum ada batch terdaftar di tingkatan ini.")
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

