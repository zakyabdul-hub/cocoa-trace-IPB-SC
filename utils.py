"""
utils.py - Utilitas untuk otomatisasi pembuatan ID terstruktur (Structured ID)
Sistem Ketertelusuran Kakao Berbasis Blockchain
"""

import re
from datetime import datetime

def normalize_name(name: str) -> str:
    """
    Mengubah nama menjadi UPPERCASE, menghapus karakter non-alphanumeric (kecuali spasi),
    dan mengganti semua spasi dengan garis bawah (_).
    """
    if not name:
        return ""
    # Hapus whitespace berlebih di awal/akhir dan jadikan uppercase
    normalized = name.strip().upper()
    # Hapus karakter khusus selain spasi, alphanumeric, dan underscore
    normalized = re.sub(r'[^A-Z0-9\s_]', '', normalized)
    # Ganti spasi dengan underscore
    normalized = re.sub(r'\s+', '_', normalized)
    return normalized

def get_next_sequence_lahan(contract_master_data, no_stdb: str) -> str:
    """
    Query blockchain MasterData, hitung jumlah lahan yang memiliki no_stdb yang sama,
    dan kembalikan nomor urut berikutnya dalam format 3-digit (misal '001', '002').
    """
    try:
        # Dapatkan semua ID Lahan di blockchain
        all_ids = contract_master_data.functions.getAllLahanIds().call()
        count = 0
        target_stdb = no_stdb.strip().upper()
        
        for lid in all_ids:
            try:
                # dataLahan returns tuple:
                # (idLahan, noSTDB, koordinat, luas, idVar1, idVar2, isBebasDeforestasi, petani, timestamp)
                ldata = contract_master_data.functions.dataLahan(lid).call()
                if ldata[1].strip().upper() == target_stdb:
                    count += 1
            except Exception:
                pass
        
        return str(count + 1).zfill(3)
    except Exception:
        # Fallback jika gagal koneksi blockchain
        return "001"

def get_next_sequence_batch(contract_traceability, tingkat: int, prefix: str) -> str:
    """
    Query blockchain Traceability, dapatkan list batch pada level (tingkat) tertentu,
    hitung jumlah ID batch yang ber-awalan dengan prefix,
    dan kembalikan nomor urut berikutnya dalam format 3-digit (misal '001', '002').
    """
    try:
        # Dapatkan semua ID Batch pada level tersebut dari blockchain
        all_ids = contract_traceability.functions.getBatchIdsByLevel(tingkat).call()
        count = 0
        target_prefix = prefix.strip().upper()
        
        for bid in all_ids:
            if bid.strip().upper().startswith(target_prefix):
                count += 1
                
        return str(count + 1).zfill(3)
    except Exception:
        # Fallback jika gagal koneksi blockchain
        return "001"

def generate_varietas_id(jenis: str, mmyy: str, masa_edar: int) -> str:
    """
    Generate ID Varietas: VAR-[Jenis Varietas]-[MMYY]-[Masa Edar]
    Contoh: VAR-TSH858-0724-5
    """
    jenis_norm = normalize_name(jenis)
    mmyy_norm = normalize_name(mmyy)
    return f"VAR-{jenis_norm}-{mmyy_norm}-{masa_edar}"

def generate_lahan_id(nama_petani: str, no_stdb: str, seq: str) -> str:
    """
    Generate ID Lahan: LAHAN-[Nama]-[NO STDB]-[No urut]
    Contoh: LAHAN-AGUS-STDB1234567-001
    """
    nama_norm = normalize_name(nama_petani)
    stdb_norm = normalize_name(no_stdb)
    return f"LAHAN-{nama_norm}-{stdb_norm}-{seq}"

def generate_panen_id(ddmmyy: str, id_lahan: str) -> str:
    """
    Generate ID Panen: PANEN-[DDMMYY]-[ID Lahan]
    Contoh: PANEN-090726-LAHAN-AGUS-1234567-001
    """
    # DDMMYY diinput/autofill, ID Lahan menggunakan ID Lahan penuh yang dipilih
    id_lahan_norm = id_lahan.strip().upper()
    return f"PANEN-{ddmmyy}-{id_lahan_norm}"

def generate_agregasi_id(prefix: str, nama: str, ddmmyy: str, seq: str) -> str:
    """
    Generate ID Agregasi (Pengepul / Perusahaan): [PREFIX]-[Nama]-[DDMMYY]-[No Urut]
    Contoh: P3-PT_OLAM_INTERNASIONAL-120726-001
    """
    nama_norm = normalize_name(nama)
    return f"{prefix}-{nama_norm}-{ddmmyy}-{seq}"
