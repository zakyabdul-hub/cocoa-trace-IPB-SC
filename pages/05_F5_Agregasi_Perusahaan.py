"""
05_F5_Agregasi_Perusahaan.py
Fitur F5: Agregasi Batch Perusahaan
Aktor: Perusahaan
Smart Contract: Traceability.createCompanyBatch()
Tingkat: 1=GudangKab, 2=GudangPelabuhan, 3=Pusat
"""

import streamlit as st
import sys
import os
from datetime import datetime

from config import build_transaction, TINGKAT_PROSES_MAP, TINGKAT_LABEL_MAP

# ============================================================
# KONFIGURASI HALAMAN
# ============================================================
st.set_page_config(
    page_title="F5 — Agregasi Perusahaan | CacaoTrace",
    page_icon="🏭",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
.stApp { background: linear-gradient(135deg, #120008 0%, #0D0006 100%) !important; color: #FFF5F7 !important; }
[data-testid="stSidebar"] { background: #0D0006 !important; border-right: 1px solid rgba(220,38,38,0.2) !important; }
.page-header {
    background: linear-gradient(135deg, rgba(220,38,38,0.15) 0%, rgba(239,68,68,0.08) 100%);
    border: 1px solid rgba(220,38,38,0.2); border-radius: 20px; padding: 32px; margin-bottom: 24px;
    border-left: 4px solid #DC2626;
}
.form-card {
    background: rgba(220,38,38,0.04); border: 1px solid rgba(220,38,38,0.12);
    border-radius: 16px; padding: 28px; margin: 12px 0;
}
.hierarchy-card {
    background: rgba(220,38,38,0.06); border: 1px solid rgba(220,38,38,0.15);
    border-radius: 12px; padding: 16px; text-align: center;
    transition: all 0.3s ease;
}
.hierarchy-card.active {
    background: rgba(220,38,38,0.15); border: 2px solid rgba(220,38,38,0.5);
    box-shadow: 0 0 20px rgba(220,38,38,0.2);
}
.batch-chip { display: inline-block; margin: 4px; padding: 4px 12px;
    background: rgba(220,38,38,0.1); border: 1px solid rgba(239,68,68,0.3);
    border-radius: 20px; font-size: 0.75rem; color: #FCA5A5; }
.batch-chip.valid { border-color: rgba(52,211,153,0.5); color: #34D399; background: rgba(5,150,105,0.1); }
.batch-chip.invalid { border-color: rgba(239,68,68,0.6); color: #F87171; background: rgba(239,68,68,0.1); }
.tx-success {
    background: linear-gradient(135deg, rgba(220,38,38,0.12), rgba(239,68,68,0.06));
    border: 1px solid rgba(220,38,38,0.4); border-radius: 12px; padding: 20px;
}
.stTextInput > div > div > input, .stNumberInput > div > div > input, .stTextArea > div > div > textarea {
    background: rgba(220,38,38,0.04) !important; border: 1px solid rgba(220,38,38,0.2) !important;
    border-radius: 10px !important; color: #FFF5F7 !important;
}
.stButton > button {
    background: linear-gradient(135deg, #DC2626, #EF4444) !important; color: white !important;
    border: none !important; border-radius: 10px !important; font-weight: 700 !important;
    padding: 0.6rem 2rem !important; transition: all 0.3s !important;
}
.stButton > button:hover { transform: translateY(-2px) !important; box-shadow: 0 8px 24px rgba(239,68,68,0.3) !important; }
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
    if st.session_state.get('role') != "Perusahaan":
        st.error(f"🚫 Akses Ditolak! Halaman ini hanya untuk **Perusahaan**.")
        st.page_link("app.py", label="← Kembali ke Dashboard", icon="🏠")
        return False
    return True

# ============================================================
# FUNGSI HELPER
# ============================================================
def validasi_batch_agregasi_perusahaan(batch_ids: list, tingkat_tujuan: int) -> dict:
    """Validasi batch agregasi sumber untuk perusahaan menggunakan aturan VALID_ROUTES."""
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
            data = traceability.functions.dataAgregasi(bid).call()
            # ABI returns: idBatchBaru, tingkat, totalQty, parameterMutu, pemilik, isAggregated, timestamp
            id_b, tingkat_sumber, qty, mutu, pemilik, is_agg, ts = data
            
            exists = ts != 0
            route_valid = traceability.functions.isValidRoute(tingkat_sumber, tingkat_tujuan).call() if exists else False
            valid = exists and not is_agg and route_valid
            
            results[bid] = {
                'exists': exists,
                'is_aggregated': is_agg,
                'tingkat': tingkat_sumber,
                'qty': qty,
                'valid': valid,
                'reason': (
                    "✅ Valid" if valid else
                    "belum terdaftar" if not exists else
                    "sudah diagregasi" if is_agg else
                    f"jalur tidak valid (level sumber: {tingkat_sumber})"
                )
            }
        except Exception as e:
            results[bid] = {'exists': False, 'valid': False, 'reason': f"Error: {e}"}
    return results

# ============================================================
# HEADER
# ============================================================
st.markdown("""
<div class="page-header">
    <div style="font-size: 2rem; margin-bottom: 8px;">🏭</div>
    <div style="font-family: 'Space Grotesk', sans-serif; font-size: 1.8rem; font-weight: 700; color: #FCA5A5;">
        F5 — Agregasi Batch Perusahaan (Multi-Level)
    </div>
    <div style="color: #FECACA; font-size: 0.95rem; margin-top: 8px;">
        Pemrosesan agregasi perusahaan: GudangKab (L5) → GudangPelabuhan (L6) → Pusat (L7).
        Sistem memvalidasi rute ketertelusuran alur secara dinamis.
    </div>
    <div style="margin-top: 12px; font-size: 0.75rem; color: #FCA5A5;">
        📋 Smart Contract: <code style="background: rgba(220,38,38,0.1); padding: 2px 8px; border-radius: 4px;">Traceability.createCompanyBatch()</code>
        &nbsp;|&nbsp; 👤 Aktor: <strong>Perusahaan</strong>
    </div>
</div>
""", unsafe_allow_html=True)

if not check_auth():
    st.stop()

# ============================================================
# HIERARKI VISUAL
# ============================================================
st.markdown("**🏗️ Hierarki Rantai Pasok Perusahaan (Level 5-7):**")
col_h0, col_h1, col_h2, col_h3 = st.columns(4)

tingkat_options = {
    "GudangKab (Level 5)": 5,
    "GudangPelabuhan (Level 6)": 6,
    "Pusat (Level 7)": 7,
}

# ============================================================
# SESSION STATE
# ============================================================
if 'company_batches' not in st.session_state:
    st.session_state.company_batches = []
if 'company_batch_validation' not in st.session_state:
    st.session_state.company_batch_validation = {}
if 'selected_tingkat' not in st.session_state:
    st.session_state.selected_tingkat = 5
if 'generated_id_perusahaan' not in st.session_state:
    st.session_state.generated_id_perusahaan = ""
if 'prefilled_nama_perusahaan' not in st.session_state:
    st.session_state.prefilled_nama_perusahaan = ""

# ============================================================
# LAYOUT
# ============================================================
col_form, col_info = st.columns([5, 3], gap="large")

with col_form:
    st.markdown('<div class="form-card">', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-family: 'Space Grotesk', sans-serif; font-size: 1.1rem; font-weight: 600; 
         color: #FCA5A5; margin-bottom: 20px;">📝 Form Agregasi Perusahaan</div>
    """, unsafe_allow_html=True)
    
    # Pilih Tingkat Proses
    st.markdown("**🏗️ Pilih Tingkat Fasilitas**")
    tingkat_col1, tingkat_col2, tingkat_col3 = st.columns(3)
    
    with tingkat_col1:
        if st.button("🏠 GudangKab\n(Level 5)", key="t5", use_container_width=True, type="primary" if st.session_state.selected_tingkat == 5 else "secondary"):
            st.session_state.selected_tingkat = 5
            st.session_state.company_batches = []
            st.session_state.company_batch_validation = {}
            st.session_state.generated_id_perusahaan = ""
            st.rerun()
    with tingkat_col2:
        if st.button("🚢 GudangPelabuhan\n(Level 6)", key="t6", use_container_width=True, type="primary" if st.session_state.selected_tingkat == 6 else "secondary"):
            st.session_state.selected_tingkat = 6
            st.session_state.company_batches = []
            st.session_state.company_batch_validation = {}
            st.session_state.generated_id_perusahaan = ""
            st.rerun()
    with tingkat_col3:
        if st.button("🏛️ Pusat\n(Level 7)", key="t7", use_container_width=True, type="primary" if st.session_state.selected_tingkat == 7 else "secondary"):
            st.session_state.selected_tingkat = 7
            st.session_state.company_batches = []
            st.session_state.company_batch_validation = {}
            st.session_state.generated_id_perusahaan = ""
            st.rerun()
    
    selected_tingkat = st.session_state.selected_tingkat
    
    # Tampilkan tingkat yang dipilih dan aturan routing
    from config import VALID_ROUTES, TINGKAT_PROSES_MAP
    
    # Tentukan sumber yang diizinkan berdasarkan VALID_ROUTES
    allowed_sources_levels = []
    for src, tgts in VALID_ROUTES.items():
        if selected_tingkat in tgts:
            allowed_sources_levels.append(src)
            
    allowed_sources_str = ", ".join([TINGKAT_PROSES_MAP.get(l, str(l)) for l in allowed_sources_levels])
    
    st.markdown(f"""
    <div style="background: rgba(220,38,38,0.08); border: 1px solid rgba(220,38,38,0.25); 
         border-radius: 10px; padding: 12px; margin: 12px 0; font-size: 0.85rem;">
        <span style="color: #FCA5A5;">🎯 Tingkat Dipilih:</span> 
        <strong style="color: #F87171;">{TINGKAT_PROSES_MAP.get(selected_tingkat, '?')}</strong>
        <br/>
        <span style="color: #FCA5A5;">📥 Sumber yang Diizinkan:</span>
        <strong style="color: #F87171;">{allowed_sources_str}</strong>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("**📋 Informasi Batch Perusahaan Baru**")
    col_gen_comp, col_gen_date = st.columns(2)
    with col_gen_comp:
        g_nama_c = st.text_input("Nama Perusahaan / Gudang *", placeholder="Contoh: PT_CACAO_EXPORT", key="g_comp_name")
    with col_gen_date:
        g_date_c = st.date_input("Tanggal Input *", value=datetime.today(), key="g_comp_date")

    # Dynamic real-time sequence and ID calculation
    id_batch_baru = ""
    seq = ""
    if g_nama_c.strip():
        from config import ID_PREFIX
        from utils import get_next_sequence_batch, generate_agregasi_id, normalize_name
        prefix = ID_PREFIX.get(selected_tingkat, "COMP")
        ddmmyy = g_date_c.strftime("%d%m%y")
        search_prefix = f"{prefix}-{normalize_name(g_nama_c.strip())}-{ddmmyy}-"
        
        if st.session_state.get('ganache_connected'):
            traceability = st.session_state.contracts['Traceability']
            seq = get_next_sequence_batch(traceability, selected_tingkat, search_prefix)
            id_batch_baru = generate_agregasi_id(prefix, g_nama_c.strip(), ddmmyy, seq)
        else:
            id_batch_baru = f"{prefix}-{normalize_name(g_nama_c.strip())}-{ddmmyy}-001"

    col_id, col_qty = st.columns(2)
    with col_id:
        st.text_input(
            "🏷️ ID Batch Perusahaan Baru (Otomatis) *",
            value=id_batch_baru,
            disabled=True,
            help="ID unik untuk batch perusahaan ini yang dihasilkan secara otomatis."
        )
    with col_qty:
        total_qty = st.number_input(
            "⚖️ Total Kuantitas (Kg) *",
            min_value=1,
            max_value=10_000_000,
            value=5000,
            step=100
        )
    if seq:
        st.caption(f"ℹ️ Nomor Urut Batch terdeteksi di blockchain: **#{seq}**")

    keterangan_mutu = st.text_area(
        "📋 Keterangan Parameter Mutu *",
        placeholder="Contoh: Kadar air 7.5%, fermentasi baik, bebas aflatoksin...",
        height=80,
        help="Deskripsi parameter mutu kakao"
    )
    
    st.markdown("---")
    
    # Pilih Batch Sumber
    st.markdown(f"**📥 Pilih Batch Sumber ({allowed_sources_str})**")

    # Ambil daftar batch sumber yang tersedia berdasarkan level input yang valid
    available_sources = []
    if st.session_state.get('ganache_connected'):
        try:
            traceability = st.session_state.contracts['Traceability']
            
            for s_lvl in allowed_sources_levels:
                all_ids = traceability.functions.getBatchIdsByLevel(s_lvl).call()
                for bid in all_ids:
                    try:
                        data = traceability.functions.dataAgregasi(bid).call()
                        # data = (idBatchBaru, tingkat, totalQty, parameterMutu, pemilik, isAggregated, timestamp)
                        if not data[5] and bid not in st.session_state.company_batches: # isAggregated == False
                            available_sources.append(bid)
                    except Exception:
                        pass
        except Exception:
            pass

    col_add, col_btn = st.columns([4, 1])
    with col_add:
        new_source = st.selectbox(
            "ID Batch Sumber",
            options=[""] + available_sources,
            format_func=lambda x: "Pilih Batch Sumber Tersedia..." if x == "" else x,
            key="new_source",
            label_visibility="collapsed",
            disabled=len(available_sources) == 0
        )
    with col_btn:
        if st.button("➕", key="btn_add_source"):
            sid = new_source.strip()
            if sid and sid not in st.session_state.company_batches:
                st.session_state.company_batches.append(sid)
                st.rerun()
    
    if st.session_state.company_batches:
        for i, bid in enumerate(st.session_state.company_batches):
            col_b, col_r = st.columns([5, 1])
            with col_b:
                vd = st.session_state.company_batch_validation.get(bid, {})
                if vd:
                    if vd.get('valid'):
                        st.markdown(f'<span class="batch-chip valid">✅ {bid} ({vd.get("qty",0):,} Kg)</span>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<span class="batch-chip invalid">❌ {bid} — {vd.get("reason","")}</span>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<span class="batch-chip">⏳ {bid}</span>', unsafe_allow_html=True)
            with col_r:
                if st.button("🗑️", key=f"rm_c_{i}"):
                    st.session_state.company_batches.remove(bid)
                    if bid in st.session_state.company_batch_validation:
                        del st.session_state.company_batch_validation[bid]
                    st.rerun()
        
        col_vld, col_clr = st.columns(2)
        with col_vld:
            if st.button("🔍 Validasi Sumber", key="btn_val_company"):
                with st.spinner("Validasi ke blockchain..."):
                    results = validasi_batch_agregasi_perusahaan(st.session_state.company_batches, selected_tingkat)
                    st.session_state.company_batch_validation = results
                    st.rerun()
        with col_clr:
            if st.button("🗑️ Bersihkan", key="btn_clr_company"):
                st.session_state.company_batches = []
                st.session_state.company_batch_validation = {}
                st.rerun()
    else:
        st.info(f"📋 Tambahkan ID Batch dari {allowed_sources_str} sebagai sumber.")
    
    st.markdown("---")
    st.markdown(f"""
    <div style="font-size: 0.8rem; color: #FECACA; margin-bottom: 12px;">
        🔑 Transaksi dari: <code>{st.session_state.get('wallet_address', 'N/A')[:20]}...</code>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button(
        f"🏭 Buat Batch Perusahaan - {TINGKAT_PROSES_MAP.get(selected_tingkat,'?')}",
        key="btn_submit_company",
        use_container_width=True
    ):
        errors = []
        if not id_batch_baru.strip():
            errors.append("ID Batch Perusahaan wajib diisi.")
        if len(st.session_state.company_batches) == 0:
            errors.append("Pilih minimal 1 Batch Sumber.")
        if not keterangan_mutu.strip():
            errors.append("Keterangan mutu wajib diisi.")
        
        for err in errors:
            st.error(f"❌ {err}")
        
        if not errors:
            if not st.session_state.get('private_key'):
                st.error("❌ Private Key belum diinput!")
            else:
                with st.spinner("⏳ Mengirim transaksi ke blockchain..."):
                    try:
                        w3 = st.session_state.w3
                        contracts = st.session_state.contracts
                        traceability = contracts['Traceability']
                        
                        batch_list = [b.strip() for b in st.session_state.company_batches]
                        
                        contract_func = traceability.functions.createCompanyBatch(
                            id_batch_baru.strip(),
                            batch_list,
                            int(selected_tingkat),  # TingkatProses enum (5, 6, 7)
                            int(total_qty),
                            keterangan_mutu.strip()
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
                                <div style="font-size: 1.2rem; color: #FCA5A5; margin-bottom: 12px;">✅ Batch Perusahaan Berhasil Dibuat!</div>
                                <table style="font-size: 0.8rem; color: #FECACA; width: 100%;">
                                    <tr><td style="color: #FCA5A5; padding: 3px 0;">🏭 ID Batch</td><td><strong>{id_batch_baru}</strong></td></tr>
                                    <tr><td style="color: #FCA5A5; padding: 3px 0;">🏗️ Tingkat</td><td><strong>{TINGKAT_PROSES_MAP.get(selected_tingkat,'?')}</strong></td></tr>
                                    <tr><td style="color: #FCA5A5; padding: 3px 0;">📥 Batch Sumber</td><td>{len(batch_list)} Batch</td></tr>
                                    <tr><td style="color: #FCA5A5; padding: 3px 0;">⚖️ Total Qty</td><td><strong>{total_qty:,} Kg</strong></td></tr>
                                    <tr><td style="color: #FCA5A5; padding: 3px 0;">🔗 TX Hash</td>
                                        <td style="font-family: monospace; font-size: 0.7rem;">{result['tx_hash'][:24]}...{result['tx_hash'][-8:]}</td>
                                    </tr>
                                </table>
                            </div>
                            """, unsafe_allow_html=True)
                            st.session_state.company_batches = []
                            st.session_state.company_batch_validation = {}
                            st.balloons()
                        else:
                            st.error(f"❌ Transaksi Gagal: {result['error']}")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
    
    st.markdown("</div>", unsafe_allow_html=True)

with col_info:
    # Hierarki Visual
    st.markdown("""
    <div class="form-card">
        <div style="font-family: 'Space Grotesk', sans-serif; font-size: 1rem; font-weight: 600; 
             color: #FCA5A5; margin-bottom: 16px;">🏗️ Hierarki Rantai Pasok</div>
        <div style="font-size: 0.82rem; color: #FECACA; line-height: 2.0; text-align: center;">
            <div style="background: rgba(220,38,38,0.15); border-radius: 8px; padding: 8px; margin: 4px 0;">
                🏛️ <strong>Pusat / Eksportir (Level 7)</strong><br>
                <span style="font-size: 0.7rem; color: #FCA5A5;">Menarik dari GudangPelabuhan, GudangKab, dsb.</span>
            </div>
            <div style="color: #DC2626;">↑</div>
            <div style="background: rgba(220,38,38,0.1); border-radius: 8px; padding: 8px; margin: 4px 0;">
                🚢 <strong>GudangPelabuhan (Level 6)</strong><br>
                <span style="font-size: 0.7rem; color: #FCA5A5;">Menarik dari GudangKab / Pengepul</span>
            </div>
            <div style="color: #DC2626;">↑</div>
            <div style="background: rgba(220,38,38,0.08); border-radius: 8px; padding: 8px; margin: 4px 0;">
                🏠 <strong>GudangKab (Level 5)</strong><br>
                <span style="font-size: 0.7rem; color: #FCA5A5;">Menarik dari Pengepul (Tk. 3 & 4)</span>
            </div>
            <div style="color: #DC2626;">↑</div>
            <div style="background: rgba(245,158,11,0.08); border-radius: 8px; padding: 8px; margin: 4px 0;">
                📦 <strong>Pengepul (Level 0 - 4)</strong><br>
                <span style="font-size: 0.7rem; color: #FCD34D;">Tingkat Kelompok Tani s.d Luar Kabupaten</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Cek Data
    st.markdown("""
    <div class="form-card" style="margin-top: 12px;">
        <div style="font-weight: 600; color: #FCA5A5; margin-bottom: 12px;">🔍 Cek Batch Perusahaan</div>
    """, unsafe_allow_html=True)
    
    check_comp_id = st.text_input("ID Batch Perusahaan", placeholder="COMP-GK-001", key="check_comp")
    if st.button("🔍 Cek", key="btn_check_comp"):
        if check_comp_id.strip() and st.session_state.get('ganache_connected'):
            try:
                contracts = st.session_state.contracts
                data = contracts['Traceability'].functions.dataAgregasi(check_comp_id.strip()).call()
                # ABI returns: idBatchBaru, tingkat, totalQty, parameterMutu, pemilik, isAggregated, timestamp
                id_b, tingkat, qty, mutu, pemilik, is_agg, ts = data
                
                if ts == 0:
                    st.warning(f"⚠️ Batch `{check_comp_id}` belum terdaftar.")
                else:
                    reg_time = datetime.fromtimestamp(ts).strftime("%d %b %Y, %H:%M")
                    sumber = contracts['Traceability'].functions.getSumberAgregasi(check_comp_id.strip()).call()
                    agg_str = "🔒 Sudah Diagregasi" if is_agg else "🟢 Tersedia"
                    
                    st.markdown(f"""
                    <div style="background: rgba(220,38,38,0.05); border: 1px solid rgba(220,38,38,0.15); 
                         border-radius: 10px; padding: 12px; font-size: 0.78rem; color: #FECACA;">
                        <div style="color: #FCA5A5; font-weight: 600; margin-bottom: 8px;">✅ Batch Ditemukan</div>
                        <div>🏭 ID: <strong>{id_b}</strong></div>
                        <div>🏗️ Tingkat: {TINGKAT_PROSES_MAP.get(tingkat, 'Unknown')}</div>
                        <div>⚖️ Qty: {qty:,} Kg</div>
                        <div>📋 Mutu: {mutu[:50]}...</div>
                        <div>📥 {len(sumber)} batch sumber</div>
                        <div>📊 {agg_str}</div>
                        <div>🕐 {reg_time}</div>
                    </div>
                    """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error: {str(e)}")

    st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# PANEL DAFTAR BATCH PERUSAHAAN PER TINGKATAN (Full Width)
# ============================================================
st.markdown("---")
st.markdown("""
<div style="font-family: 'Space Grotesk', sans-serif; font-size: 1.2rem; font-weight: 700;
     color: #FCA5A5; margin-bottom: 16px;">
    📋 Daftar Batch Perusahaan per Tingkatan
</div>
""", unsafe_allow_html=True)

col_ref5, col_cnt5 = st.columns([1, 4])
with col_ref5:
    refresh_company = st.button("🔄 Muat / Refresh", key="btn_refresh_company")

tab_gk, tab_gp, tab_pusat = st.tabs([
    "🏠 GudangKab (Level 5)",
    "🚢 GudangPelabuhan (Level 6)",
    "🏛️ Pusat (Level 7)"
])

def render_company_batch_list(level: int, tab, level_name: str, color: str):
    """Helper untuk render daftar batch per level di dalam tab."""
    with tab:
        if refresh_company or st.session_state.get(f'company_list_{level}_loaded'):
            if st.session_state.get('ganache_connected'):
                try:
                    contracts = st.session_state.contracts
                    traceability = contracts['Traceability']

                    all_ids = traceability.functions.getBatchIdsByLevel(level).call()
                    total = traceability.functions.getTotalBatchByLevel(level).call()
                    st.session_state[f'company_list_{level}_loaded'] = True

                    st.markdown(f"""
                    <div style="background: rgba(220,38,38,0.06); border: 1px solid rgba(220,38,38,0.15);
                         border-radius: 10px; padding: 10px 16px; font-size: 0.85rem; color: #FECACA;
                         margin-bottom: 12px;">
                        📊 Total Batch {level_name}: <strong style="color: {color}; font-size: 1.1rem;">{total}</strong>
                    </div>
                    """, unsafe_allow_html=True)

                    if not all_ids:
                        st.info(f"📭 Belum ada batch {level_name} yang terdaftar.")
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
                                    "Parameter Mutu": mutu[:40] + "..." if len(mutu) > 40 else mutu,
                                    "Status": "Diagregasi" if is_agg else "Tersedia",
                                    "Pemilik": f"{pemilik[:8]}...{pemilik[-4:]}",
                                    "Waktu": datetime.fromtimestamp(ts).strftime("%d %b %Y"),
                                })
                            except Exception:
                                rows.append({"ID Batch": bid, "Tingkat": "-", "Total Qty (Kg)": "-",
                                             "Jml Sumber": "-", "Parameter Mutu": "-", "Status": "Error",
                                             "Pemilik": "-", "Waktu": "-"})

                        import pandas as pd
                        df = pd.DataFrame(rows)
                        st.dataframe(df, use_container_width=True, hide_index=True)
                except Exception as e:
                    st.error(f"❌ Gagal memuat daftar batch {level_name}: {str(e)}")
            else:
                st.warning("⚠️ Tidak terhubung ke blockchain.")
        else:
            st.info(f"👆 Klik **Muat / Refresh** di atas untuk memuat daftar batch {level_name}.")

render_company_batch_list(5, tab_gk,    "GudangKab",       "#FCA5A5")
render_company_batch_list(6, tab_gp,    "GudangPelabuhan", "#F87171")
render_company_batch_list(7, tab_pusat, "Pusat",           "#EF4444")

