# Laporan Analisis Skalabilitas Gas (EVM Gas consumption)

Laporan ini merekam konsumsi gas untuk fungsi agregasi dengan berbagai ukuran input batch (2 s.d 25 input).

## 1. Skalabilitas createCollectorBatch (Pengepul)
Fungsi ini mengagregasikan $N$ batch panen milik Petani.

| Jumlah Input Batch ($N$) | Konsumsi Gas (Gas Units) |
|---|---|
| 2 | 331.051 |
| 5 | 396.491 |
| 10 | 562.647 |
| 15 | 728.807 |
| 20 | 894.863 |
| 25 | 1.061.042 |

## 2. Skalabilitas createCompanyBatch (Perusahaan)
Fungsi ini mengagregasikan $N$ batch agregasi dari tingkat sebelumnya.

| Jumlah Input Batch ($N$) | Konsumsi Gas (Gas Units) |
|---|---|
| 2 | 359.191 |
| 5 | 432.830 |
| 10 | 612.664 |
| 15 | 792.489 |
| 20 | 972.210 |
| 25 | 1.152.054 |

## 3. CSV Format (Untuk Excel/Grafik)
```csv
InputSize,createCollectorBatch_Gas,createCompanyBatch_Gas
2,331051,359191
5,396491,432830
10,562647,612664
15,728807,792489
20,894863,972210
25,1061042,1152054
```
