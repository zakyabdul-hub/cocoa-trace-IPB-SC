# Laporan Analisis Skalabilitas Gas (EVM Gas consumption)

Laporan ini merekam konsumsi gas untuk fungsi agregasi dengan berbagai ukuran input batch (2 s.d 25 input).

## 1. Skalabilitas createCollectorBatch (Pengepul)
Fungsi ini mengagregasikan $N$ batch panen milik Petani.

| Jumlah Input Batch ($N$) | Konsumsi Gas (Gas Units) |
|---|---|
| 2 | 333.412 |
| 5 | 399.921 |
| 10 | 567.860 |
| 15 | 735.804 |
| 20 | 903.644 |
| 25 | 1.071.610 |

## 2. Skalabilitas createCompanyBatch (Perusahaan)
Fungsi ini mengagregasikan $N$ batch agregasi dari tingkat sebelumnya.

| Jumlah Input Batch ($N$) | Konsumsi Gas (Gas Units) |
|---|---|
| 2 | 359.449 |
| 5 | 433.394 |
| 10 | 613.738 |
| 15 | 794.073 |
| 20 | 974.304 |
| 25 | 1.154.658 |

## 3. CSV Format (Untuk Excel/Grafik)
```csv
InputSize,createCollectorBatch_Gas,createCompanyBatch_Gas
2,333412,359449
5,399921,433394
10,567860,613738
15,735804,794073
20,903644,974304
25,1071610,1154658
```
