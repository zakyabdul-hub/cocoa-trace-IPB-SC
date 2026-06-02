"""
06_F6_Riwayat_Ketertelusuran.py
Fitur F6: Melihat Riwayat Ketertelusuran (Traceback Rekursif)
Aktor: Semua Pengguna / Publik
Smart Contract: Traceability.getSumberAgregasi(), dataPanen, dataAgregasi, MasterData.dataLahan, dataVarietas
Output: Visualisasi timeline pohon + Download PDF
"""

import streamlit as st
import sys
import os
from datetime import datetime
from io import BytesIO

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import TINGKAT_PROSES_MAP

# ============================================================
# KONFIGURASI HALAMAN
# ============================================================
st.set_page_config(
    page_title="F6 — Riwayat Ketertelusuran | CacaoTrace",
    page_icon="🔍",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@500;600;700&family=Space+Mono:wght@400;700&display=swap');
.stApp { background: linear-gradient(135deg, #06050F 0%, #040408 100%) !important; color: #F0EEFF !important; }
[data-testid="stSidebar"] { background: #040408 !important; border-right: 1px solid rgba(124,58,237,0.2) !important; }
.page-header {
    background: linear-gradient(135deg, rgba(124,58,237,0.15) 0%, rgba(167,139,250,0.08) 100%);
    border: 1px solid rgba(124,58,237,0.2); border-radius: 20px; padding: 32px; margin-bottom: 24px;
    border-left: 4px solid #7C3AED;
}
.traceback-container {
    background: rgba(124,58,237,0.04); border: 1px solid rgba(124,58,237,0.15);
    border-radius: 20px; padding: 28px; margin: 16px 0;
}
.trace-node {
    background: rgba(124,58,237,0.08); border: 1px solid rgba(167,139,250,0.2);
    border-radius: 14px; padding: 16px; margin: 8px 0;
    position: relative; transition: all 0.3s ease;
}
.trace-node:hover { border-color: rgba(167,139,250,0.5); transform: translateX(4px); }
.trace-node.level-pusat { border-left: 4px solid #DC2626; }
.trace-node.level-pelabuhan { border-left: 4px solid #D97706; }
.trace-node.level-gudangkab { border-left: 4px solid #0284C7; }
.trace-node.level-pengepul { border-left: 4px solid #059669; }
.trace-node.level-panen { border-left: 4px solid #4ADE80; }
.trace-node.level-lahan { border-left: 4px solid #38BDF8; }
.trace-node.level-varietas { border-left: 4px solid #34D399; }
.trace-connector {
    color: rgba(124,58,237,0.5); font-size: 1.2rem;
    margin-left: 24px; display: block; padding: 4px 0;
}
.trace-badge {
    display: inline-block; padding: 3px 10px; border-radius: 12px;
    font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em;
}
.badge-pusat { background: rgba(220,38,38,0.2); color: #FCA5A5; }
.badge-pelabuhan { background: rgba(217,119,6,0.2); color: #FCD34D; }
.badge-gudangkab { background: rgba(2,132,199,0.2); color: #7DD3FC; }
.badge-pengepul { background: rgba(5,150,105,0.2); color: #34D399; }
.badge-panen { background: rgba(74,222,128,0.15); color: #86EFAC; }
.badge-lahan { background: rgba(56,189,248,0.15); color: #7DD3FC; }
.badge-varietas { background: rgba(52,211,153,0.15); color: #6EE7B7; }
.deforest-ok { color: #4ADE80; font-size: 0.8rem; }
.deforest-no { color: #EF4444; font-size: 0.8rem; }
.stTextInput > div > div > input {
    background: rgba(124,58,237,0.05) !important; border: 1px solid rgba(124,58,237,0.25) !important;
    border-radius: 10px !important; color: #F0EEFF !important; font-size: 1rem !important;
}
.stButton > button {
    background: linear-gradient(135deg, #7C3AED, #8B5CF6) !important; color: white !important;
    border: none !important; border-radius: 10px !important; font-weight: 600 !important;
    padding: 0.6rem 2rem !important; transition: all 0.3s !important;
}
.stButton > button:hover { transform: translateY(-2px) !important; box-shadow: 0 8px 24px rgba(124,58,237,0.4) !important; }
.stDownloadButton > button {
    background: linear-gradient(135deg, #059669, #10B981) !important; color: white !important;
    border: none !important; border-radius: 10px !important; font-weight: 700 !important;
    font-size: 1rem !important; padding: 0.7rem 2rem !important; width: 100% !important;
}
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# HEADER
# ============================================================
st.markdown("""
<div class="page-header">
    <div style="font-size: 2rem; margin-bottom: 8px;">🔍</div>
    <div style="font-family: 'Space Grotesk', sans-serif; font-size: 1.8rem; font-weight: 700; color: #A78BFA;">
        F6 — Riwayat Ketertelusuran
    </div>
    <div style="color: #C4B5FD; font-size: 0.95rem; margin-top: 8px;">
        Lacak riwayat lengkap rantai pasok kakao secara rekursif dari hilir ke hulu.
        Visualisasi pohon ketertelusuran interaktif + Ekspor laporan PDF.
    </div>
    <div style="margin-top: 12px; font-size: 0.75rem; color: #A78BFA;">
        👤 Aktor: <strong>Semua Pengguna (Publik)</strong> &nbsp;|&nbsp;
        📋 Fungsi: <code style="background: rgba(124,58,237,0.1); padding: 2px 8px; border-radius: 4px;">getSumberAgregasi() → rekursif</code>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# FUNGSI TRACEBACK REKURSIF
# ============================================================

def get_trace_data_agregasi(batch_id: str, contracts: dict, depth: int = 0, max_depth: int = 20) -> dict:
    """
    Mengambil data batch agregasi dari blockchain.
    Mengembalikan dictionary berisi data node dan children.
    """
    if depth > max_depth:
        return {"type": "MAX_DEPTH", "id": batch_id}
    
    try:
        # Coba sebagai BatchAgregasi
        data = contracts['Traceability'].functions.dataAgregasi(batch_id).call()
        id_b, tingkat, qty, mutu, pemilik, is_agg, ts = data
        
        if ts != 0:
            # Ambil sumber
            id_sumber_list = contracts['Traceability'].functions.getSumberAgregasi(batch_id).call()
            
            tingkat_name = TINGKAT_PROSES_MAP.get(tingkat, f"Level{tingkat}")
            
            node = {
                "type": "AGREGASI",
                "tingkat": tingkat,
                "tingkat_name": tingkat_name,
                "id": id_b,
                "qty": qty,
                "mutu": mutu,
                "pemilik": pemilik,
                "is_aggregated": is_agg,
                "timestamp": ts,
                "children": []
            }
            
            # Rekursi ke setiap sumber
            for sumber_id in id_sumber_list:
                child = get_trace_data_panen_or_agregasi(sumber_id, contracts, depth + 1, max_depth)
                node["children"].append(child)
            
            return node
    except Exception:
        pass
    
    return {"type": "UNKNOWN", "id": batch_id}


def get_trace_data_panen_or_agregasi(batch_id: str, contracts: dict, depth: int = 0, max_depth: int = 20) -> dict:
    """
    Menentukan apakah batch_id adalah BatchPanen atau BatchAgregasi lalu mengambil datanya.
    """
    if depth > max_depth:
        return {"type": "MAX_DEPTH", "id": batch_id}
    
    # Coba sebagai BatchPanen dahulu
    try:
        data_panen = contracts['Traceability'].functions.dataPanen(batch_id).call()
        id_b, id_lahan, qty, is_ferm, petani, is_agg, ts = data_panen
        
        if ts != 0:
            # Ambil data Lahan
            lahan_node = get_lahan_data(id_lahan, contracts)
            
            return {
                "type": "PANEN",
                "id": id_b,
                "id_lahan": id_lahan,
                "qty": qty,
                "is_fermented": is_ferm,
                "petani": petani,
                "is_aggregated": is_agg,
                "timestamp": ts,
                "children": [lahan_node] if lahan_node else []
            }
    except Exception:
        pass
    
    # Coba sebagai BatchAgregasi
    return get_trace_data_agregasi(batch_id, contracts, depth, max_depth)


def get_lahan_data(id_lahan: str, contracts: dict) -> dict:
    """Mengambil data Lahan dan Varietas dari MasterData."""
    try:
        data = contracts['MasterData'].functions.dataLahan(id_lahan).call()
        id_l, no_stdb, koordinat, luas, id_v1, id_v2, is_bebas, petani, ts = data
        
        if ts == 0:
            return {"type": "LAHAN_NOT_FOUND", "id": id_lahan}
        
        # Ambil data Varietas
        var1_node = get_varietas_data(id_v1, contracts) if id_v1 else None
        var2_node = get_varietas_data(id_v2, contracts) if id_v2 and id_v2.strip() else None
        
        return {
            "type": "LAHAN",
            "id": id_l,
            "no_stdb": no_stdb,
            "koordinat": koordinat,
            "luas": luas,
            "is_bebas_deforestasi": is_bebas,
            "petani": petani,
            "timestamp": ts,
            "children": [n for n in [var1_node, var2_node] if n is not None]
        }
    except Exception as e:
        return {"type": "ERROR", "id": id_lahan, "error": str(e)}


def get_varietas_data(id_varietas: str, contracts: dict) -> dict:
    """Mengambil data Varietas dari MasterData."""
    if not id_varietas or not id_varietas.strip():
        return None
    try:
        data = contracts['MasterData'].functions.dataVarietas(id_varietas).call()
        id_v, sk_pep, masa_edar, penangkar, ts = data
        
        if ts == 0:
            return {"type": "VARIETAS_NOT_FOUND", "id": id_varietas}
        
        return {
            "type": "VARIETAS",
            "id": id_v,
            "sk_pelepasan": sk_pep,
            "masa_edar": masa_edar,
            "penangkar": penangkar,
            "timestamp": ts,
            "children": []
        }
    except Exception as e:
        return {"type": "ERROR", "id": id_varietas, "error": str(e)}


def flatten_trace(node: dict, flat_list: list = None, indent: int = 0) -> list:
    """Meratakan pohon trace menjadi daftar berurutan untuk PDF dan tampilan."""
    if flat_list is None:
        flat_list = []
    
    flat_list.append({"node": node, "indent": indent})
    
    for child in node.get("children", []):
        flatten_trace(child, flat_list, indent + 1)
    
    return flat_list


# ============================================================
# FUNGSI RENDER NODE
# ============================================================

def render_trace_node(node: dict, indent: int = 0) -> str:
    """Merender satu node menjadi HTML."""
    if not node:
        return ""
    
    node_type = node.get("type", "UNKNOWN")
    margin = f"margin-left: {indent * 30}px;"
    
    if node_type == "AGREGASI":
        tingkat = node.get('tingkat', 0)
        tingkat_name = node.get('tingkat_name', 'Unknown')
        
        level_css = {
            3: ("level-pusat", "badge-pusat", "🏛️", "#DC2626"),
            2: ("level-pelabuhan", "badge-pelabuhan", "🚢", "#D97706"),
            1: ("level-gudangkab", "badge-gudangkab", "🏠", "#0284C7"),
            0: ("level-pengepul", "badge-pengepul", "📦", "#059669"),
        }
        css, badge_css, icon, color = level_css.get(tingkat, ("", "", "📋", "#7C3AED"))
        ts_str = datetime.fromtimestamp(node['timestamp']).strftime("%d %b %Y, %H:%M")
        agg_status = "🔒 Sudah Diagregasi" if node.get('is_aggregated') else "🟢 Tersedia"
        
        return f"""
        <div class="trace-node {css}" style="{margin}">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                <span style="font-size: 1.3rem;">{icon}</span>
                <span class="trace-badge {badge_css}">{tingkat_name}</span>
                <span style="font-family: 'Space Grotesk', sans-serif; font-weight: 600; color: {color}; font-size: 0.95rem;">
                    {node['id']}
                </span>
            </div>
            <div style="font-size: 0.78rem; color: #C4B5FD; display: grid; grid-template-columns: 1fr 1fr; gap: 4px;">
                <span>⚖️ Qty: <strong>{node.get('qty', 0):,} Kg</strong></span>
                <span>🕐 {ts_str}</span>
                <span>📊 {agg_status}</span>
                <span>📋 Mutu: {str(node.get('mutu',''))[:30]}...</span>
            </div>
        </div>"""
    
    elif node_type == "PANEN":
        ferm_str = "✅ Difermentasi" if node.get('is_fermented') else "⏳ Belum Difermentasi"
        ts_str = datetime.fromtimestamp(node['timestamp']).strftime("%d %b %Y, %H:%M")
        agg_status = "🔒 Diagregasi" if node.get('is_aggregated') else "🟢 Tersedia"
        
        return f"""
        <div class="trace-node level-panen" style="{margin}">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                <span style="font-size: 1.3rem;">🌾</span>
                <span class="trace-badge badge-panen">Batch Panen</span>
                <span style="font-family: 'Space Grotesk', sans-serif; font-weight: 600; color: #4ADE80; font-size: 0.95rem;">
                    {node['id']}
                </span>
            </div>
            <div style="font-size: 0.78rem; color: #BBF7D0; display: grid; grid-template-columns: 1fr 1fr; gap: 4px;">
                <span>⚖️ Qty: <strong>{node.get('qty', 0):,} Kg</strong></span>
                <span>🕐 {ts_str}</span>
                <span>🧪 {ferm_str}</span>
                <span>📊 {agg_status}</span>
                <span>🗺️ Lahan: {node.get('id_lahan','')}</span>
            </div>
        </div>"""
    
    elif node_type == "LAHAN":
        bebas = node.get('is_bebas_deforestasi', False)
        bebas_html = '<span class="deforest-ok">✅ Bebas Deforestasi</span>' if bebas else '<span class="deforest-no">❌ Kawasan Hutan</span>'
        ts_str = datetime.fromtimestamp(node['timestamp']).strftime("%d %b %Y, %H:%M")
        
        return f"""
        <div class="trace-node level-lahan" style="{margin}">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                <span style="font-size: 1.3rem;">🗺️</span>
                <span class="trace-badge badge-lahan">Lahan</span>
                <span style="font-family: 'Space Grotesk', sans-serif; font-weight: 600; color: #38BDF8; font-size: 0.95rem;">
                    {node['id']}
                </span>
            </div>
            <div style="font-size: 0.78rem; color: #BAE6FD; display: grid; grid-template-columns: 1fr 1fr; gap: 4px;">
                <span>📄 STDB: {node.get('no_stdb','')}</span>
                <span>🕐 {ts_str}</span>
                <span>📐 Luas: {node.get('luas',0):,} m²</span>
                <span>{bebas_html}</span>
                <span>📍 {node.get('koordinat','')}</span>
            </div>
        </div>"""
    
    elif node_type == "VARIETAS":
        ts_str = datetime.fromtimestamp(node['timestamp']).strftime("%d %b %Y, %H:%M")
        
        return f"""
        <div class="trace-node level-varietas" style="{margin}">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                <span style="font-size: 1.3rem;">🌱</span>
                <span class="trace-badge badge-varietas">Varietas Benih</span>
                <span style="font-family: 'Space Grotesk', sans-serif; font-weight: 600; color: #34D399; font-size: 0.95rem;">
                    {node['id']}
                </span>
            </div>
            <div style="font-size: 0.78rem; color: #A7F3D0; display: grid; grid-template-columns: 1fr 1fr; gap: 4px;">
                <span>📄 SK: {node.get('sk_pelepasan','')}</span>
                <span>🕐 {ts_str}</span>
                <span>📅 Masa Edar: {node.get('masa_edar',0)} Tahun</span>
            </div>
        </div>"""
    
    elif node_type in ["UNKNOWN", "MAX_DEPTH", "ERROR", "LAHAN_NOT_FOUND", "VARIETAS_NOT_FOUND"]:
        return f"""
        <div class="trace-node" style="{margin}; border-left: 4px solid #6B7280;">
            <span style="color: #9CA3AF; font-size: 0.85rem;">⚠️ {node_type}: {node.get('id', 'N/A')}</span>
        </div>"""
    
    return ""


def render_trace_recursive(node: dict, depth: int = 0) -> str:
    """Merender seluruh pohon trace secara rekursif."""
    html = render_trace_node(node, depth)
    
    for i, child in enumerate(node.get("children", [])):
        html += f'<div class="trace-connector" style="margin-left: {(depth + 1) * 30}px;">↓</div>'
        html += render_trace_recursive(child, depth + 1)
    
    return html


# ============================================================
# FUNGSI GENERATE PDF
# ============================================================

def generate_pdf_report(trace_tree: dict, root_id: str) -> bytes:
    """Menghasilkan laporan PDF dari data trace."""
    try:
        from fpdf import FPDF
        from fpdf.enums import XPos, YPos
        
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        # Konfigurasi font — menggunakan font bawaan fpdf2 yang mendukung Unicode
        pdf.set_font('Helvetica', 'B', 20)
        pdf.set_fill_color(50, 20, 5)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 14, 'LAPORAN KETERTELUSURAN KAKAO', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C', fill=True)
        pdf.ln(2)
        
        pdf.set_font('Helvetica', '', 11)
        pdf.set_text_color(80, 60, 40)
        pdf.cell(0, 6, f'Dihasilkan: {datetime.now().strftime("%d %B %Y, %H:%M:%S")}', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        pdf.cell(0, 6, f'ID Batch Asal Penelusuran: {root_id}', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        pdf.ln(6)
        
        # Garis pemisah
        pdf.set_draw_color(180, 140, 80)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(6)
        
        # Ratakan pohon untuk tabel
        flat = flatten_trace(trace_tree)
        
        # TABEL
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_fill_color(70, 35, 10)
        pdf.set_text_color(255, 255, 255)
        
        col_widths = [45, 30, 25, 30, 30, 30]
        headers = ['ID Aset', 'Tipe', 'Qty (Kg)', 'Timestamp', 'Bebas Defor.', 'Status']
        
        for i, (header, width) in enumerate(zip(headers, col_widths)):
            pdf.cell(width, 8, header, border=1, align='C', fill=True)
        pdf.ln()
        
        pdf.set_font('Helvetica', '', 8)
        
        for item in flat:
            node = item['node']
            indent = item['indent']
            
            node_type = node.get('type', 'UNKNOWN')
            
            # ID
            id_val = ('  ' * indent) + node.get('id', 'N/A')[:35]
            
            # Tipe
            type_map = {
                'AGREGASI': TINGKAT_PROSES_MAP.get(node.get('tingkat', 0), 'Agregasi'),
                'PANEN': 'Batch Panen',
                'LAHAN': 'Lahan',
                'VARIETAS': 'Varietas',
            }
            type_val = type_map.get(node_type, node_type)
            
            # Qty
            qty_val = f"{node.get('qty', 0):,}" if 'qty' in node else '-'
            
            # Timestamp
            ts = node.get('timestamp', 0)
            ts_val = datetime.fromtimestamp(ts).strftime('%d/%m/%Y %H:%M') if ts and ts > 0 else '-'
            
            # Bebas Deforestasi
            if node_type == 'LAHAN':
                bebas = 'YA' if node.get('is_bebas_deforestasi') else 'TIDAK'
            else:
                bebas = '-'
            
            # Status
            if 'is_aggregated' in node:
                status = 'Diagregasi' if node['is_aggregated'] else 'Tersedia'
            elif node_type == 'VARIETAS':
                status = 'Terdaftar'
            elif node_type == 'LAHAN':
                status = 'Terdaftar'
            else:
                status = '-'
            
            # Warna baris berdasarkan tipe
            color_map = {
                'AGREGASI': (255, 245, 230),
                'PANEN': (230, 255, 240),
                'LAHAN': (225, 240, 255),
                'VARIETAS': (225, 255, 250),
            }
            r, g, b = color_map.get(node_type, (255, 255, 255))
            pdf.set_fill_color(r, g, b)
            pdf.set_text_color(40, 30, 20)
            
            values = [id_val, type_val, qty_val, ts_val, bebas, status]
            fill = node_type in color_map
            
            for val, width in zip(values, col_widths):
                pdf.cell(width, 7, str(val), border=1, fill=fill)
            pdf.ln()
        
        pdf.ln(8)
        
        # Ringkasan Statistik
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_fill_color(70, 35, 10)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 8, 'RINGKASAN STATISTIK', new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)
        pdf.ln(2)
        
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(40, 30, 20)
        
        # Hitung statistik
        total_nodes = len(flat)
        total_panen = sum(1 for f in flat if f['node'].get('type') == 'PANEN')
        total_lahan = sum(1 for f in flat if f['node'].get('type') == 'LAHAN')
        total_varietas = sum(1 for f in flat if f['node'].get('type') == 'VARIETAS')
        total_qty_panen = sum(f['node'].get('qty', 0) for f in flat if f['node'].get('type') == 'PANEN')
        lahan_bebas = sum(1 for f in flat if f['node'].get('type') == 'LAHAN' and f['node'].get('is_bebas_deforestasi'))
        
        stats = [
            ('Total Node Ketertelusuran', str(total_nodes)),
            ('Jumlah Batch Panen', str(total_panen)),
            ('Jumlah Lahan Terlibat', str(total_lahan)),
            ('Jumlah Varietas Terlibat', str(total_varietas)),
            ('Total Qty Panen Hulu', f'{total_qty_panen:,} Kg'),
            ('Lahan Bebas Deforestasi', f'{lahan_bebas}/{total_lahan}'),
            ('Status Kepatuhan', 'LULUS' if lahan_bebas == total_lahan else 'TIDAK LULUS'),
        ]
        
        for key, val in stats:
            pdf.set_font('Helvetica', 'B', 9)
            pdf.cell(70, 7, f'{key}:', border='LTB')
            pdf.set_font('Helvetica', '', 9)
            pdf.cell(120, 7, val, border='RTB', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        pdf.ln(10)
        pdf.set_font('Helvetica', 'I', 8)
        pdf.set_text_color(120, 100, 80)
        pdf.cell(0, 5, 'Dokumen ini dihasilkan secara otomatis dari blockchain Ethereum (Ganache Local) - CacaoTrace v2.1', align='C')
        
        return bytes(pdf.output())
    
    except ImportError:
        return None
    except Exception as e:
        st.error(f"Error generate PDF: {str(e)}")
        return None


# ============================================================
# SESSION STATE
# ============================================================
if 'trace_result' not in st.session_state:
    st.session_state.trace_result = None
if 'trace_root_id' not in st.session_state:
    st.session_state.trace_root_id = ""

# ============================================================
# INPUT PENCARIAN
# ============================================================
col_search, col_btn = st.columns([5, 1])

with col_search:
    search_id = st.text_input(
        "🔍 Masukkan ID Batch yang Ingin Ditelusuri",
        placeholder="Contoh: COMP-PUSAT-001  atau  COL-POLMAN-001  atau  BTC-PETANI-001",
        value=st.session_state.trace_root_id,
        key="trace_search_input",
        label_visibility="collapsed"
    )

with col_btn:
    do_trace = st.button("🔍 Lacak", key="btn_trace", use_container_width=True)

# Quick examples
with st.expander("📌 Contoh ID Batch untuk Dilacak"):
    st.markdown("""
    Gunakan ID dari batch yang sudah Anda buat melalui fitur F3, F4, atau F5.
    - **F3 Batch Panen**: `BTC-PETANI-001`
    - **F4 Batch Pengepul**: `COL-POLMAN-001`
    - **F5 GudangKab**: `COMP-GK-001`
    - **F5 GudangPelabuhan**: `COMP-PEL-001`
    - **F5 Pusat**: `COMP-PUSAT-001`
    """)

# ============================================================
# PROSES TRACEBACK
# ============================================================
if do_trace and search_id.strip():
    if not st.session_state.get('ganache_connected'):
        st.error("❌ Tidak terhubung ke Ganache!")
    else:
        st.session_state.trace_root_id = search_id.strip()
        
        with st.spinner("🔄 Menelusuri rantai pasok secara rekursif ke blockchain..."):
            try:
                contracts = st.session_state.contracts
                
                # Mulai traceback dari ID yang diinput
                trace_result = get_trace_data_panen_or_agregasi(
                    search_id.strip(), 
                    contracts, 
                    depth=0, 
                    max_depth=25
                )
                
                if trace_result.get('type') in ['UNKNOWN', 'ERROR']:
                    st.error(f"❌ ID `{search_id}` tidak ditemukan di blockchain (bukan BatchPanen maupun BatchAgregasi).")
                    st.session_state.trace_result = None
                else:
                    st.session_state.trace_result = trace_result
            except Exception as e:
                st.error(f"❌ Error saat traceback: {str(e)}")
                st.session_state.trace_result = None

# ============================================================
# TAMPILKAN HASIL TRACEBACK
# ============================================================
if st.session_state.trace_result:
    trace = st.session_state.trace_result
    root_id = st.session_state.trace_root_id
    
    # Hitung ringkasan
    flat_data = flatten_trace(trace)
    
    # STATISTIK
    total_panen = sum(1 for f in flat_data if f['node'].get('type') == 'PANEN')
    total_lahan = sum(1 for f in flat_data if f['node'].get('type') == 'LAHAN')
    total_var = sum(1 for f in flat_data if f['node'].get('type') == 'VARIETAS')
    total_qty = sum(f['node'].get('qty', 0) for f in flat_data if f['node'].get('type') == 'PANEN')
    lahan_bebas = sum(1 for f in flat_data if f['node'].get('type') == 'LAHAN' and f['node'].get('is_bebas_deforestasi'))
    all_bebas = (lahan_bebas == total_lahan) if total_lahan > 0 else True
    
    # Banner status kepatuhan
    if all_bebas:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(34,197,94,0.15), rgba(34,197,94,0.08));
             border: 1px solid rgba(34,197,94,0.4); border-radius: 14px; padding: 16px;
             display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
            <span style="font-size: 2rem;">✅</span>
            <div>
                <div style="color: #4ADE80; font-weight: 700; font-size: 1rem;">
                    LULUS UJI KETERTELUSURAN — Bebas Deforestasi
                </div>
                <div style="color: #86EFAC; font-size: 0.8rem;">
                    Semua {total_lahan} lahan dalam rantai pasok ini bebas dari kawasan hutan.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(239,68,68,0.15), rgba(239,68,68,0.08));
             border: 1px solid rgba(239,68,68,0.4); border-radius: 14px; padding: 16px;
             display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
            <span style="font-size: 2rem;">⚠️</span>
            <div>
                <div style="color: #F87171; font-weight: 700; font-size: 1rem;">
                    PERINGATAN — Ada Lahan di Kawasan Hutan
                </div>
                <div style="color: #FCA5A5; font-size: 0.8rem;">
                    {total_lahan - lahan_bebas} dari {total_lahan} lahan terindikasi masuk kawasan hutan.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # METRIK RINGKASAN
    col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
    with col_m1:
        st.metric("📊 Total Node", len(flat_data))
    with col_m2:
        st.metric("🌾 Batch Panen", total_panen)
    with col_m3:
        st.metric("🗺️ Lahan", total_lahan)
    with col_m4:
        st.metric("🌱 Varietas", total_var)
    with col_m5:
        st.metric("⚖️ Qty Hulu", f"{total_qty:,} Kg")
    
    st.markdown('<hr style="border: none; height: 1px; background: linear-gradient(90deg, transparent, rgba(124,58,237,0.3), transparent); margin: 16px 0;">', unsafe_allow_html=True)
    
    # VISUALISASI POHON
    col_tree, col_dl = st.columns([3, 1])
    
    with col_tree:
        st.markdown(f"""
        <div style="font-family: 'Space Grotesk', sans-serif; font-size: 1.1rem; font-weight: 600; 
             color: #A78BFA; margin-bottom: 16px;">
            🌳 Pohon Ketertelusuran — ID: <span style="color: #C4B5FD;">{root_id}</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="traceback-container">', unsafe_allow_html=True)
        tree_html = render_trace_recursive(trace, 0)
        st.markdown(tree_html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_dl:
        st.markdown("""
        <div style="font-family: 'Space Grotesk', sans-serif; font-size: 1rem; font-weight: 600; 
             color: #A78BFA; margin-bottom: 16px;">
            📄 Export Laporan
        </div>
        """, unsafe_allow_html=True)
        
        # Generate PDF
        with st.spinner("Menyiapkan PDF..."):
            pdf_bytes = generate_pdf_report(trace, root_id)
        
        if pdf_bytes:
            filename = f"Riwayat_{root_id}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            st.download_button(
                label="📥 Download Riwayat (PDF)",
                data=pdf_bytes,
                file_name=filename,
                mime="application/pdf",
                key="btn_download_pdf"
            )
            st.markdown(f"""
            <div style="background: rgba(5,150,105,0.08); border: 1px solid rgba(52,211,153,0.2); 
                 border-radius: 10px; padding: 12px; font-size: 0.78rem; color: #86EFAC; margin-top: 8px;">
                <div style="font-weight: 600; color: #4ADE80; margin-bottom: 6px;">📋 Isi Laporan PDF:</div>
                <div>• Tabel ketertelusuran lengkap</div>
                <div>• Status bebas deforestasi tiap lahan</div>
                <div>• Kuantitas di setiap tingkat</div>
                <div>• Timestamp transaksi blockchain</div>
                <div>• Ringkasan statistik kepatuhan</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("⚠️ fpdf2 tidak tersedia. Install: `pip install fpdf2`")
        
        # Tampilkan data mentah JSON
        with st.expander("🔧 Data Mentah (JSON)"):
            import json
            
            def make_json_safe(obj):
                if isinstance(obj, dict):
                    return {k: make_json_safe(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [make_json_safe(i) for i in obj]
                elif isinstance(obj, bytes):
                    return obj.hex()
                else:
                    return obj
            
            st.code(json.dumps(make_json_safe(trace), indent=2, ensure_ascii=False), language='json')

elif not do_trace:
    # Tampilan placeholder
    st.markdown("""
    <div style="text-align: center; padding: 60px 20px; color: #4C3F7A;">
        <div style="font-size: 4rem; margin-bottom: 16px; opacity: 0.5;">🔍</div>
        <div style="font-family: 'Space Grotesk', sans-serif; font-size: 1.2rem; color: #7C6DAE;">
            Masukkan ID Batch di kolom pencarian dan klik "Lacak"
        </div>
        <div style="font-size: 0.85rem; margin-top: 8px; color: #4C3F7A;">
            Sistem akan menelusuri seluruh rantai pasok secara rekursif dari hilir ke hulu
        </div>
    </div>
    """, unsafe_allow_html=True)
