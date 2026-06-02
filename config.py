"""
config.py - Konfigurasi terpusat untuk koneksi Web3 dan Smart Contract
Sistem Ketertelusuran Kakao Berbasis Blockchain
"""

import json
import os
from pathlib import Path
from web3 import Web3

# ============================================================
# KONFIGURASI KONEKSI BLOCKCHAIN
# ============================================================
GANACHE_RPC = "http://127.0.0.1:7545"

# ============================================================
# ALAMAT SMART CONTRACT (Dari hasil deploy di REMIX IDE - scenario2.json)
# ============================================================
CONTRACT_ADDRESSES = {
    "RoleManager":  "0xDF8E528Eae01282135C084C8d85B069AcB46B2c1",
    "MasterData":   "0xf0FE187109C84C1EC7dB83401250047dDFf06a8f",
    "Traceability": "0x645276f7Da2332D4B5e5F3d00AA40364Eaa77367",
}

# ============================================================
# AKUN SIMULASI (Dari scenario2.json) — Untuk referensi
# ============================================================
SIMULATION_ACCOUNTS = {
    "Admin":      "0xfdf8c15bb2936c8acc3aa84c444ed5a927f54087",
    "Penangkar":  "0xb00d3972d191fd5ca1d09b502301d459783c59a0",
    "Petani":     "0x26db7fdfb334d158264381be9e669072e9950985",
    "Pengepul":   "0xf92d7da870741eace5c336a5cf501ec75e398e6e",
}

# ============================================================
# DAFTAR PERAN VALID (sesuai RoleManager.sol)
# ============================================================
VALID_ROLES = ["Admin", "Penangkar", "Petani", "Pengepul", "Perusahaan"]

# ============================================================
# ENUM TingkatProses (sesuai Traceability.sol)
# ============================================================
TINGKAT_PROSES_MAP = {
    0: "Pengepul",
    1: "GudangKab",
    2: "GudangPelabuhan",
    3: "Pusat",
}

TINGKAT_LABEL_MAP = {
    "GudangKab": 1,
    "GudangPelabuhan": 2,
    "Pusat": 3,
}

# ============================================================
# PATH KONFIGURASI
# ============================================================
BASE_DIR = Path(__file__).parent
ABI_DIR = BASE_DIR / "ABI"
SHAPEFILE_PATH = BASE_DIR / "peta_kawasan_hutan.shp"


def load_abi(contract_name: str) -> list:
    """Memuat ABI dari file JSON di folder ABI/.
    Mendukung dua konvensi nama file:
      1. ContractName_abi.json  (default)
      2. ContractName.json      (fallback)
    """
    # Coba nama dengan suffix _abi terlebih dahulu
    abi_file = ABI_DIR / f"{contract_name}_abi.json"
    if not abi_file.exists():
        # Fallback: coba nama tanpa suffix _abi
        abi_file = ABI_DIR / f"{contract_name}.json"
    if not abi_file.exists():
        raise FileNotFoundError(
            f"ABI file tidak ditemukan untuk '{contract_name}'. "
            f"Cari: {ABI_DIR}/{contract_name}_abi.json atau {ABI_DIR}/{contract_name}.json"
        )
    with open(abi_file, "r", encoding="utf-8") as f:
        return json.load(f)


def get_web3() -> Web3:
    """Membuat koneksi Web3 ke Ganache."""
    w3 = Web3(Web3.HTTPProvider(GANACHE_RPC))
    return w3


def get_contracts(w3: Web3) -> dict:
    """Menginisialisasi semua instance smart contract."""
    contracts = {}
    for name, address in CONTRACT_ADDRESSES.items():
        abi = load_abi(name)
        contracts[name] = w3.eth.contract(
            address=Web3.to_checksum_address(address),
            abi=abi
        )
    return contracts


def build_transaction(w3: Web3, contract_func, sender_address: str, private_key: str):
    """
    Helper untuk membangun, menandatangani, dan mengirim transaksi.
    
    Returns:
        dict: {'success': bool, 'tx_hash': str, 'error': str}
    """
    try:
        sender = Web3.to_checksum_address(sender_address)
        nonce = w3.eth.get_transaction_count(sender)
        
        # Estimasi gas
        gas_estimate = contract_func.estimate_gas({'from': sender})
        
        # Bangun transaksi
        txn = contract_func.build_transaction({
            'from': sender,
            'nonce': nonce,
            'gas': int(gas_estimate * 1.2),  # buffer 20%
            'gasPrice': w3.eth.gas_price,
        })
        
        # Tandatangani transaksi dengan private key
        signed_txn = w3.eth.account.sign_transaction(txn, private_key=private_key)
        
        # Kirim transaksi
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        
        # Tunggu receipt
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
        
        if receipt.status == 1:
            return {
                'success': True,
                'tx_hash': tx_hash.hex(),
                'receipt': receipt,
                'error': None
            }
        else:
            return {
                'success': False,
                'tx_hash': tx_hash.hex(),
                'receipt': receipt,
                'error': "Transaksi reverted oleh kontrak."
            }
    except Exception as e:
        error_msg = str(e)
        # Ekstrak pesan error dari ContractLogicError
        if "execution reverted" in error_msg:
            try:
                # Coba ekstrak pesan revert
                start = error_msg.find("revert") + len("revert")
                clean_msg = error_msg[start:].strip().strip(":")
                if clean_msg:
                    error_msg = clean_msg.strip()
            except Exception:
                pass
        return {
            'success': False,
            'tx_hash': None,
            'receipt': None,
            'error': error_msg
        }
