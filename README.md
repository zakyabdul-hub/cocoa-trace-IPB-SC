# 🍫 CacaoTrace — Sistem Ketertelusuran Rantai Pasok Kakao Berbasis Blockchain

> **Proof of Concept** | Streamlit + Web3.py + Solidity | Ganache Local EVM

---

## 🚀 Cara Menjalankan Aplikasi

### 1. Prasyarat
Pastikan sudah terinstall:
- **Python 3.x** (direkomendasikan 3.9+)
- **Ganache** (running di `http://127.0.0.1:7545`)
- Kontrak sudah di-deploy (lihat `scenario2.json` untuk alamat)

### 2. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

Untuk library geospasial (opsional, bisa di-skip jika error):
```bash
python -m pip install geopandas shapely fiona pyproj
```

### 3. Buat Shapefile Simulasi (Opsional)

```bash
python create_shapefile_simulasi.py
```

### 4. Jalankan Aplikasi

```bash
python -m streamlit run app.py
```

Atau jika streamlit sudah di PATH:
```bash
streamlit run app.py
```

Akses di browser: **http://localhost:8501**

---

## 📁 Struktur File

```
Cacao_trace_phyton/
├── app.py                          # Halaman utama (Login + Dashboard)
├── config.py                       # Konfigurasi Web3 & Smart Contract
├── requirements.txt                # Dependencies Python
├── create_shapefile_simulasi.py    # Generator file .shp simulasi
├── peta_kawasan_hutan.shp          # (buat dengan script di atas)
│
├── ABI/                            # ABI hasil deploy dari REMIX IDE
│   ├── RoleManager_abi.json
│   ├── MasterData_abi.json
│   └── Traceability_abi.json
│
├── pages/                          # Halaman fitur Streamlit
│   ├── 00_Admin_Panel.py           # Manajemen peran
│   ├── 01_F1_Registrasi_Varietas.py
│   ├── 02_F2_Registrasi_Lahan.py   # Dengan validasi geospasial
│   ├── 03_F3_Pencatatan_Panen.py
│   ├── 04_F4_Agregasi_Pengepul.py
│   ├── 05_F5_Agregasi_Perusahaan.py
│   └── 06_F6_Riwayat_Ketertelusuran.py  # Traceback + PDF export
│
└── .streamlit/
    └── config.toml                 # Tema dark mode
```

---

## 🔗 Alamat Smart Contract (Ganache Lokal)

| Kontrak | Alamat |
|---|---|
| RoleManager | `0xDF8E528Eae01282135C084C8d85B069AcB46B2c1` |
| MasterData | `0xf0FE187109C84C1EC7dB83401250047dDFf06a8f` |
| Traceability | `0x645276f7Da2332D4B5e5F3d00AA40364Eaa77367` |

## 👤 Akun Simulasi (dari scenario2.json)

| Peran | Alamat |
|---|---|
| Admin | `0xfdf8c15bb2936c8acc3aa84c444ed5a927f54087` |
| Penangkar | `0xb00d3972d191fd5ca1d09b502301d459783c59a0` |
| Petani | `0x26db7fdfb334d158264381be9e669072e9950985` |
| Pengepul | `0xf92d7da870741eace5c336a5cf501ec75e398e6e` |

---

## 🎯 Alur Penggunaan

```
1. Jalankan Ganache di port 7545
2. Buka aplikasi Streamlit
3. Login dengan Wallet Address + Private Key dari Ganache
4. Admin: Assign peran ke akun lain (Admin Panel)
5. Penangkar: F1 — Registrasi Varietas Benih
6. Petani: F2 — Registrasi Lahan (validasi geospasial otomatis)
7. Petani: F3 — Catat Hasil Panen
8. Pengepul: F4 — Agregasi Batch Pengepul
9. Perusahaan: F5 — Agregasi Berjenjang (GudangKab→Pelabuhan→Pusat)
10. Semua: F6 — Lacak Riwayat + Download PDF
```

---

## 🛠️ Teknologi

- **Blockchain**: Local EVM (Ganache), Solidity ^0.8.0
- **Backend**: Python 3.x + Web3.py 6.x
- **Frontend**: Streamlit
- **Geospasial**: geopandas + shapely
- **PDF**: fpdf2
- **Data**: pandas, numpy, plotly

---

*CacaoTrace v2.1 | Proof of Concept*
