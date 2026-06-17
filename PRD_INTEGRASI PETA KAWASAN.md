# 📝 Product Requirement Document (PRD)

## Dokumen Kontrol
*   **Nama Fitur:** Modul Validasi Legalitas Lahan & Kepatuhan Deforestasi (KLHK API Integration)
*   **Status:** Draft Proposal
*   **Tech Stack Utama:** Python, Streamlit, Requests, Folium, Web3/Blockchain Interfacing
*   **Target Rilis:** v1.0-alpha (Milestone Penelitian/Sistem)

---

## 1. Ringkasan Eksekutif & Latar Belakang
Dalam industri kakao global, khususnya terkait regulasi keberlanjutan baru seperti **EUDR (European Union Deforestation Regulation)**, pembuktian bahwa komoditas tidak ditanam di kawasan hutan lindung atau lahan hasil deforestasi adalah hal wajib. 

Fitur ini bertujuan untuk mengintegrasikan sistem ketertelusuran suplai kakao (*cocoa traceability*) dengan **ArcGIS REST API Geoportal KLHK**. Fitur ini bertindak sebagai *gatekeeper* (gerbang validasi) otomatis di *front-end* aplikasi Streamlit sebelum data koordinat kebun petani di-minting atau dicatat secara permanen ke dalam *smart contract blockchain*.

---

## 2. Tujuan Kunci (Objectives)
*   **Validasi Otomatis:** Menilai kepatuhan spasial koordinat kebun petani terhadap peta Kawasan Hutan Indonesia secara *real-time*.
*   **Integritas Data Blockchain:** Memastikan hanya kebun yang berstatus **APL (Areal Penggunaan Lain)** atau luar kawasan hutan yang dapat melanjutkan proses registrasi dan pengetokan token ketertelusuran (*traceability token*).
*   **Visualisasi UI:** Menyediakan peta interaktif di dalam dasbor Streamlit untuk memberikan transparansi lokasi kepada verifikator atau pembeli (*buyer*).

---

## 3. Persona Pengguna & Alur Kerja
### Persona: Auditor Keberlanjutan / Pengelola Koperasi Kakao
*   **Kebutuhan:** Memasukkan data koordinat kebun yang dikumpulkan dari GPS petani di lapangan, memverifikasi status hukumnya, dan mendaftarkannya ke rantai pasok digital.

### Alur Kerja Sistem (User Flow)
1. Pengguna membuka halaman pendaftaran lahan di aplikasi Streamlit.
2. Pengguna memasukkan koordinat `Latitude` dan `Longitude`.
3. Pengguna menekan tombol **"Validasi Lahan"**.
4. Sistem memproses *request* ke API KLHK di balik layar.
5. **Kondisi A (Lolos):** Jika koordinat di luar kawasan, sistem memunculkan indikator hijau dan mengaktifkan tombol **"Minting ke Blockchain"**.
6. **Kondisi B (Ditolak):** Jika masuk kawasan hutan, sistem menampilkan indikator merah, memunculkan nama fungsi hutan, dan mengunci tombol registrasi.

---

## 4. Kebutuhan Fungsional (Functional Requirements)

### FR-1: Form Input Koordinat Geografis
*   **Deskripsi:** Antarmuka untuk menerima input titik koordinat kebun.
*   **Spesifikasi:** 
    *   Kolom input desimal untuk *Latitude* (Rentang -11.000000 s/d 6.000000).
    *   Kolom input desimal untuk *Longitude* (Rentang 95.000000 s/d 141.000000).
    *   Validasi format angka (harus bertipe *float*).

### FR-2: Mesin Kueri Spasial (KLHK API Connector)
*   **Deskripsi:** Fungsi *back-end* (Python) yang melakukan HTTP GET Request ke server Geoportal KLHK.
*   **Endpoint Target:** `https://geoportal.menlhk.go.id/server/rest/services/SIGAP_Interaktif/Kawasan_Hutan/MapServer/0/query`
*   **Logika Penilaian Kepatuhan:**
    *   Jika respon JSON menghasilkan elemen `"features": []` (kosong), maka status = **VALID / APL**.
    *   Jika respon JSON menghasilkan elemen `"features"` bermuatan data, maka status = **INVALID**, ambil parameter `FUNGSI_KWS` dan `NAMA_KWS`.

### FR-3: Komponen Peta Interaktif (Geovisualization)
*   **Deskripsi:** Menampilkan peta lokasi berdasarkan koordinat yang diinput menggunakan pustaka `folium` di dalam komponen `streamlit-folium`.
*   **Spesifikasi:**
    *   Peta otomatis melakukan *pan/zoom* ke titik koordinat kebun.
    *   Menampilkan *marker* (pin) berwarna **Hijau** jika lahan aman, atau **Merah** jika lahan bermasalah.
    *   *Pop-up* pada pin menampilkan informasi status kawasan lahan.

### FR-4: Kontrol Gerbang Blockchain (Smart Contract Trigger)
*   **Deskripsi:** Tombol eksekusi penulisan data ke *blockchain* yang perilakunya bergantung pada hasil API KLHK.
*   **Spesifikasi:**
    *   Secara *default*, tombol "Daftarkan ke Blockchain" dalam keadaan tidak aktif (*disabled*).
    *   Tombol hanya aktif jika dan hanya jika fungsi `FR-2` mengembalikan hasil **VALID**.

---

## 5. Kebutuhan Non-Fungsional (Non-Functional Requirements)

| Kategori | Parameter Kebutuhan |
| :--- | :--- |
| **Kinerja (Performance)** | Waktu tunggu (*timeout*) untuk pemanggilan API KLHK dibatasi maksimal **10 detik**. Jika server KLHK tidak merespons, sistem harus mengeluarkan pesan *fallback* "Server KLHK Sibuk" agar aplikasi tidak mengalami *freeze/hang*. |
| **Keandalan (Reliability)** | Karena Streamlit mengeksekusi ulang skrip dari atas ke bawah pada setiap interaksi, status hasil API harus disimpan di dalam `st.session_state` agar tidak melakukan *spamming request* (pemboman API) ke server KLHK saat peta digeser. |
| **Keamanan (Security)** | Komunikasi data menggunakan protokol HTTPS terenkripsi. Tidak diperlukan manajemen *API Key* eksternal karena direktori REST KLHK bersifat publik. |

---

## 6. Spesifikasi Integrasi Teknis & Data Mapping

### Parameter Request (Outbound)
Sistem Python harus mengirimkan parameter berikut dalam format *URL-encoded query string*:
*   `geometry`: `{longitude},{latitude}`
*   `geometryType`: `esriGeometryPoint`
*   `spatialRel`: `esriSpatialRelIntersects`
*   `outFields`: `FUNGSI_KWS,NAMA_KWS`
*   `returnGeometry`: `false`
*   `f`: `json`

### Pemetaan Respon JSON (Inbound Data Mapping)
Sistem harus membaca struktur data berikut untuk percabangan logika (*conditional logic*):

```json
{
  "features": [
    {
      "attributes": {
        "FUNGSI_KWS": "Hutan Produksi Terbatas",
        "NAMA_KWS": "HP. SANGKULIRANG"
      }
    }
  ]
}