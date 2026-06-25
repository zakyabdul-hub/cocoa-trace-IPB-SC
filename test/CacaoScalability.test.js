const { expect } = require("chai");
const { ethers } = require("hardhat");
const fs = require("fs");
const path = require("path");

describe("Sistem Ketertelusuran Kakao - Scalability Analysis", function () {
  let RoleManager, roleManager;
  let MasterData, masterData;
  let Traceability, traceability;

  let admin, penangkar, petani, pengepul, perusahaan;
  
  // Penampung data hasil tes
  const collectorResults = [];
  const companyResults = [];

  before(async function () {
    this.timeout(120000); // Set timeout 2 menit karena melakukan banyak transaksi setup
    
    [admin, penangkar, petani, pengepul, perusahaan] = await ethers.getSigners();

    // 1. Deploy contracts
    RoleManager = await ethers.getContractFactory("RoleManager");
    roleManager = await RoleManager.deploy();
    await roleManager.waitForDeployment();

    MasterData = await ethers.getContractFactory("MasterData");
    masterData = await MasterData.deploy(await roleManager.getAddress());
    await masterData.waitForDeployment();

    Traceability = await ethers.getContractFactory("Traceability");
    traceability = await Traceability.deploy(
      await roleManager.getAddress(),
      await masterData.getAddress()
    );
    await traceability.waitForDeployment();

    // 2. Setup Roles
    await roleManager.connect(admin).assignRole(penangkar.address, "Penangkar");
    await roleManager.connect(admin).assignRole(petani.address, "Petani");
    await roleManager.connect(admin).assignRole(pengepul.address, "Pengepul");
    await roleManager.connect(admin).assignRole(perusahaan.address, "Perusahaan");

    // 3. Register Seed Variety
    await masterData.connect(penangkar).registerVariety("VAR-01", "SK-PELEPASAN-01", 365);

    // 4. Setup 154 Lands and 154 Harvest Batches (77 untuk Collector test, 77 untuk Company test)
    console.log("Memulai setup 154 Lahan dan 154 Batch Panen. Harap tunggu...");
    for (let i = 1; i <= 154; i++) {
      // Register Land
      await masterData.connect(petani).registerLand(
        `LAND-${i}`,
        `STDB-${1000 + i}`,
        `-6.2000, 106.8166`,
        5000,
        "VAR-01",
        "",
        true
      );

      // Create Harvest Batch
      await traceability.connect(petani).createHarvestBatch(
        `BATCH-HARVEST-${i}`,
        `LAND-${i}`,
        100, // Qty 100 kg
        true
      );
    }
    console.log("Setup 154 Lahan dan Batch Panen selesai dengan sukses.");
  });

  it("Menguji skalabilitas fungsi createCollectorBatch (Pengepul)", async function () {
    const sizes = [2, 5, 10, 15, 20, 25];
    let currentIndex = 1;

    for (let size of sizes) {
      const batchId = `BATCH-COLLECTOR-SCALE-${size}`;
      const sources = [];
      
      // Ambil slice batch panen yang belum ter-agregasi
      for (let i = 0; i < size; i++) {
        sources.push(`BATCH-HARVEST-${currentIndex}`);
        currentIndex++;
      }

      // Jalankan transaksi agregasi pengepul
      const tx = await traceability.connect(pengepul).createCollectorBatch(
        batchId,
        sources,
        size * 100
      );

      const receipt = await tx.wait();
      const gasUsed = receipt.gasUsed.toString();
      
      collectorResults.push({ size, gasUsed });
      console.log(`[Collector Batch Scale] Input Size: ${size} | Gas Used: ${gasUsed}`);
    }
  });

  it("Mempersiapkan 77 Batch Pengepul untuk pengujian Perusahaan", async function () {
    // Kita membutuhkan 77 batch pengepul untuk di-agregasi oleh perusahaan dengan berbagai ukuran (2+5+10+15+20+25 = 77)
    // Batch panen yang digunakan adalah BATCH-HARVEST-78 s.d BATCH-HARVEST-154
    console.log("Mempersiapkan 77 batch pengepul untuk test company...");
    for (let i = 1; i <= 77; i++) {
      const harvestIndex = 77 + i;
      await traceability.connect(pengepul).createCollectorBatch(
        `BATCH-COLLECTOR-FOR-COMPANY-${i}`,
        [`BATCH-HARVEST-${harvestIndex}`],
        100
      );
    }
  });

  it("Menguji skalabilitas fungsi createCompanyBatch (Perusahaan)", async function () {
    const sizes = [2, 5, 10, 15, 20, 25];
    let currentIndex = 1;

    for (let size of sizes) {
      const batchId = `BATCH-COMPANY-SCALE-${size}`;
      const sources = [];

      // Ambil slice batch pengepul yang belum ter-agregasi
      for (let i = 0; i < size; i++) {
        sources.push(`BATCH-COLLECTOR-FOR-COMPANY-${currentIndex}`);
        currentIndex++;
      }

      // Jalankan transaksi agregasi perusahaan (GudangKab, level 1)
      const tx = await traceability.connect(perusahaan).createCompanyBatch(
        batchId,
        sources,
        1, // TingkatProses.GudangKab
        size * 100,
        `Mutu Skala ${size}`
      );

      const receipt = await tx.wait();
      const gasUsed = receipt.gasUsed.toString();

      companyResults.push({ size, gasUsed });
      console.log(`[Company Batch Scale] Input Size: ${size} | Gas Used: ${gasUsed}`);
    }
  });

  after(function () {
    // Generate file laporan Markdown hasil pengujian skalabilitas
    const reportPath = path.join(__dirname, "../scalability-report.md");
    
    let reportContent = `# Laporan Analisis Skalabilitas Gas (EVM Gas consumption)\n\n`;
    reportContent += `Laporan ini merekam konsumsi gas untuk fungsi agregasi dengan berbagai ukuran input batch (2 s.d 25 input).\n\n`;
    
    reportContent += `## 1. Skalabilitas createCollectorBatch (Pengepul)\n`;
    reportContent += `Fungsi ini mengagregasikan $N$ batch panen milik Petani.\n\n`;
    reportContent += `| Jumlah Input Batch ($N$) | Konsumsi Gas (Gas Units) |\n`;
    reportContent += `|---|---|\n`;
    for (let res of collectorResults) {
      reportContent += `| ${res.size} | ${Number(res.gasUsed).toLocaleString("id-ID")} |\n`;
    }
    
    reportContent += `\n## 2. Skalabilitas createCompanyBatch (Perusahaan)\n`;
    reportContent += `Fungsi ini mengagregasikan $N$ batch agregasi dari tingkat sebelumnya.\n\n`;
    reportContent += `| Jumlah Input Batch ($N$) | Konsumsi Gas (Gas Units) |\n`;
    reportContent += `|---|---|\n`;
    for (let res of companyResults) {
      reportContent += `| ${res.size} | ${Number(res.gasUsed).toLocaleString("id-ID")} |\n`;
    }

    reportContent += `\n## 3. CSV Format (Untuk Excel/Grafik)\n`;
    reportContent += `\`\`\`csv\n`;
    reportContent += `InputSize,createCollectorBatch_Gas,createCompanyBatch_Gas\n`;
    for (let i = 0; i < collectorResults.length; i++) {
      reportContent += `${collectorResults[i].size},${collectorResults[i].gasUsed},${companyResults[i].gasUsed}\n`;
    }
    reportContent += `\`\`\`\n`;

    fs.writeFileSync(reportPath, reportContent, "utf8");
    console.log(`\n[SUCCESS] Laporan skalabilitas disimpan ke: ${reportPath}`);
  });
});
