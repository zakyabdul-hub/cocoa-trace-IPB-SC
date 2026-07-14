# 📐 Panduan Perubahan UML Diagram — Restrukturisasi Rantai Pasok Kakao

**Tanggal Dokumen:** 9 Juli 2026  
**Referensi:** `IMPLEMENTATION_PLAN_Restrukturisasi_Rantai_Pasok.md`  
**Folder UML:** `UML Diagram/`

---

## Daftar Diagram dan Status Perubahan

| No | Nama File Diagram | Tipe | Status | Prioritas |
|----|-------------------|------|:---:|:---:|
| 1 | `BPMN TO-BE.png` | BPMN | ✅ WAJIB UBAH | 🔴 Tinggi |
| 2 | `Class Diagram _cacao trace.png` | Class Diagram | ✅ WAJIB UBAH | 🔴 Tinggi |
| 3 | `Activity Diagram F4 (Agregasi Batch Petani - Pengepul).png` | Activity Diagram | ✅ WAJIB UBAH | 🔴 Tinggi |
| 4 | `Activity Diagram F5 - Agregasi Batch Perusahaan.png` | Activity Diagram | ✅ WAJIB UBAH | 🟠 Sedang |
| 5 | `Sequence Diagram F4 (Batch Pengepul).png` | Sequence Diagram | ✅ WAJIB UBAH | 🔴 Tinggi |
| 6 | `Sequence Diagram F5 (batch Perusahaan).png` | Sequence Diagram | ✅ WAJIB UBAH | 🟠 Sedang |
| 7 | `Use Case Diagram - Cacao_trace.png` | Use Case Diagram | ⚠️ MINOR UPDATE | 🟡 Rendah |
| 8 | `Sequence Diagram F6 (Riwayat Ketertelusuran).png` | Sequence Diagram | ⚠️ MINOR UPDATE | 🟡 Rendah |
| 9 | `Activty Diagram F6 - Melihat Riwayat Aset.png` | Activity Diagram | ❌ TIDAK BERUBAH | ⚪ — |
| 10 | `Activity Diagram F1 (Asset Vaeitas Benih).png` | Activity Diagram | ⚠️ MINOR UPDATE | 🟡 Rendah |
| 11 | `Activity Diagram F2 (Aset Lahan).png` | Activity Diagram | ⚠️ MINOR UPDATE | 🟡 Rendah |
| 12 | `Activity Diagram F3 (Asset Panen Petani).png` | Activity Diagram | ⚠️ MINOR UPDATE | 🟡 Rendah |
| 13 | `Sequence Diagram F1(Asset Benih).png` | Sequence Diagram | ❌ TIDAK BERUBAH | ⚪ — |
| 14 | `Sequence Diagram F2 (Aset Lahan).png` | Sequence Diagram | ❌ TIDAK BERUBAH | ⚪ — |
| 15 | `Sequence Diagram F3 (Asset Batch Petani).png` | Sequence Diagram | ❌ TIDAK BERUBAH | ⚪ — |

---

## 1. BPMN TO-BE — ✅ WAJIB UBAH (Prioritas Tinggi)

**File:** `BPMN TO-BE.png`

### Kondisi Saat Ini

Diagram BPMN saat ini memiliki **swimlane** berikut (dari bawah ke atas):
- **Penangkar Benih** → Produksi Benih → Input Pencatatan Benih
- **Petani** → Budidaya → Panen → Fermentasi → Pencatatan Batch Panen
- **Pengepul** → Penerimaan → Sortasi Kualitas → Penyimpanan → Pengiriman → Batch Pengepul
- **Gudang Kabupaten** → Penerimaan → Agregasi Batch → Input Ketertelusuran → Pengiriman Barang
- **Gudang Pelabuhan** → Penerimaan → Agregasi Batch → Input Ketertelusuran → Pengiriman Barang
- **Perusahaan/Manufacturer** → Penerimaan → Batch Eksportir → Input Ketertelusuran → Pengiriman
- **Office** → Pembuatan Kontrak → Pelatihan Petani → Input Petani Mitra
- **Customer** → Penerimaan Barang → Cek Ketertelusuran

### Perubahan yang Diperlukan

#### A. Ubah Swimlane — Tambah Tingkatan Pengepul

Swimlane **"Pengepul"** yang saat ini hanya 1 lane harus **dipecah menjadi beberapa lane**:

| Swimlane Lama | Swimlane Baru | Keterangan |
|---|---|---|
| Pengepul (1 lane) | **Kelompok Tani** | Lane baru — menerima BatchPanen dari petani |
| | **Pengepul Desa (Tk.1)** | Lane baru — menerima BatchPanen dari petani |
| | **Pengepul Kecamatan (Tk.2)** | Lane baru — menerima dari KelTani/Desa |
| | **Pengepul Kabupaten (Tk.3)** | Lane baru (pengganti "Pengepul" lama) |
| | **Pengepul Luar Kab (Tk.4)** | Lane baru — menerima dari Kab |

#### B. Ubah Alur — Dari Linear ke Bercabang

**Saat ini:** Alur linear satu arah  
```
Petani → Pengepul → Gudang Kab → Gudang Pelabuhan → Perusahaan
```

**Harus diubah menjadi:** Alur bercabang dengan gateway (decision point)
```
                  ┌──→ Kelompok Tani ──┐
Petani (BatchPanen)                     ├──→ Pengepul Kecamatan ──→ Pengepul Kabupaten ──┐
                  └──→ Pengepul Desa ──┘                     ↗                          │
                                                                                         │
                                                 ┌── Pengepul Luar Kab ←────────────────┤
                                                 │                                       │
                                                 ▼                                       ▼
                                           Gudang Kab ──→ Gudang Pelabuhan ──→ Pusat/Manufacturer
                                                    └────────────────────────────→ Pusat (langsung)
```

#### C. Tambah Gateway/Decision Point

Di diagram BPMN, tambahkan **XOR gateway (diamond)** di beberapa titik keputusan:

1. **Setelah Petani "Pengiriman Hasil Panen":**
   - Gateway: "Ke mana hasil panen dikirim?"
   - Cabang 1: Ke Kelompok Tani
   - Cabang 2: Ke Pengepul Desa (Tk.1)

2. **Setelah Kelompok Tani / Pengepul Desa:**
   - Gateway: "Kirim ke tingkat mana?"
   - Cabang 1: Ke Pengepul Kecamatan (Tk.2)
   - Cabang 2: Langsung ke Pengepul Kabupaten (Tk.3) — loncatan

3. **Setelah Pengepul Kabupaten (Tk.3):**
   - Gateway: "Kirim ke mana?"
   - Cabang 1: Ke Pengepul Luar Kab (Tk.4)
   - Cabang 2: Langsung ke Gudang Kab (perusahaan)
   - Cabang 3: Langsung ke Pusat (perusahaan tanpa gudang bertingkat)

4. **Setelah Gudang Kabupaten:**
   - Gateway: "Proses selanjutnya?"
   - Cabang 1: Ke Gudang Pelabuhan (berjenjang)
   - Cabang 2: Langsung ke Pusat (skip Gudang Pelabuhan)

#### D. Swimlane Gudang Kabupaten, Gudang Pelabuhan, Perusahaan — TETAP

Tidak ada perubahan struktural pada swimlane perusahaan. Hanya **sumber input** yang berubah:
- **Gudang Kab** sekarang bisa menerima dari **Pengepul Kab (Tk.3)** ATAU **Pengepul Luar Kab (Tk.4)** (bukan hanya dari "Pengepul")

#### E. Swimlane Penangkar Benih, Office, Customer — TIDAK BERUBAH

> [!NOTE]
> **Dikonfirmasi dari gambar interview:** Petani HANYA memiliki dua jalur aliran barang: (1) ke Kelompok Tani, dan (2) ke Pengepul Desa (Tk1). **Tidak ada jalur langsung** dari Petani ke Pengepul Kecamatan, Pengepul Kabupaten, atau tingkat perusahaan manapun.

---

## 2. Class Diagram — ✅ WAJIB UBAH (Prioritas Tinggi)

**File:** `Class Diagram _cacao trace.png`

### Kondisi Saat Ini

Diagram menampilkan:
- **RoleManager** class dengan `assignRole`, `hasRole`, `removeRole`
- **MasterData** class dengan `Varietas` dan `Lahan` struct
- **TraceabilityContract** class dengan `createHarvestBatch`, `createCollectorBatch`, `createCompanyBatch`
- **Enum TingkatProses**: `Pengepul`, `GudangKab`, `GudangPelabuhan`, `Pusat`
- **BatchAgregasi** struct
- **BatchPanen** struct

### Perubahan yang Diperlukan

#### A. Ubah Enum `TingkatProses`

```
LAMA:                          BARU:
┌──────────────────┐          ┌──────────────────────────┐
│ <<enumeration>>  │          │ <<enumeration>>          │
│ TingkatProses    │          │ TingkatProses            │
├──────────────────┤          ├──────────────────────────┤
│ Pengepul         │   →→→    │ KelompokTani         (0)│
│ GudangKab        │          │ PengepulDesa         (1)│
│ GudangPelabuhan  │          │ PengepulKecamatan    (2)│
│ Pusat            │          │ PengepulKabupaten    (3)│
└──────────────────┘          │ PengepulLuarKab      (4)│
                              │ GudangKab            (5)│
                              │ GudangPelabuhan      (6)│
                              │ Pusat*               (7)│ ← Terminal Node
                              └──────────────────────────┘

* Level 7 (Pusat) = Terminal Node, merepresentasikan:
  - Pusat / Gudang Ekspor (misal: Olam)
  - Perusahaan Pengolah Biji Kakao (langsung ke konsumen)
  - Eksportir Biji Kakao
  Ketiganya disamakan di sistem karena = tujuan akhir biji kakao mentah
```

#### B. Ubah Method Signature di `TraceabilityContract`

```
LAMA:
+createCollectorBatch(idBaru : String, idSumber : List<String>, qty : int) : void

BARU:
+createCollectorBatch(idBaru : String, idSumberPanen : List<String>,
                      idSumberAgregasi : List<String>, tingkat : TingkatProses,
                      qty : int) : void
```

#### C. Tambah Method Baru di `TraceabilityContract`

```
+isValidRoute(from : TingkatProses, to : TingkatProses) : boolean    ← BARU (internal)
+_mergeArrays(a : List<String>, b : List<String>) : List<String>     ← BARU (internal)
```

> [!IMPORTANT]
> **Perubahan v2.4:** Fungsi `migrateAgregasi()` **TIDAK JADI DITAMBAHKAN** ke Class Diagram. Keputusan v2.4 menetapkan tidak ada migrasi data lama, sehingga fungsi ini tidak dibuat di smart contract.

#### D. Ubah Validasi di `createCompanyBatch`

Catatan/note di diagram perlu diubah:
```
LAMA: "Validasi: tingkat sumber == tingkat baru - 1"
BARU: "Validasi: isValidRoute(tingkat sumber, tingkat baru)"
```

#### E. `RoleManager`, `MasterData`, `Varietas`, `Lahan`, `BatchPanen`, `BatchAgregasi` — TIDAK BERUBAH

Struct dan class ini tidak ada perubahan.

> [!NOTE]
> **Anotasi penting untuk Class Diagram:** Tambahkan note/catatan pada class diagram di dekat enum `TingkatProses` bahwa Level 7 (`Pusat`) adalah *Terminal Node* yang secara logis merepresentasikan Pusat Perusahaan, Perusahaan Pengolah Biji Kakao, maupun Eksportir Biji Kakao. Ini penting untuk memudahkan pembaca thesis memahami desain yang diambil.

---

## 3. Activity Diagram F4 (Agregasi Pengepul) — ✅ WAJIB UBAH (Prioritas Tinggi)

**File:** `Activity Diagram F4 (Agregasi Batch Petani - Pengepul).png`

### Kondisi Saat Ini

Diagram memiliki 3 swimlane:
- **Pengepul** → Mengakses menu → Memilih ID Batch Panen → Menginput data → Melihat notifikasi
- **Antarmuka Sistem** → Menerima input → Membuat ID → Memanggil SC → Menampilkan notifikasi
- **Jaringan Blockchain** → Menerima request → SC memproses → Transaksi sukses/gagal

### Perubahan yang Diperlukan

#### A. Tambah Langkah "Pilih Tingkat Pengepul" (BARU)

Setelah activity **"Mengakses menu Buat Batch Pengepul"**, tambahkan:

```
[Activity Baru] ──→ "Memilih Tingkat Pengepul"
                     (Kelompok Tani / Desa / Kecamatan / Kabupaten / Luar Kab)
```

#### B. Tambah Decision Node (Gateway) untuk Tipe Sumber

Setelah memilih tingkat, tambahkan **Decision Node (Diamond)**:

```
                    ◇ Tingkat = 0 atau 1?
                   / \
                 Ya    Tidak
                /        \
"Memilih ID         "Memilih ID
Batch Panen"        Batch Agregasi
                    dari tingkat
                    di bawahnya"
```

#### C. Update Label di Swimlane Pengepul

```
LAMA: "Memilih ID Batch Panen yang digunakan"
BARU: Tergantung decision:
  - Jika KelTani/Desa: "Memilih ID Batch Panen yang digunakan"
  - Jika Kecamatan+: "Memilih ID Batch Agregasi dari tingkat yang valid"
```

#### D. Update Label di Swimlane Antarmuka Sistem

```
LAMA: "Membuat ID Batch Pengepul"
BARU: "Membuat ID Batch [Tingkat yang Dipilih]"
```

#### E. Update Label di Swimlane Blockchain

Tambahkan validasi baru di blok SC:

```
LAMA:
"Smart Contract memproses dan menuliskan data ke dalam ledger blockchain"

BARU:
"Smart Contract memproses:
 1. Validasi role (Pengepul)
 2. Validasi tingkat (0-4)
 3. Jika tingkat 0-1: Validasi BatchPanen sumber
 4. Jika tingkat 2+: Validasi BatchAgregasi + isValidRoute()
 5. Kunci batch sumber (isAggregated = true)
 6. Simpan ke ledger blockchain"
```

#### F. Update Nama Fungsi SC

```
LAMA: createCollectorBatch(idBatchKT, [idBatchPetani], totalQty)
BARU: createCollectorBatch(idBaru, [idSumberPanen], [idSumberAgregasi], tingkat, totalQty)
```

#### G. Tambah Langkah "Generate ID" di Awal Alur (BARU — v2.3)

Sebelum activity **"Mengisi Data Agregasi Batch"**, tambahkan activity baru:

```
[Activity Baru] ──→ "Mengisi Form Generate ID Batch"
                     (Nama Entitas, Tanggal auto-fill, No-Urut auto-count)
                         │
                         ▼
                    ◇ ID valid & unik?
                   / \
                 Ya    Tidak → kembali isi form
                 │
                 ▼
                [Lanjut ke isi data batch]
```

Format ID yang dihasilkan: `[PREFIX]-[NAMA]-[DDMMYY]-[NO_URUT]`
- Prefix ditentukan otomatis berdasarkan tingkat (P1, P2, P3, P4, KELTANI)
- Spasi pada nama auto-replace menjadi `_`, auto-UPPERCASE

---

## 4. Activity Diagram F5 (Agregasi Perusahaan) — ✅ WAJIB UBAH (Prioritas Sedang)

**File:** `Activity Diagram F5 - Agregasi Batch Perusahaan.png`

### Kondisi Saat Ini

Diagram memiliki 3 section terpisah untuk 3 tingkat perusahaan:
1. **Batch Gudang Kabupaten** — memilih dari Batch Pengepul
2. **Batch Gudang Pelabuhan** — memilih dari Batch Gudang Kabupaten
3. **Batch Eksportir** — memilih dari Batch Gudang Pelabuhan

Setiap section memiliki alur yang sama: Perusahaan → Antarmuka Sistem → Blockchain.

### Perubahan yang Diperlukan

#### A. Ubah Label Sumber di Section "Batch Gudang Kabupaten"

```
LAMA:
"Menampilkan Batch Pengepul yang tersedia"
"Memilih ID Batch Pengepul yang digunakan"

BARU:
"Menampilkan Batch Pengepul Tk.3 (Kabupaten) dan Tk.4 (Luar Kab) yang tersedia"
"Memilih ID Batch sumber dari tingkat yang valid (routing check)"
```

#### B. Ubah Label Sumber di Section "Batch Gudang Pelabuhan"

```
LAMA:
"Menampilkan Batch Gudang Kabupaten yang tersedia"
"Memilih ID Batch Gudang Kabupaten yang digunakan"

BARU:
"Menampilkan Batch dari tingkat yang valid:
 - Pengepul Kabupaten (Tk.3)
 - Pengepul Luar Kab (Tk.4)
 - Gudang Kabupaten"
"Memilih ID Batch sumber (routing check via isValidRoute)"
```

#### C. Ubah Label Sumber di Section "Batch Eksportir/Pusat"

```
LAMA:
"Menampilkan Batch Gudang Pelabuhan yang tersedia"
"Memilih ID Batch Gudang Pelabuhan yang digunakan"

BARU:
"Menampilkan Batch dari tingkat yang valid:
 - Pengepul Kabupaten (Tk.3)
 - Pengepul Luar Kab (Tk.4)
 - Gudang Kabupaten
 - Gudang Pelabuhan"
"Memilih ID Batch sumber (routing check via isValidRoute)"
```

#### D. Update Validasi Blockchain di Setiap Section

```
LAMA (di setiap section):
"Validasi: tingkat batch sumber == tingkat batch baru - 1"

BARU:
"Validasi: isValidRoute(tingkat batch sumber, tingkat batch baru)"
```

#### E. Tambah Note/Catatan

Tambahkan note di diagram:
```
"Setiap tingkat perusahaan bisa menerima langsung dari
Pengepul Kabupaten (Tk.3) atau Luar Kabupaten (Tk.4),
tidak harus dari tingkat tepat di bawahnya.
Routing divalidasi oleh isValidRoute().

Level Pusat (7) = Terminal Node:
Merepresentasikan Pusat Perusahaan (Olam),
Perusahaan Pengolah Biji Kakao, atau Eksportir.
Ketiganya disamakan di sistem."
```

#### F. Tambah Langkah "Generate ID" di Awal Alur (BARU — v2.3)

Sebelum activity **"Mengisi Data Agregasi Batch"**, tambahkan activity baru:

```
[Activity Baru] ──→ "Mengisi Form Generate ID Batch"
                     (Nama Entitas, Tanggal auto-fill, No-Urut)
                         │
                         ▼
                    [ID terbentuk: GUDKAB/GUDPEL/COMPANY-[NAMA]-[DDMMYY]-[SEQ]]
```

---

## 5. Sequence Diagram F4 (Batch Pengepul) — ✅ WAJIB UBAH (Prioritas Tinggi)

**File:** `Sequence Diagram F4 (Batch Pengepul).png`

### Kondisi Saat Ini

Lifelines: `Pengepul` → `UI` → `Web3` → `SC` → `Ledger`

Alur:
1. Pengepul mengisi data: ID Batch Pengepul, [Array ID Batch Petani], Total Qty
2. UI validasi format
3. Permintaan transaksi: `createCollectorBatch(idBatchKT, [idBatchPetani], totalQty, isFermented)`
4. Web3 kirim ke SC
5. SC validasi on-chain (ID unik, role Pengepul, looping cek BatchPanen)
6. Alt: Sukses/Gagal

### Perubahan yang Diperlukan

#### A. Ubah Input Parameter di Message Pertama

```
LAMA:
"1: Mengisi Data Agregasi Batch
    (ID Batch Pengepul, [Array ID Batch Petani], Total Qty, Status Fermentasi)"

BARU:
"1: Mengisi Data Agregasi Batch
    (ID Batch Baru, Tingkat Pengepul, [Array ID Batch Panen], 
     [Array ID Batch Agregasi], Total Qty)"
```

#### B. Tambah Langkah "Pilih Tingkat" Sebelum Validasi

Tambahkan message baru dari Pengepul ke UI:
```
"0.5: Memilih Tingkat Pengepul (KelTani/Desa/Kecamatan/Kabupaten/LuarKab)"
```

#### C. Ubah Validasi Format di UI

```
LAMA:
"1.1: Validasi Format (Array ID Petani tidak boleh kosong)"

BARU:
"1.1: Validasi Format
  - Tingkat harus 0-4
  - Jika tingkat 0-1: Array BatchPanen tidak boleh kosong
  - Jika tingkat 2+: Array BatchAgregasi tidak boleh kosong"
```

#### D. Ubah Permintaan Transaksi

```
LAMA:
"1.2: Permintaan Transaksi
  createCollectorBatch(idBatchKT, [idBatchPetani], totalQty, isFermented)"

BARU:
"1.2: Permintaan Transaksi
  createCollectorBatch(idBaru, [idSumberPanen], [idSumberAgregasi], tingkat, totalQty)"
```

#### E. Ubah Validasi On-Chain di SC

```
LAMA:
"2: Eksekusi Validasi On-chain (require())
  1. Cek Apakah 'idBatchKT' unik & belum terdaftar
  2. Verifikasi Otoritas Pemanggil (Pengepul)
  3. Looping: Cek setiap item dalam [Array ID Batch Petani]
     - Apakah eksis di Aset Panen?
     - Apakah statusnya BELUM pernah diagregasi pihak lain?"

BARU:
"2: Eksekusi Validasi On-chain (require())
  1. Cek 'idBaru' unik & belum terdaftar
  2. Verifikasi Role (Pengepul)
  3. Validasi tingkat dalam range 0-4
  4. Jika tingkat 0-1:
     - Looping [idSumberPanen]: cek eksistensi + belum diagregasi
  5. Jika tingkat 2+:
     - Looping [idSumberAgregasi]: cek eksistensi + belum diagregasi
       + isValidRoute(tingkat sumber, tingkat baru)"
```

---

## 6. Sequence Diagram F5 (Batch Perusahaan) — ✅ WAJIB UBAH (Prioritas Sedang)

**File:** `Sequence Diagram F5 (batch Perusahaan).png`

### Kondisi Saat Ini

Alur:
1. Perusahaan mengisi data: ID Batch Baru, [Array ID Batch Sumber], Tingkat Proses, Total Qty, Parameter Mutu
2. UI validasi format & hierarki (Gudang Pelabuhan harus menarik data Gudang Kab)
3. Permintaan transaksi: `createCompanyBatch(idBatchBaru, [idSumber], tingkatProses, qty, mutu)`
4. SC validasi: ID unik, role, urutan tingkat berjenjang, status batch sumber
5. Alt: Sukses/Gagal

### Perubahan yang Diperlukan

#### A. Ubah Validasi Format di UI

```
LAMA:
"1.1: Validasi Format & Hirarki Tingkat Proses
  (Cth: Gudang Pelabuhan harus menarik data Gudang Kab)"

BARU:
"1.1: Validasi Format & Routing
  - Tingkat harus 5-7 (GudangKab/GudangPelabuhan/Pusat)
  - Sumber harus dari tingkat yang valid menurut routing table
  - Cth: GudangKab bisa dari Pengepul Kab(3) atau Luar Kab(4)
  - Cth: Pusat bisa dari Pengepul Kab(3)/LuarKab(4)/GudKab(5)/GudPel(6)"
```

#### B. Ubah Validasi On-Chain di SC

```
LAMA:
"2: Eksekusi Validasi On-chain (require())
  1. Cek 'idBatchBaru' unik & belum terdaftar
  2. Verifikasi Otoritas Role (Cth: Hanya role Pusat untuk produksi)
  3. Validasi Urutan Tingkat Proses berjenjang
  4. Looping: ..."

BARU:
"2: Eksekusi Validasi On-chain (require())
  1. Cek 'idBatchBaru' unik & belum terdaftar
  2. Verifikasi Role (Perusahaan)
  3. Validasi tingkat >= GudangKab (5)
  4. Looping: Cek setiap [ID Batch Sumber]
     - Eksistensi di ledger?
     - isValidRoute(tingkat sumber, tingkat baru)?
     - Belum diagregasi?"
```

#### C. Ubah Label Validasi Gagal

```
LAMA:
"7: Transaksi Gagal (Revert: 'Urutan level tidak valid / Batch telah digunakan')"

BARU:
"7: Transaksi Gagal (Revert: 'Jalur rantai pasok tidak valid / Batch telah digunakan')"
```

---

## 7. Use Case Diagram — ⚠️ MINOR UPDATE (Prioritas Rendah)

**File:** `Use Case Diagram - Cacao_trace.png`

### Kondisi Saat Ini

Aktor:
- Penangkar Benih → "Membuat Asset Varietas Benih"
- Petani → "Registrasi Lahan", "Pencatatan batch asset hasil panen kakao"
- **Pengepul / Kelompok Tani** → "Agregasi Batch Panen - Pengepul"
- Perusahaan Kakao (Gudang Kab, Gudang Pelabuhan, Eksportir/Pengolah) → "Agregasi Batch Pengepul - Gudang - Eksportir"

### Perubahan yang Diperlukan

#### A. Ubah Deskripsi Use Case "Agregasi Batch Panen - Pengepul"

```
LAMA: "Agregasi Batch Panen - Pengepul"

BARU: "Agregasi Batch Multi-Tingkat Pengepul"
       (mencakup KelTani, Desa, Kecamatan, Kabupaten, Luar Kab)
```

Atau tambahkan note di bawah use case:
```
Note: "Pengepul memilih tingkat (KelTani/Desa/Kecamatan/Kab/LuarKab).
       Tingkat 0-1: sumber dari BatchPanen
       Tingkat 2+: sumber dari BatchAgregasi tingkat di bawahnya
       Loncatan tingkat dibolehkan sesuai routing table."
```

#### B. Tambah Note pada Use Case "Agregasi Perusahaan"

```
Note: "Setiap tingkat perusahaan (GudangKab/GudPelabuhan/Pusat)
       bisa menerima langsung dari Pengepul Kab(Tk.3) atau LuarKab(Tk.4).
       Tidak harus melalui GudangKab terlebih dahulu.
       Routing divalidasi oleh isValidRoute()."
```

#### C. Aktor "Pengepul / Kelompok Tani" — TIDAK BERUBAH

Label aktor sudah mencantumkan "Pengepul / Kelompok Tani", sehingga sudah sesuai dengan keputusan bahwa role Kelompok Tani = Pengepul.

---

## 8. Sequence Diagram F6 (Riwayat Ketertelusuran) — ⚠️ MINOR UPDATE (Prioritas Rendah)

**File:** `Sequence Diagram F6 (Riwayat Ketertelusuran).png`

### Kondisi Saat Ini

Alur:
1. User input ID Batch
2. UI validasi format → kueri `getTraceabilityHistory(batchId)`
3. SC menelusuri rekursif: Array Batch Sumber → Batch Panen → Lahan → Varietas
4. Kembalikan data lengkap → render visualisasi

### Perubahan yang Diperlukan

#### A. Update Catatan di Note SC

```
LAMA:
"3: Telusuri Riwayat ke Belakang (Rekursi / Looping):
  1. Identifikasi Array Batch Sumber (Gudang/Pengepul)
  2. Lacak hingga Batch Panen Petani
  3. Lacak Data Lahan (Status Deforestasi)
  4. Lacak Varietas Benih (Penangkar)"

BARU:
"3: Telusuri Riwayat ke Belakang (Rekursi / Looping):
  1. Identifikasi Array Batch Sumber (Perusahaan/Pengepul multi-tingkat)
  2. Rekursif melalui seluruh tingkatan (Pusat→GudPel→GudKab→PengepulKab→...→KelTani)
  3. Lacak hingga Batch Panen Petani
  4. Lacak Data Lahan (Status Deforestasi)
  5. Lacak Varietas Benih (Penangkar)"
```

#### B. Update Label Input User

```
LAMA: "1: Input ID Batch (Cth: Batch Perusahaan / Pengepul)"
BARU: "1: Input ID Batch (Cth: Batch Pusat / GudangKab / PengepulKab / KelTani)"
```

**Catatan:** Logic rekursif di diagram ini **tidak berubah** secara fundamental — sudah generik. Hanya label dan contoh yang perlu diperbarui.

---

## 9. Activity Diagram F1, F2, F3 — ⚠️ MINOR UPDATE (Generate ID)

**Berlaku untuk:**
- `Activity Diagram F1 (Asset Vaeitas Benih).png`
- `Activity Diagram F2 (Aset Lahan).png`
- `Activity Diagram F3 (Asset Panen Petani).png`

### Perubahan yang Diperlukan

#### Tambah Langkah "Generate ID" di Awal Alur

Masing-masing diagram perlu menambahkan satu activity baru **sebelum** activity utama (input data):

| Diagram | Activity Baru | Format ID |
|---------|--------------|----------|
| F1 Varietas | "Mengisi Form Generate ID Varietas" | `VAR-[JENIS]-[MMYY]-[MASA_EDAR_BLN]` |
| F2 Lahan | "Mengisi Form Generate ID Lahan" | `LAHAN-[NAMA]-[NO_STDB]-[NO_URUT]` |
| F3 Panen | "Memilih ID Lahan & Generate ID Panen" | `PANEN-[DDMMYY]-[ID_LAHAN_LENGKAP]` |

Pola activity yang ditambahkan (sama untuk F1, F2, F3):

```
[Mulai]
   │
   ▼
[Activity BARU] ──→ "Mengisi Form Generate ID"
                     (input komponen ID sesuai format)
                         │
                         ▼
                    [Preview ID terbentuk]
                         │
                         ▼
               ◇ Klik "Generate"?
              / \
           Ya    Tidak → kembali edit
           │
           ▼
[Lanjut ke input data utama — ID sudah tersedia]
```

> [!NOTE]
> Sequence Diagram F1, F2, F3 **TIDAK BERUBAH** karena interaksi dengan Smart Contract (fungsi SC dan parameternya) tidak berubah. Generate ID adalah proses murni frontend yang terjadi sebelum transaksi dikirim.

---

## 10-15. Diagram yang TIDAK BERUBAH

Diagram-diagram berikut **tidak perlu diubah**:

| Diagram | Alasan Tidak Berubah |
|---------|---------------------|
| Activity Diagram F6 (Riwayat Aset) | Alur user melakukan pencarian dan melihat riwayat tidak berubah |
| Sequence Diagram F1 (Varietas) | Interaksi contract `registerVariety()` tidak berubah |
| Sequence Diagram F2 (Lahan) | Interaksi contract `registerLand()` tidak berubah |
| Sequence Diagram F3 (Batch Petani) | Interaksi contract `createHarvestBatch()` tidak berubah |

---

## Ringkasan Checklist Perubahan Diagram

### Prioritas Tinggi (Wajib sebelum implementasi)

- [ ] **BPMN TO-BE** — Tambah swimlane pengepul multi-level, ubah alur linear → bercabang dengan gateway
- [ ] **Class Diagram** — Ubah enum TingkatProses (4→8), ubah signature `createCollectorBatch`, tambah `isValidRoute()` (hapus `migrateAgregasi()`)
- [ ] **Activity Diagram F4** — Tambah langkah "Pilih Tingkat", tambah decision node sumber, tambah Generate ID, update validasi SC
- [ ] **Sequence Diagram F4** — Ubah parameter fungsi, tambah validasi routing, update validasi on-chain

### Prioritas Sedang (Bisa bersamaan dengan implementasi)

- [ ] **Activity Diagram F5** — Update label sumber, ubah validasi routing, tambah Generate ID
- [ ] **Sequence Diagram F5** — Update validasi format, ubah validasi on-chain, update label error

### Prioritas Rendah (Bisa setelah implementasi)

- [ ] **Activity Diagram F1** — Tambah langkah Generate ID Varietas (`VAR-[JENIS]-[MMYY]-[BLN]`)
- [ ] **Activity Diagram F2** — Tambah langkah Generate ID Lahan (`LAHAN-[NAMA]-[STDB]-[SEQ]`)
- [ ] **Activity Diagram F3** — Tambah langkah Generate ID Panen (`PANEN-[DDMMYY]-[ID_LAHAN]`)
- [ ] **Use Case Diagram** — Tambah note deskripsi multi-tingkat
- [ ] **Sequence Diagram F6** — Update label dan contoh ID

### Tidak Perlu Diubah

- [x] Activity Diagram F6
- [x] Sequence Diagram F1, F2, F3

---

*Dokumen ini merupakan panduan untuk menyesuaikan UML diagram berdasarkan perubahan arsitektur multi-level pengepul. Gunakan bersama dengan `IMPLEMENTATION_PLAN_Restrukturisasi_Rantai_Pasok.md` untuk referensi teknis.*
