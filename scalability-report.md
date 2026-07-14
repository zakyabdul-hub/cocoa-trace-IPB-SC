# Laporan Analisis Skalabilitas Gas (EVM Gas consumption)

Laporan ini merekam konsumsi gas untuk fungsi agregasi dengan berbagai ukuran input batch (2 s.d 25 input).

## 1. Skalabilitas createCollectorBatch (Pengepul)
Fungsi ini mengagregasikan $N$ batch panen milik Petani.

| Jumlah Input Batch ($N$) | Konsumsi Gas (Gas Units) |
|---|---|
| 2 | 331.329 |
| 5 | 396.769 |
| 10 | 562.925 |
| 15 | 729.085 |
| 20 | 895.140 |
| 25 | 1.061.319 |

## 2. Skalabilitas createCompanyBatch (Perusahaan)
Fungsi ini mengagregasikan $N$ batch agregasi dari tingkat sebelumnya.

| Jumlah Input Batch ($N$) | Konsumsi Gas (Gas Units) |
|---|---|
| 2 | 359.485 |
| 5 | 433.124 |
| 10 | 612.957 |
| 15 | 792.783 |
| 20 | 972.503 |
| 25 | 1.152.348 |

## 3. CSV Format (Untuk Excel/Grafik)
```csv
InputSize,createCollectorBatch_Gas,createCompanyBatch_Gas
2,331329,359485
5,396769,433124
10,562925,612957
15,729085,792783
20,895140,972503
25,1061319,1152348
```
