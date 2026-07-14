# 📋 Implementation Plan: Restrukturisasi Rantai Pasok Kakao — Multi-Level Pengepul

**Tanggal Dokumen:** 9 Juli 2026  
**Versi:** 2.4 (Final — Data Lama Tidak Dimigrasikan, Deploy Fresh)
**Sistem:** Blockchain-Based Cocoa Traceability System (CacaoTrace)  
**Konteks:** Perubahan berdasarkan temuan lapangan bahwa rantai pasok kakao lebih kompleks dari desain awal

---

## 1. Latar Belakang Perubahan

Berdasarkan temuan lapangan, rantai pasok kakao ternyata **lebih panjang dan kompleks** dari desain awal. Perubahan utama:

1. **Tingkat Pengepul bertambah** — dari 1 level menjadi 5 level (Kelompok Tani, Desa, Kecamatan, Kabupaten, Luar Kabupaten)
2. **Jalur pengiriman fleksibel** — bisa lompat tingkat (non-linear), bukan strict sequential
3. **Perusahaan fleksibel** — tidak semua perusahaan memiliki gudang bertingkat; beberapa bisa menerima langsung dari pengepul
4. **Mixed source** — satu batch bisa mengumpulkan dari beberapa tingkat sekaligus

---

## 2. Keputusan Desain Final

Seluruh keputusan desain telah dikonfirmasi:

| No | Keputusan | Jawaban Final |
|----|-----------|---------------|
| 1 | Role Kelompok Tani | Sama dengan `Pengepul` (tidak perlu role baru) |
| 2 | Petani → Kelompok Tani | Menyetorkan `BatchPanen` (mekanisme sama dengan ke Pengepul) |
| 3 | Hierarki Perusahaan | **Dipertahankan** (GudangKab → GudangPelabuhan → Pusat) |
| 4 | Mixed Source | **Harus bisa** campuran dari beberapa tingkat |
| 5 | Data Lama | **Tidak dimigrasikan** — sistem deploy fresh, data blockchain lama tidak diambil. Kontrak baru dimulai dari state kosong |
| 6 | Parameter Mutu | Cukup di tingkat **Perusahaan** saja |
| 7 | PengepulKab → Pusat langsung | **Boleh** — tidak semua perusahaan punya gudang bertingkat |
| 8 | GudangKab → Pusat (skip GudPelabuhan) | **Boleh** — perusahaan bisa punya gudang di kabupaten dan pusat di satu provinsi |
| 9 | Petani langsung ke PengepulKabupaten (Tk3) | **Tidak ada jalur ini** — dikonfirmasi dari gambar interview |
| 10 | Perusahaan Pengolah Kakao vs Pusat Olam | Berbeda entitas di dunia nyata, tapi **sama di sistem** (Level 7). Scope sistem hanya pada biji kakao mentah, bukan produk olahan |
| 11 | Eksportir sebagai level tersendiri | **Masuk ke Level 7 (Pusat)** — Eksportir, Pusat Olam, dan Perusahaan Pengolah adalah semua terminal node di rantai pasok biji kakao |
| 12 | Identitas organisasi di blockchain | **Embedded dalam Batch ID** via Structured Naming Convention. Tidak perlu database tambahan, tidak ubah SC |
| 13 | Nomor Urut (No-Urut) Batch | **Auto-count dari blockchain** — query `batchIdsByLevel`, filter prefix, hitung otomatis. Tidak ada perubahan SC |

---

## 3. Perbandingan Alur Rantai Pasok

### 3.1 Alur Lama (Desain Awal)

```
Petani → Pengepul (Level 0) → GudangKab (Level 1) → GudangPelabuhan (Level 2) → Pusat (Level 3)
```

**Aturan:** Setiap tingkat hanya bisa menarik dari tingkat **tepat di bawahnya** (`tingkat_sumber == tingkat_baru - 1`).

**Aktor:** `Pengepul` (1 role) + `Perusahaan` (1 role)

### 3.2 Alur Baru (Temuan Lapangan)

```
                     ┌─→ Pengepul Tk.1 (Desa) ──────────────────────────────────┐
 Petani ─ BatchPanen ┤                           ┌─→ Pengepul Kecamatan (Tk2) ──┤
  [hanya 2 jalur]    └─→ Kelompok Tani ──────────┤                               │
                                                 └─→ Pengepul Kabupaten (Tk3) ──┤
                                                                                 │
                     Pengepul Kecamatan (Tk2) ───→ Pengepul Kabupaten (Tk3) ─────┤
                                                                                 │
                     Pengepul Kabupaten (Tk3) ──┬─→ Pengepul Luar Kab (Tk4) ────┐
                                               │                                 │
                                               └────────────┐                   │
                                                             ▼                   ▼
                               ┌────────────────────────────────────────────────────┐
                               │  JALUR PERUSAHAAN (hierarki internal tetap ada)    │
                               │                                                    │
                               │  GudangKab (5) ─→ GudangPelabuhan (6) ─→ Pusat*  │
                               │      └──────────────────────────────────→ Pusat*  │
                               │  ATAU langsung:  PengepulKab/LuarKab ──→ Pusat*  │
                               │                                                    │
                               │  * Pusat (Level 7) = Terminal Node, bisa berupa:  │
                               │    - Pusat / Gudang Ekspor (Olam)                  │
                               │    - Perusahaan Pengolah Biji Kakao                │
                               │    - Eksportir Biji Kakao                          │
                               └────────────────────────────────────────────────────┘
```

**Aturan:** Loncatan tingkat **dibolehkan** (Tk.1 langsung ke Tk.3), tapi **tidak boleh mundur**.

**Catatan penting dari validasi gambar interview:**
- Petani **hanya** bisa mengirim ke Kelompok Tani (0) atau Pengepul Desa (1) — tidak ada jalur langsung ke Tk.2, Tk.3, atau perusahaan
- **Level 7 (Pusat)** adalah *terminal node* yang merepresentasikan tiga jenis entitas berbeda di dunia nyata: Pusat/Gudang Ekspor (Olam), Perusahaan Pengolah Biji Kakao, dan Eksportir. Ketiganya **disamakan di sistem** karena sama-sama merupakan tujuan akhir biji kakao dalam rantai pasok
- Scope sistem hanya mencakup **biji kakao** (raw cocoa beans), bukan produk turunan olahan

**Aktor:** `Pengepul` (untuk KelTani + semua tingkat pengepul) + `Perusahaan` (tetap)

---

## 4. Desain Teknis

### 4.1 Enum `TingkatProses` Baru (8 Level)

```solidity
enum TingkatProses {
    KelompokTani,         // 0 — Kelompok Tani (dari BatchPanen)
    PengepulDesa,         // 1 — Pengepul Tk.1 (dari BatchPanen)
    PengepulKecamatan,    // 2 — Pengepul Tk.2 (dari BatchAgregasi)
    PengepulKabupaten,    // 3 — Pengepul Tk.3 (dari BatchAgregasi)
    PengepulLuarKab,      // 4 — Pengepul Tk.4 (dari BatchAgregasi)
    GudangKab,            // 5 — Perusahaan: Gudang Kabupaten
    GudangPelabuhan,      // 6 — Perusahaan: Gudang Pelabuhan
    Pusat                 // 7 — Terminal Node: Pusat Perusahaan / Perusahaan Pengolah Biji Kakao / Eksportir
}
```

**Perbandingan dengan enum lama:**

| Enum Lama | Value Lama | Enum Baru | Value Baru |
|-----------|:---:|-----------|:---:|
| - | - | KelompokTani | 0 |
| - | - | PengepulDesa | 1 |
| - | - | PengepulKecamatan | 2 |
| Pengepul | 0 | PengepulKabupaten | 3 |
| - | - | PengepulLuarKab | 4 |
| GudangKab | 1 | GudangKab | 5 |
| GudangPelabuhan | 2 | GudangPelabuhan | 6 |
| Pusat | 3 | Pusat | 7 |

### 4.2 Tabel Routing yang Diizinkan

Fungsi `isValidRoute()` akan meng-enforce aturan berikut:

| Dari (Sumber) | Ke (Tujuan) yang Diizinkan | Catatan |
|---|---|---|
| KelompokTani (0) | PengepulKecamatan (2), PengepulKabupaten (3) | Bisa lompat |
| PengepulDesa (1) | PengepulKecamatan (2), PengepulKabupaten (3) | Bisa lompat |
| PengepulKecamatan (2) | PengepulKabupaten (3) | Sequential |
| PengepulKabupaten (3) | PengepulLuarKab (4), GudangKab (5), GudangPelabuhan (6), Pusat (7) | Bisa langsung ke perusahaan level manapun |
| PengepulLuarKab (4) | GudangKab (5), GudangPelabuhan (6), Pusat (7) | Bisa langsung ke perusahaan level manapun |
| GudangKab (5) | GudangPelabuhan (6), Pusat (7) | Bisa skip GudPelabuhan |
| GudangPelabuhan (6) | Pusat (7) | Sequential |

### 4.3 Aturan Sumber per Tingkat

| Tingkat | Dari `BatchPanen`? | Dari `BatchAgregasi`? | Keterangan |
|---------|:---:|:---:|---|
| KelompokTani (0) | ✅ | ❌ | Agregasi langsung dari petani — **satu-satunya sumber dari Petani** |
| PengepulDesa (1) | ✅ | ❌ | Agregasi langsung dari petani — **satu-satunya sumber dari Petani** |
| PengepulKecamatan (2) | ❌ | ✅ (dari level 0/1) | Dari Kel.Tani atau Pengepul Desa |
| PengepulKabupaten (3) | ❌ | ✅ (dari level 0/1/2) | Mixed source dibolehkan. **Tidak ada jalur langsung dari Petani** |
| PengepulLuarKab (4) | ❌ | ✅ (dari level 3) | Dari Pengepul Kabupaten |
| GudangKab (5) | ❌ | ✅ (dari level 3/4) | Dari Pengepul Kab atau Luar Kab |
| GudangPelabuhan (6) | ❌ | ✅ (dari level 3/4/5) | Bisa langsung dari pengepul |
| **Pusat (7)** | ❌ | ✅ (dari level 3/4/5/6) | **Terminal Node** — merepresentasikan: Pusat/Ekspor Olam, Perusahaan Pengolah Biji Kakao, atau Eksportir |

### 4.4 Pola Fungsi `createCollectorBatch` (Baru)

Fungsi `createCollectorBatch` sekarang menggunakan **pola enum yang sama** seperti `createCompanyBatch`:

**Desain Lama:**
```solidity
// Hanya 1 level, tanpa parameter tingkat, hanya dari BatchPanen
function createCollectorBatch(
    string memory _idBaru,
    string[] memory _idSumber,  // HANYA dari BatchPanen
    uint256 _totalQty
) public onlyRole("Pengepul") { ... }
```

**Desain Baru:**
```solidity
// Multi-level + dual source, dengan parameter enum
function createCollectorBatch(
    string memory _idBaru,
    string[] memory _idSumberPanen,     // Array BatchPanen (bisa kosong [])
    string[] memory _idSumberAgregasi,  // Array BatchAgregasi (bisa kosong [])
    TingkatProses _tingkat,             // 0=KelTani, 1=Desa, 2=Kec, 3=Kab, 4=LuarKab
    uint256 _totalQty
) public onlyRole("Pengepul") { ... }
```

**Logika validasi internal:**
- Tingkat 0-1: Wajib dari `_idSumberPanen`, `_idSumberAgregasi` harus kosong
- Tingkat 2-4: Wajib dari `_idSumberAgregasi`, `_idSumberPanen` harus kosong
- Routing divalidasi via `isValidRoute()` untuk setiap batch sumber agregasi

---

### 4.5 Konvensi Penamaan ID Batch (Structured Meaningful ID)

Identitas organisasi **tidak disimpan sebagai field terpisah** di blockchain. Sebaliknya, nama organisasi di-encode langsung ke dalam Batch ID menggunakan format terstruktur. Pendekatan ini:
- Tidak memerlukan database tambahan (JSON, SQLite, dsb.)
- Tidak mengubah smart contract
- Identitas langsung terbaca dari Batch ID di blockchain explorer

#### Aturan Teknis Global

| Aturan | Implementasi |
|--------|-------------|
| Spasi dalam nama | Auto-replace menjadi `_` di frontend |
| Kapitalisasi | Auto-convert semua menjadi `UPPERCASE` |
| No-Urut | **Auto-count dari blockchain** (query `batchIdsByLevel`, filter prefix, hitung) |
| Satuan waktu | `DDMMYY` untuk tanggal input; `MMYY` untuk bulan-tahun edar varietas |

#### Format ID per Entitas

| No | Entitas | Format ID | Contoh |
|----|---------|-----------|--------|
| 1 | Varietas Benih | `VAR-[JENIS]-[MMYY]-[MASA_EDAR_BLN]` | `VAR-TSH858-0724-24` |
| 2 | Lahan Petani | `LAHAN-[NAMA]-[NO_STDB]-[NO_URUT]` | `LAHAN-AGUS-1234567-001` |
| 3 | Batch Panen | `PANEN-[DDMMYY]-[ID_LAHAN_LENGKAP]` | `PANEN-090726-LAHAN-AGUS-1234567-001` |
| 4 | Batch Kelompok Tani (Tk.0) | `KELTANI-[NAMA]-[DDMMYY]-[NO_URUT]` | `KELTANI-KOPTAN_MAJU-120726-001` |
| 5 | Batch Pengepul Desa (Tk.1) | `P1-[NAMA]-[DDMMYY]-[NO_URUT]` | `P1-PENGDESA_LUWU-120726-001` |
| 6 | Batch Pengepul Kecamatan (Tk.2) | `P2-[NAMA]-[DDMMYY]-[NO_URUT]` | `P2-CV_KECAMATAN_JAYA-120726-001` |
| 7 | Batch Pengepul Kabupaten (Tk.3) | `P3-[NAMA]-[DDMMYY]-[NO_URUT]` | `P3-OLAM-120726-001` |
| 8 | Batch Pengepul Luar Kab (Tk.4) | `P4-[NAMA]-[DDMMYY]-[NO_URUT]` | `P4-PT_EKSPOR_NUSA-120726-001` |
| 9 | Batch Gudang Kabupaten (Tk.5) | `GUDKAB-[NAMA]-[DDMMYY]-[NO_URUT]` | `GUDKAB-OLAM-120726-001` |
| 10 | Batch Gudang Pelabuhan (Tk.6) | `GUDPEL-[NAMA]-[DDMMYY]-[NO_URUT]` | `GUDPEL-OLAM-120726-001` |
| 11 | Batch Pusat/Pengolah/Eksportir (Tk.7) | `COMPANY-[NAMA]-[DDMMYY]-[NO_URUT]` | `COMPANY-OLAM-120726-001` |

#### Catatan Khusus per Entitas

- **Varietas `[MASA_EDAR_BLN]`** — angka bulat dalam satuan **bulan** (misal `24` = 24 bulan masa edar)
- **Lahan `[NO_URUT]`** — reset per `[NO_STDB]`; satu STDB bisa punya beberapa lahan (001, 002, ...)
- **Batch Panen `[ID_LAHAN_LENGKAP]`** — embed full ID Lahan agar Panen langsung ter-link ke Lahan tanpa lookup tambahan
- **Batch Agregasi `[NO_URUT]`** — reset per kombinasi `[NAMA]+[DDMMYY]`; hari berbeda atau nama berbeda → kembali ke `001`

#### Mekanisme Auto-Count No-Urut (Frontend)

```python
# Akan ditambahkan di utils.py
def get_next_sequence(contract_traceability, tingkat: int, prefix: str) -> str:
    """
    Query blockchain, hitung batch yang sudah ada dengan prefix tertentu,
    return No-Urut berikutnya dalam format '001', '002', dst.
    Operasi READ-ONLY — tidak ada gas fee, tidak mengubah state contract.
    """
    # Ambil semua ID di tingkat ini dari blockchain
    all_ids = contract_traceability.functions.batchIdsByLevel(tingkat).call()

    # Filter yang cocok dengan prefix hari ini
    matching = [id for id in all_ids if id.upper().startswith(prefix.upper())]

    # Return nomor urut berikutnya
    return str(len(matching) + 1).zfill(3)  # "001", "002", dst.
```

#### Tampilan Form Generate ID di Frontend

```
┌─── Generate ID Batch P3 (Pengepul Kabupaten) ───────────┐
│  Nama Entitas  : [ PT Olam Internasional  ]          │
│  Tanggal Input : [ 12/07/26 ] ← auto-fill hari ini  │
│  No. Urut      : [ 001 ]      ← auto-count blockchain│
│                                                       │
│  Preview ID: P3-PT_OLAM_INTERNASIONAL-120726-001      │
│                                                       │
│              [ ✨ Generate ID ]                        │
└───────────────────────────────────────────────────┘
```

---

## 5. Detail Perubahan per File

### 5.1 Smart Contract Layer

#### `contracts/Traceability.sol` — 🔴 PERUBAHAN BESAR

| No | Perubahan | Lokasi | Detail |
|----|-----------|--------|--------|
| 1 | Ubah enum `TingkatProses` | Line 48 | Dari 4 level → 8 level |
| 2 | Tambah `isValidRoute()` | Baru | Fungsi internal pure untuk validasi routing |
| 3 | Tambah `_mergeArrays()` | Baru | Helper menggabungkan 2 string array |
| 4 | Ubah `createCollectorBatch()` | Line 227-272 | Tambah parameter `_tingkat`, dual source input |
| 5 | Ubah `createCompanyBatch()` | Line 285-344 | Update validasi: `>= GudangKab`, routing fleksibel |
| 6 | Tambah `migrateAgregasi()` | Baru | Fungsi admin untuk migrasi data lama |
| 7 | Update getter bounds check | Line 378-381 | Range valid: 0-7 (bukan 0-3) |
| 8 | Update event `CollectorBatchCreated` | Line 119-125 | Tambah parameter `tingkat` di event |

#### `contracts/RoleManager.sol` — 🟢 TIDAK BERUBAH

Tidak ada perubahan. Validasi role "Admin" untuk migrasi data dilakukan dengan memanggil `IRoleManager.admin()` secara langsung di smart contract `Traceability.sol`, sehingga menghindari kebutuhan memodifikasi dan mendeploy ulang `RoleManager.sol`.

#### `contracts/MasterData.sol` — 🟢 TIDAK BERUBAH

Tidak ada perubahan. F1 (Varietas) dan F2 (Lahan) tidak terpengaruh.

---

### 5.2 ABI Layer

| File | Status |
|------|--------|
| `ABI/Traceability_abi.json` | 🔴 REGENERATE — signature fungsi berubah |
| `ABI/RoleManager.json` | 🟢 TIDAK BERUBAH |
| `ABI/MasterData_abi.json` | 🟢 TIDAK BERUBAH |

---

### 5.3 Configuration Layer

#### `config.py` — 🔴 PERUBAHAN BESAR

```python
# ENUM MAP BARU
# Catatan Level 7: Terminal Node — merepresentasikan semua entitas
# penerima akhir biji kakao: Pusat/Ekspor Olam, Perusahaan Pengolah
# Biji Kakao, atau Eksportir. Scope sistem = biji kakao mentah.
TINGKAT_PROSES_MAP = {
    0: "Kelompok Tani",
    1: "Pengepul Desa (Tk.1)",
    2: "Pengepul Kecamatan (Tk.2)",
    3: "Pengepul Kabupaten (Tk.3)",
    4: "Pengepul Luar Kab (Tk.4)",
    5: "GudangKab",
    6: "GudangPelabuhan",
    7: "Pusat / Pengolah / Eksportir",  # Terminal Node
}

TINGKAT_LABEL_MAP = {
    "GudangKab": 5,
    "GudangPelabuhan": 6,
    "Pusat": 7,
}

# ROUTING TABLE (Dikonfirmasi dari gambar rantai pasok interview)
# PENTING: Petani HANYA bisa mengirim ke Level 0 (KelTani) atau Level 1 (PengepulDesa)
# Tidak ada jalur langsung Petani → Tk.2, Tk.3, atau perusahaan
VALID_ROUTES = {
    0: [2, 3],           # KelTani → Kecamatan, Kabupaten (dikonfirmasi)
    1: [2, 3],           # PengepulDesa → Kecamatan, Kabupaten (dikonfirmasi)
    2: [3],              # Kecamatan → Kabupaten
    3: [4, 5, 6, 7],     # Kabupaten → LuarKab, GudKab, GudPelabuhan, Terminal
    4: [5, 6, 7],        # LuarKab → GudKab, GudPelabuhan, Terminal
    5: [6, 7],           # GudKab → GudPelabuhan, Terminal (bisa skip GudPelabuhan)
    6: [7],              # GudPelabuhan → Terminal
}

# Jalur sumber BatchPanen: HANYA level 0 dan 1
TINGKAT_TERIMA_PANEN = [0, 1]      # KelTani dan PengepulDesa saja
TINGKAT_PENGEPUL = [0, 1, 2, 3, 4] # Semua level pengepul
TINGKAT_PERUSAHAAN = [5, 6, 7]     # Level perusahaan
TERMINAL_NODE = 7                   # Pusat / Pengolah / Eksportir

# PREFIX FORMAT ID BATCH (Structured Meaningful ID)
# Identitas organisasi di-encode dalam Batch ID, tidak perlu database terpisah
ID_PREFIX = {
    0: "KELTANI",
    1: "P1",
    2: "P2",
    3: "P3",
    4: "P4",
    5: "GUDKAB",
    6: "GUDPEL",
    7: "COMPANY",
}

# Contoh format lengkap per entitas:
# VAR    : VAR-[JENIS]-[MMYY]-[MASA_EDAR_BLN]   → VAR-TSH858-0724-24
# LAHAN  : LAHAN-[NAMA]-[NO_STDB]-[NO_URUT]      → LAHAN-AGUS-1234567-001
# PANEN  : PANEN-[DDMMYY]-[ID_LAHAN_LENGKAP]     → PANEN-090726-LAHAN-AGUS-1234567-001
# LEVEL0 : KELTANI-[NAMA]-[DDMMYY]-[NO_URUT]     → KELTANI-KOPTAN_MAJU-120726-001
# LEVEL3 : P3-[NAMA]-[DDMMYY]-[NO_URUT]          → P3-OLAM-120726-001
# LEVEL7 : COMPANY-[NAMA]-[DDMMYY]-[NO_URUT]     → COMPANY-OLAM-120726-001

# Contract addresses (akan diupdate setelah deploy ulang Traceability.sol)
CONTRACT_ADDRESSES = {
    "RoleManager":  "...",  # Tidak berubah — pakai address lama
    "MasterData":   "...",  # Tidak berubah — pakai address lama
    "Traceability": "...",  # BARU — deploy ulang
}
```

---

### 5.4 Frontend Layer — Streamlit Pages

#### `pages/04_F4_Agregasi_Pengepul.py` — 🔴 REDESIGN

| No | Perubahan |
|----|-----------|
| 1 | Tambah selector tingkat: KelompokTani / PengepulDesa / PengepulKecamatan / PengepulKabupaten / PengepulLuarKab |
| 2 | Dynamic source selector: tingkat 0-1 → list BatchPanen; tingkat 2+ → list BatchAgregasi |
| 3 | Update pemanggilan contract: `createCollectorBatch(id, panenSources, agregasiSources, tingkat, qty)` |
| 4 | Update tabs list batch: dari 1 tab → 5 tabs (KelTani, Tk.1, Tk.2, Tk.3, Tk.4) |
| 5 | Update hierarki visual |
| 6 | **Tambah form Generate ID**: input Nama → auto `_` dan `UPPERCASE` → auto-count No-Urut dari blockchain → preview ID |

#### `pages/05_F5_Agregasi_Perusahaan.py` — 🟠 PERUBAHAN MODERAT

| No | Perubahan |
|----|-----------|
| 1 | Hierarki tetap 3 tingkat (GudangKab=5, GudangPelabuhan=6, Pusat=7) |
| 2 | Update enum values: Level 1→5, Level 2→6, Level 3→7 |
| 3 | Update validasi sumber: `expected_prev_level` → routing check via `VALID_ROUTES` |
| 4 | Update source list: GudangKab bisa tarik dari PengepulKab (3) atau PengepulLuarKab (4) |
| 5 | GudangKab bisa langsung ke Pusat (skip GudPelabuhan) |
| 6 | **Tambah form Generate ID**: format `GUDKAB-/GUDPEL-/COMPANY-[NAMA]-[DDMMYY]-[NO_URUT]` |

#### `pages/06_F6_Riwayat_Ketertelusuran.py` — 🟠 PERUBAHAN MODERAT

| No | Perubahan |
|----|-----------|
| 1 | Tambah CSS classes untuk tingkat baru (`.level-keltani`, `.level-pengepul-desa`, dst.) |
| 2 | Update `render_trace_node`: tambah case rendering untuk tingkat 0-4 |
| 3 | Update browse tabs: dari 5 → 9 tabs |
| 4 | Update PDF report: label dan warna baru |
| 5 | Logic rekursif traceback **tidak berubah** (sudah generik) |

#### `pages/00_Admin_Panel.py` — 🟡 PERUBAHAN MINOR

| No | Perubahan |
|----|-----------|
| 1 | Update referensi `VALID_ROLES` jika ada perubahan |

#### `pages/01_F1_Varietas_Benih.py` — 🟡 MINOR UPDATE

| No | Perubahan |
|----|-----------|
| 1 | **Tambah form Generate ID Varietas**: format `VAR-[JENIS]-[MMYY]-[MASA_EDAR_BLN]` |

#### `pages/02_F2_Registrasi_Lahan.py` — 🟡 MINOR UPDATE

| No | Perubahan |
|----|-----------|
| 1 | **Tambah form Generate ID Lahan**: format `LAHAN-[NAMA]-[NO_STDB]-[NO_URUT]` |

#### `pages/03_F3_Batch_Panen.py` — 🟡 MINOR UPDATE

| No | Perubahan |
|----|-----------|
| 1 | **Tambah form Generate ID Panen**: format `PANEN-[DDMMYY]-[ID_LAHAN_LENGKAP]`; dropdown Lahan yang sudah terdaftar |

#### `app.py` — 🟠 PERUBAHAN MODERAT

| No | Perubahan |
|----|-----------|
| 1 | Update dashboard statistik: batch count per tingkat baru |
| 2 | Update hierarki visual |
| 3 | Update navigasi sidebar |

#### `utils.py` — 🔴 FILE BARU

| No | Fungsi Baru |
|----|-------------|
| 1 | `normalize_name(nama) -> str` — replace spasi → `_`, convert ke `UPPERCASE` |
| 2 | `get_next_sequence(contract, tingkat, prefix) -> str` — auto-count No-Urut dari blockchain |
| 3 | `generate_batch_id(tingkat, nama, tanggal, seq) -> str` — generate ID agregasi sesuai format |
| 4 | `generate_varietas_id(jenis, mmyy, masa_edar) -> str` — generate ID varietas |
| 5 | `generate_lahan_id(nama_petani, no_stdb, no_urut) -> str` — generate ID lahan |
| 6 | `generate_panen_id(ddmmyy, id_lahan) -> str` — generate ID batch panen |

---

### 5.5 Testing Layer

#### `test/CacaoTraceability.test.js` — 🔴 PERUBAHAN BESAR

| No | Perubahan |
|----|-----------|
| 1 | Update `createCollectorBatch` calls: parameter baru (panenSources, agregasiSources, tingkat) |
| 2 | Update enum values: 1→5, 2→6, 3→7 |
| 3 | Tambah test multi-level pengepul: KelTani → PengepulKec → PengepulKab |
| 4 | Tambah test loncatan: PengepulDesa langsung ke PengepulKab (skip Kec) |
| 5 | Tambah test invalid route: PengepulKab → PengepulDesa (harus gagal) |
| 6 | Tambah test mixed source: PengepulKab dari campuran KelTani + PengepulDesa |
| 7 | Tambah test direct-to-company: PengepulKab langsung ke Pusat (skip gudang) |
| 8 | Tambah test GudangKab langsung ke Pusat (skip GudPelabuhan) |

#### `test/CacaoScalability.test.js` — 🔴 PERUBAHAN BESAR

Sama dengan CacaoTraceability.test.js — semua panggilan contract harus diupdate.

---

### 5.6 Deployment Strategy

> [!IMPORTANT]
> **Keputusan Perubahan (v2.4):** Data dari blockchain lama **tidak dimigrasikan**. Sistem deploy fresh ke Ganache dengan state bersih.

#### Proses Deploy

1. Deploy `Traceability.sol` v2 ke Ganache — arahkan constructor ke alamat **`RoleManager`** dan **`MasterData`** yang sudah ada (tidak dideploy ulang)
2. Update `CONTRACT_ADDRESSES["Traceability"]` di `config.py` dengan address baru
3. Regenerate `ABI/Traceability_abi.json` dari compile hasil baru
4. Data Varietas & Lahan di `MasterData.sol` **tetap utuh** (contract tidak berubah)
5. Role pengguna di `RoleManager.sol` **tetap utuh** (contract tidak berubah)
6. Data BatchPanen & BatchAgregasi lama **tidak diambil** — mulai transaksi baru dari nol

> [!NOTE]
> Karena scope sistem adalah **penelitian/thesis**, tidak ada kebutuhan continuity data produksi. Data lama tetap tersimpan di Ganache lama dan bisa direferensikan secara terpisah jika diperlukan untuk dokumentasi.

---

## 6. Smart Contract — Kode Perubahan Kunci

### 6.1 Fungsi `isValidRoute()` (BARU)

```solidity
/// @dev Validasi apakah jalur dari tingkat sumber ke tingkat tujuan diperbolehkan
function isValidRoute(TingkatProses _from, TingkatProses _to) internal pure returns (bool) {
    uint256 f = uint256(_from);
    uint256 t = uint256(_to);
    
    // Aturan dasar: tidak boleh mundur atau sama
    if (f >= t) return false;
    
    // KelompokTani(0) / PengepulDesa(1) → PengepulKecamatan(2) atau PengepulKabupaten(3)
    if (f <= 1) return (t == 2 || t == 3);
    
    // PengepulKecamatan(2) → PengepulKabupaten(3)
    if (f == 2) return (t == 3);
    
    // PengepulKabupaten(3) → semua level di atasnya (4, 5, 6, 7)
    if (f == 3) return (t >= 4);
    
    // PengepulLuarKab(4) → level perusahaan (5, 6, 7)
    if (f == 4) return (t >= 5);
    
    // GudangKab(5) → GudangPelabuhan(6) atau Pusat(7)
    if (f == 5) return (t >= 6);
    
    // GudangPelabuhan(6) → Pusat(7)
    if (f == 6) return (t == 7);
    
    return false;
}
```

### 6.2 Fungsi `createCollectorBatch()` (DIUBAH)

```solidity
function createCollectorBatch(
    string memory _idBaru,
    string[] memory _idSumberPanen,
    string[] memory _idSumberAgregasi,
    TingkatProses _tingkat,
    uint256 _totalQty
) public onlyRole("Pengepul") {
    require(dataAgregasi[_idBaru].timestamp == 0, "ID Batch sudah ada!");
    require(uint256(_tingkat) <= uint256(TingkatProses.PengepulLuarKab),
        "Tingkat tidak valid untuk Pengepul! Gunakan createCompanyBatch()");
    require(_idSumberPanen.length + _idSumberAgregasi.length > 0,
        "Minimal 1 sumber diperlukan!");
    require(_totalQty > 0, "Total kuantitas harus lebih dari 0");
    
    // Tingkat 0-1: hanya dari BatchPanen
    if (uint256(_tingkat) <= 1) {
        require(_idSumberAgregasi.length == 0,
            "KelompokTani/PengepulDesa hanya bisa dari BatchPanen!");
        for (uint256 i = 0; i < _idSumberPanen.length; i++) {
            require(dataPanen[_idSumberPanen[i]].timestamp != 0, "BatchPanen fiktif!");
            require(!dataPanen[_idSumberPanen[i]].isAggregated, "BatchPanen sudah diagregasi!");
            dataPanen[_idSumberPanen[i]].isAggregated = true;
        }
    } else {
        // Tingkat 2+: hanya dari BatchAgregasi
        require(_idSumberPanen.length == 0,
            "Tingkat ini hanya bisa dari BatchAgregasi!");
        for (uint256 i = 0; i < _idSumberAgregasi.length; i++) {
            require(dataAgregasi[_idSumberAgregasi[i]].timestamp != 0, "BatchAgregasi fiktif!");
            require(!dataAgregasi[_idSumberAgregasi[i]].isAggregated, "BatchAgregasi sudah diagregasi!");
            require(isValidRoute(dataAgregasi[_idSumberAgregasi[i]].tingkat, _tingkat),
                "Jalur rantai pasok tidak valid!");
            dataAgregasi[_idSumberAgregasi[i]].isAggregated = true;
        }
    }
    
    // Gabungkan sumber
    string[] memory allSources = _mergeArrays(_idSumberPanen, _idSumberAgregasi);
    
    // Simpan
    dataAgregasi[_idBaru] = BatchAgregasi({
        idBatchBaru: _idBaru,
        idSumber: allSources,
        tingkat: _tingkat,
        totalQty: _totalQty,
        parameterMutu: "",      // Mutu hanya di tingkat perusahaan
        pemilik: msg.sender,
        isAggregated: false,
        timestamp: block.timestamp
    });
    
    batchIdsByLevel[uint256(_tingkat)].push(_idBaru);
    agregasiBatchByPemilik[msg.sender].push(_idBaru);
    
    emit CollectorBatchCreated(_idBaru, allSources, _totalQty, msg.sender, block.timestamp);
}
```

### 6.3 Perubahan `createCompanyBatch()` (DIUBAH)

```solidity
function createCompanyBatch(
    string memory _idBaru,
    string[] memory _idSumber,
    TingkatProses _tingkat,
    uint256 _totalQty,
    string memory _mutu
) public onlyRole("Perusahaan") {
    // ... existing validation ...
    
    // PERUBAHAN: Tingkat harus >= GudangKab (5)
    require(
        uint256(_tingkat) >= uint256(TingkatProses.GudangKab),
        "Tingkat tidak valid untuk Perusahaan! Gunakan createCollectorBatch()"
    );
    
    for (uint256 i = 0; i < _idSumber.length; i++) {
        string memory idAsal = _idSumber[i];
        // ... existing validation ...
        
        // PERUBAHAN: Routing fleksibel (bukan strict n-1)
        require(
            isValidRoute(dataAgregasi[idAsal].tingkat, _tingkat),
            "Jalur rantai pasok tidak valid!"
        );
        
        dataAgregasi[idAsal].isAggregated = true;
    }
    
    // ... rest of function same ...
}
```

---

## 7. UML Diagram yang Perlu Diupdate

| Diagram | Status | Detail Perubahan |
|---------|:---:|---|
| **BPMN TO-BE** | ✅ WAJIB | Alur bercabang, bukan linear. Tambah node multi-level pengepul |
| **Use Case Diagram** | ⚠️ MINOR | Deskripsi use case F4 berubah |
| **Class Diagram** | ✅ WAJIB | Enum `TingkatProses` berubah (8 level), signature fungsi berubah |
| **Activity Diagram F4** | ✅ WAJIB | Alur keputusan: pilih tingkat → pilih sumber (panen/agregasi) |
| **Activity Diagram F5** | ⚠️ MINOR | Sumber yang diizinkan berubah |
| **Sequence Diagram F4** | ✅ WAJIB | Parameter fungsi berubah |
| **Sequence Diagram F5** | ⚠️ MINOR | Enum value bergeser |
| **Sequence Diagram F6** | ⚠️ MINOR | Label berubah |
| **F1-F3 semua diagram** | ❌ TIDAK | Tidak terpengaruh |

---

## 8. Verification Plan

### 8.1 Automated Tests

```bash
npx hardhat test
```

### 8.2 Manual Verification Checklist

- [ ] Deploy kontrak baru ke Ganache (fresh state)
- [ ] Verify address `RoleManager` dan `MasterData` masih sama
- [ ] Test alur lengkap: Petani → KelTani → PengepulKec → PengepulKab → GudangKab → GudPel → Pusat
- [ ] Test loncatan pengepul: PengepulDesa → PengepulKab (skip Kecamatan) ✅
- [ ] Test langsung ke perusahaan: PengepulKab → Pusat (skip gudang) ✅
- [ ] Test skip gudang: GudangKab → Pusat (skip GudPelabuhan) ✅
- [ ] Test mundur ditolak: PengepulKab → PengepulDesa ❌ (harus revert)
- [ ] Test mixed source: PengepulKab dari campuran KelTani + PengepulDesa ✅
- [ ] Test double-spend ditolak: Batch yang sudah diagregasi tidak bisa diklaim ulang ❌
- [ ] Test traceback F6: Rekursif dari Pusat sampai ke Petani/Lahan/Varietas
- [ ] Test PDF export: Label baru tampil benar
- [ ] Test Generate ID: format VAR/LAHAN/PANEN/P1-P4/GUDKAB/GUDPEL/COMPANY benar

---

## 9. Ringkasan Dampak

### File yang Berubah

| File | Tingkat Perubahan | Kategori |
|------|:---:|---|
| `contracts/Traceability.sol` | 🔴 BESAR | Smart Contract |
| `contracts/RoleManager.sol` | 🟢 TIDAK | Smart Contract |
| `contracts/MasterData.sol` | 🟢 TIDAK | Smart Contract |
| `ABI/Traceability_abi.json` | 🔴 REGENERATE | ABI |
| `ABI/RoleManager.json` | 🟢 TIDAK | ABI |
| `ABI/MasterData_abi.json` | 🟢 TIDAK | ABI |
| `config.py` | 🔴 BESAR | Config |
| `utils.py` | 🔴 BARU | Utilities |
| `pages/01_F1_Varietas_Benih.py` | 🟡 MINOR | Frontend |
| `pages/02_F2_Registrasi_Lahan.py` | 🟡 MINOR | Frontend |
| `pages/03_F3_Batch_Panen.py` | 🟡 MINOR | Frontend |
| `pages/04_F4_Agregasi_Pengepul.py` | 🔴 REDESIGN | Frontend |
| `pages/05_F5_Agregasi_Perusahaan.py` | 🟠 MODERAT | Frontend |
| `pages/06_F6_Riwayat_Ketertelusuran.py` | 🟠 MODERAT | Frontend |
| `pages/00_Admin_Panel.py` | 🟡 MINOR | Frontend |
| `app.py` | 🟠 MODERAT | Frontend |
| `test/CacaoTraceability.test.js` | 🔴 BESAR | Testing |
| `test/CacaoScalability.test.js` | 🔴 BESAR | Testing |

**Total:** ~15 file diubah + 1 file baru (`utils.py`)

### Catatan Penting

> ⚠️ **Breaking Change:** Smart contract yang sudah di-deploy tidak bisa di-modify. Harus deploy ulang `Traceability.sol` ke Ganache. **Data BatchPanen & BatchAgregasi lama tidak dimigrasikan** — sistem dimulai dengan state bersih. Data Varietas, Lahan, dan Role pengguna tetap utuh karena `RoleManager.sol` dan `MasterData.sol` tidak dideploy ulang.

---

*Dokumen ini dihasilkan pada 9 Juli 2026 sebagai bagian dari dokumentasi thesis perubahan arsitektur rantai pasok kakao.*
