# Implementation Plan — Status: ✅ FINAL

> Semua keputusan desain telah dikunci. Dokumen lengkap telah disimpan di project.

## File Dokumentasi

📄 **[IMPLEMENTATION_PLAN_Restrukturisasi_Rantai_Pasok.md](file:///d:/Cacao_trace_phyton/IMPLEMENTATION_PLAN_Restrukturisasi_Rantai_Pasok.md)** — Disimpan di root project untuk dokumentasi thesis

## Keputusan Final (Terkunci)

| No | Keputusan | Status |
|----|-----------|:---:|
| 1 | Role Pengepul = KelTani (sama) | ✅ |
| 2 | Petani → KelTani via BatchPanen | ✅ |
| 3 | Hierarki Perusahaan dipertahankan | ✅ |
| 4 | Mixed source didukung | ✅ |
| 5 | Migrasi data: Pengepul lama → PengepulKabupaten (3) | ✅ |
| 6 | Parameter mutu hanya di Perusahaan | ✅ |
| 7 | PengepulKab bisa langsung ke Pusat | ✅ |
| 8 | GudangKab bisa langsung ke Pusat (skip GudPelabuhan) | ✅ |

## Enum Baru (8 Level)

```
0 = KelompokTani       ┐
1 = PengepulDesa        │ createCollectorBatch()
2 = PengepulKecamatan   │ role: "Pengepul"
3 = PengepulKabupaten   │
4 = PengepulLuarKab    ┘
5 = GudangKab          ┐
6 = GudangPelabuhan     │ createCompanyBatch()
7 = Pusat              ┘ role: "Perusahaan"
```

## Siap Implementasi?

Klik **Proceed** untuk memulai implementasi perubahan sesuai plan di atas. Urutan eksekusi:

1. ⛓️ `Traceability.sol` — Enum, routing, fungsi baru
2. ⛓️ `RoleManager.sol` — Role Admin
3. ⚙️ `config.py` — Mapping, routing table
4. 🧪 `test/CacaoTraceability.test.js` — Update test
5. 🖥️ Frontend: F4, F5, F6, Admin, Dashboard
6. 📦 Compile, deploy, ABI regenerate
7. 🔄 Migrasi data
