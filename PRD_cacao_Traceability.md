# Project Requirements Document (PRD)
**Project Name:** Blockchain-Based Cocoa Traceability System (Proof of Concept)
**Document Version:** 2.1 (Aligned with F1-F6 UML Diagrams & Geospatial Validation)

## 1. Project Overview
Purwarupa sistem ketertelusuran rantai pasok kakao dari hulu ke hilir menggunakan teknologi *blockchain*. Sistem dirancang untuk memastikan transparansi, validasi rantai pasok yang saling terkait (*chaining validation*), dan mencegah klaim ganda (*double-spending*). Terdapat fitur validasi geospasial otomatis untuk memastikan lahan bebas deforestasi.

## 2. Technology Stack
* **Blockchain Network:** Local EVM (Ganache) - RPC `http://127.0.0.1:7545`
* **Smart Contract:** Solidity `^0.8.0` (Modular: `RoleManager.sol`, `MasterData.sol`, `Traceability.sol`)
* **Backend/Middleware:** Python 3.x, `web3.py`
* **Geospatial Processing:** `geopandas`, `shapely` (Membaca file `.shp`)
* **PDF Generator:** `fpdf2` atau `reportlab` (Untuk ekspor laporan)
* **Frontend UI:** Streamlit (Python)

## 3. User Roles (Berdasarkan Use Case Diagram & RoleManager.sol)
Autentikasi menggunakan identitas *Wallet Address*.
* **Admin:** Mendeploy kontrak dan mendaftarkan peran (*role*) aktor lain.
* **Penangkar:** Aktor hulu, bertugas meregistrasi aset Varietas Benih.
* **Petani:** Meregistrasi Lahan (dengan validasi deforestasi otomatis) dan mencatat hasil panen harian.
* **Pengepul:** Menggabungkan (agregasi) beberapa Batch Panen Petani menjadi satu Batch Pengepul.
* **Perusahaan:** Melakukan agregasi lanjutan sesuai hierarki Tingkat Proses.

## 4. Data Models (Berdasarkan Class Diagram)
Struktur data yang dikelola oleh *Smart Contract*:
* **Varietas (MasterData):** `idVarietas`, `skPelepasan`, `masaEdar`, `penangkar`, `timestamp`.
* **Lahan (MasterData):** `idLahan`, `noSTDB`, `koordinat`, `luas`, `idVar1`, `idVar2`, `isBebasDeforestasi`, `petani`, `timestamp`.
* **BatchPanen (Traceability):** `idBatchPanen`, `idLahan`, `qtyPanen`, `isFermented`, `petani`, `isAggregated`, `timestamp`.
* **BatchAgregasi (Traceability):** `idBatchBaru`, `idSumber`, `tingkat`, `totalQty`, `parameterMutu`, `pemilik`, `isAggregated`, `timestamp`.

## 5. Core Features Specifications

### F1: Registrasi Aset Varietas Benih (Sequence Diagram F1)
* **Aktor:** Penangkar
* **UI Input:** ID Varietas, SK Pelepasan, Masa Edar (Tahun).
* **Blockchain Action:** Memanggil `registerVariety` di kontrak `MasterData`.

### F2: Registrasi Aset Lahan & Validasi Geospasial (Sequence Diagram F2)
* **Aktor:** Petani
* **UI Input:** ID Lahan, No STDB, Titik Koordinat GPS (Latitude, Longitude), Luas Lahan, ID Varietas Utama, ID Varietas Opsional.
* **System Process (Geospatial Validation):**
    1. Sistem membaca koordinat yang diinput oleh petani.
    2. Sistem memuat `peta_kawasan_hutan.shp` dari direktori root.
    3. Menggunakan `geopandas` dan `shapely`, sistem mengecek apakah titik koordinat tersebut beririsan (*intersects*) atau berada di dalam area poligon kawasan hutan.
    4. Sistem secara otomatis menetapkan nilai variabel `isBebasDeforestasi` menjadi `True` (jika di luar hutan) atau `False` (jika di dalam hutan).
* **Blockchain Action:** Memanggil `registerLand(...)` di `MasterData`. 
* *Constraint:* Transaksi ditolak sistem jika variabel `isBebasDeforestasi` bernilai `False` (peringatan UI muncul tanpa hit ke blockchain) atau jika ID Varietas fiktif.

### F3: Pencatatan Aset Panen Petani (Sequence Diagram F3)
* **Aktor:** Petani
* **UI Input:** ID Batch Panen Baru, ID Lahan, Kuantitas Panen (Kg), Checkbox "Sudah Difermentasi".
* **Blockchain Action:** Memanggil `createHarvestBatch(...)` di kontrak `Traceability`.

### F4: Agregasi Batch Petani ke Pengepul (Sequence Diagram F4)
* **Aktor:** Pengepul
* **UI Input:** ID Batch Pengepul Baru, Total Kuantitas (Kg), **Multiselect Array ID Batch Panen Petani**.
* **Blockchain Action:** Memanggil `createCollectorBatch(...)` di `Traceability`.

### F5: Agregasi Batch Perusahaan (Sequence Diagram F5)
* **Aktor:** Perusahaan
* **UI Input:** ID Batch Perusahaan Baru, Tingkat Fasilitas (1=GudangKab, 2=GudangPelabuhan, 3=Pusat), Total Kuantitas, Keterangan Mutu, **Multiselect Array ID Batch Sumber**.
* **Blockchain Action:** Memanggil `createCompanyBatch(...)` di `Traceability`.

### F6: Melihat Riwayat Ketertelusuran (Sequence Diagram F6)
* **Aktor:** Semua Pengguna / Publik
* **UI Input:** Kolom Pencarian ID Batch.
* **Proses Sistem:** Rekursif mundur membaca array `idSumber` menggunakan fungsi `getSumberAgregasi` via Web3.py hingga mencapai level hulu (Lahan & Varietas).
* **UI Output:** 1. Visualisasi *timeline* pohon ketertelusuran interaktif di layar.
    2. **Tombol "Download Riwayat (PDF)" yang akan men-*generate* file PDF berisi tabel informasi detail (ID, Status Bebas Deforestasi, Kuantitas, Tingkat Proses, dan Timestamp) dari hulu ke hilir.**

## 6. Development Guidelines untuk AI Agent
* **Manajemen State:** Gunakan `st.session_state` untuk menyimpan identitas *wallet* pengguna.
* **Geospatial Processing:** Wajib menggunakan pustaka `geopandas` untuk memuat file `.shp` secara efisien (gunakan st.cache_data agar loading file .shp tidak memperlambat aplikasi setiap kali render ulang) dan ubah input koordinat petani menjadi objek `shapely.geometry.Point` untuk pengecekan spasial (`.contains` atau `.intersects`).
* **Error Handling:** Tangkap `ContractLogicError` dan tampilkan sebagai `st.error()`.
* **Persiapan Lingkungan:** Tambahkan `geopandas`, `shapely`, dan dependensi spasial pendukung (seperti `fiona` atau `pyproj`) ke dalam `requirements.txt`.
* **PDF Report Generation:** AI Agent wajib merangkai data hasil iterasi *traceback* Web3.py ke dalam format dokumen PDF menggunakan library `fpdf2` atau `reportlab`, dan menampilkannya di Streamlit menggunakan fungsi `st.download_button`.