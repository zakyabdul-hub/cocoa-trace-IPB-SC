const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("Sistem Ketertelusuran Kakao - Gas Statistics Test (Multi-call)", function () {
  let RoleManager, roleManager;
  let MasterData, masterData;
  let Traceability, traceability;

  let admin, penangkar, petani, pengepul, perusahaan, nonUser;
  let extraSigners = [];

  before(async function () {
    // Mendapatkan signer (alamat akun simulasi)
    const allSigners = await ethers.getSigners();
    [admin, penangkar, petani, pengepul, perusahaan, nonUser] = allSigners;
    
    // Simpan sisa signer untuk pengujian multi-call assignRole
    extraSigners = allSigners.slice(6, 18); // 12 signer tambahan

    // 1. Deploy RoleManager
    RoleManager = await ethers.getContractFactory("RoleManager");
    roleManager = await RoleManager.deploy();
    await roleManager.waitForDeployment();

    // 2. Deploy MasterData
    MasterData = await ethers.getContractFactory("MasterData");
    masterData = await MasterData.deploy(await roleManager.getAddress());
    await masterData.waitForDeployment();

    // 3. Deploy Traceability
    Traceability = await ethers.getContractFactory("Traceability");
    traceability = await Traceability.deploy(
      await roleManager.getAddress(),
      await masterData.getAddress()
    );
    await traceability.waitForDeployment();
  });

  describe("1. Pengujian RoleManager (14+ Calls)", function () {
    it("Admin harus berhasil memberikan role ke akun utama", async function () {
      await roleManager.connect(admin).assignRole(penangkar.address, "Penangkar");
      await roleManager.connect(admin).assignRole(petani.address, "Petani");
      await roleManager.connect(admin).assignRole(pengepul.address, "Pengepul");
      await roleManager.connect(admin).assignRole(perusahaan.address, "Perusahaan");

      expect(await roleManager.hasRole(penangkar.address, "Penangkar")).to.be.true;
      expect(await roleManager.hasRole(petani.address, "Petani")).to.be.true;
    });

    it("Admin harus berhasil memberikan role ke akun-akun tambahan (loop 10+ kali)", async function () {
      const roles = ["Penangkar", "Petani", "Pengepul", "Perusahaan"];
      // Lakukan loop sebanyak 10 kali untuk memicu statistik gas min/max
      for (let i = 0; i < 10; i++) {
        const targetSigner = extraSigners[i];
        const assignedRole = roles[i % roles.length];
        await roleManager.connect(admin).assignRole(targetSigner.address, assignedRole);
        expect(await roleManager.hasRole(targetSigner.address, assignedRole)).to.be.true;
      }
    });

    it("User tanpa role tidak dapat mengakses fungsi yang dilindungi", async function () {
      await expect(
        roleManager.connect(nonUser).assignRole(nonUser.address, "Petani")
      ).to.be.revertedWith("Akses Ditolak: Anda bukan Admin");
    });
  });

  describe("2. Pengujian MasterData (10+ Calls)", function () {
    it("Penangkar harus bisa mendaftarkan beberapa Varietas Benih (loop 12 kali)", async function () {
      for (let i = 1; i <= 12; i++) {
        await masterData.connect(penangkar).registerVariety(`VAR-${i}`, `SK-PELEPASAN-${i}`, 365 + i);
        const varData = await masterData.dataVarietas(`VAR-${i}`);
        expect(varData.idVarietas).to.equal(`VAR-${i}`);
      }
    });

    it("Petani harus bisa mendaftarkan beberapa Lahan bebas deforestasi (loop 25 kali)", async function () {
      for (let i = 1; i <= 25; i++) {
        const selectedVariety = `VAR-${(i % 12) + 1}`; // Bergantian antara VAR-1 sampai VAR-12
        await masterData.connect(petani).registerLand(
          `LAND-${i}`,
          `STDB-${100 + i}`,
          `-6.2000, 106.8166`,
          5000 + i * 10,
          selectedVariety,
          "",
          true // isBebasDeforestasi
        );
        const landData = await masterData.dataLahan(`LAND-${i}`);
        expect(landData.idLahan).to.equal(`LAND-${i}`);
      }
    });

    it("Lahan yang terindikasi deforestasi harus ditolak", async function () {
      await expect(
        masterData.connect(petani).registerLand(
          "LAND-REVERTED",
          "STDB-999",
          "-6.3000, 106.8200",
          3000,
          "VAR-1",
          "",
          false // isBebasDeforestasi = false
        )
      ).to.be.revertedWith("Ditolak: Lahan terindikasi masuk Kawasan Hutan!");
    });
  });

  describe("3. Pengujian Traceability (10+ Calls & Route Validation)", function () {
    it("Petani harus bisa mencatat banyak Batch Panen (loop 25 kali)", async function () {
      for (let i = 1; i <= 25; i++) {
        await traceability.connect(petani).createHarvestBatch(
          `BATCH-HARVEST-${i}`,
          `LAND-${i}`,
          100 + i,
          true
        );
        const batchData = await traceability.getHarvestBatchDetail(`BATCH-HARVEST-${i}`);
        expect(batchData.idBatchPanen).to.equal(`BATCH-HARVEST-${i}`);
        expect(batchData.qtyPanen).to.equal(BigInt(100 + i));
      }
    });

    it("Pengepul harus bisa melakukan banyak Agregasi Batch Panen di Level 0 (loop 10 kali)", async function () {
      // Mengelompokkan 20 batch panen petani pertama ke dalam 10 batch KelompokTani (Level 0)
      for (let i = 1; i <= 10; i++) {
        const source1 = `BATCH-HARVEST-${(i - 1) * 2 + 1}`;
        const source2 = `BATCH-HARVEST-${(i - 1) * 2 + 2}`;
        const qtyTotal = BigInt((100 + ((i - 1) * 2 + 1)) + (100 + ((i - 1) * 2 + 2)));
        
        await traceability.connect(pengepul).createCollectorBatch(
          `BATCH-COLLECTOR-${i}`,
          [source1, source2],
          [], // idSumberAgregasi
          0,  // tingkat: KelompokTani (Level 0)
          qtyTotal
        );

        const collectorBatch = await traceability.getAgregasiBatchDetail(`BATCH-COLLECTOR-${i}`);
        expect(collectorBatch.totalQty).to.equal(qtyTotal);
        expect(collectorBatch.tingkat).to.equal(BigInt(0));
      }
    });

    it("Batch yang sudah diagregasi tidak bisa digunakan kembali", async function () {
      await expect(
        traceability.connect(pengepul).createCollectorBatch(
          "BATCH-COLLECTOR-FAILED",
          ["BATCH-HARVEST-1"],
          [],
          0,
          100
        )
      ).to.be.revertedWith("Gagal: Ada Batch Panen yang sudah diambil pengepul lain!");
    });

    it("Pengepul harus bisa melakukan agregasi tingkat lanjutan (0 -> 3) secara valid", async function () {
      for (let i = 1; i <= 10; i++) {
        const colBatch = await traceability.getAgregasiBatchDetail(`BATCH-COLLECTOR-${i}`);
        await traceability.connect(pengepul).createCollectorBatch(
          `BATCH-KAB-${i}`,
          [], // idSumberPanen
          [`BATCH-COLLECTOR-${i}`], // idSumberAgregasi
          3, // tingkat: Pengepul Kabupaten (Level 3)
          colBatch.totalQty
        );
        const kabBatch = await traceability.getAgregasiBatchDetail(`BATCH-KAB-${i}`);
        expect(kabBatch.tingkat).to.equal(BigInt(3));
      }
    });

    it("Percobaan agregasi dengan rute tidak valid (L0 -> L5) harus ditolak", async function () {
      // Buat batch level 0 temporary yang belum diagregasi
      await traceability.connect(pengepul).createCollectorBatch(
        "BATCH-COLLECTOR-TEMP-INVALID",
        ["BATCH-HARVEST-21"],
        [],
        0, // KelompokTani
        100
      );
      // GudangKab (L5) hanya menerima dari L3 atau L4, bukan L0 (KelompokTani) langsung
      await expect(
        traceability.connect(perusahaan).createCompanyBatch(
          "BATCH-GUDANGKAB-INVALID",
          ["BATCH-COLLECTOR-TEMP-INVALID"],
          5, // GudangKab
          100,
          "Mutu Gagal"
        )
      ).to.be.revertedWith("Jalur rantai pasok tidak valid!");
    });

    it("Perusahaan harus bisa melakukan agregasi berjenjang (Tk.5 -> Tk.6 -> Tk.7) secara valid", async function () {
      // 1. Agregasi ke GudangKab (Level 5) dari BATCH-KAB-1 s.d BATCH-KAB-10 (10 calls)
      for (let i = 1; i <= 10; i++) {
        const kabBatch = await traceability.getAgregasiBatchDetail(`BATCH-KAB-${i}`);
        await traceability.connect(perusahaan).createCompanyBatch(
          `BATCH-GUDANGKAB-${i}`,
          [`BATCH-KAB-${i}`],
          5, // GudangKab (Level 5)
          kabBatch.totalQty,
          `Mutu A-${i}`
        );
        const gkBatch = await traceability.getAgregasiBatchDetail(`BATCH-GUDANGKAB-${i}`);
        expect(gkBatch.totalQty).to.equal(kabBatch.totalQty);
      }

      // 2. Agregasi ke GudangPelabuhan (Level 6) dari BATCH-GUDANGKAB-1 s.d BATCH-GUDANGKAB-10 (10 calls)
      for (let i = 1; i <= 10; i++) {
        const gkBatch = await traceability.getAgregasiBatchDetail(`BATCH-GUDANGKAB-${i}`);
        await traceability.connect(perusahaan).createCompanyBatch(
          `BATCH-GUDANGPELABUHAN-${i}`,
          [`BATCH-GUDANGKAB-${i}`],
          6, // GudangPelabuhan (Level 6)
          gkBatch.totalQty,
          `Mutu Ekspor-${i}`
        );
        const gpBatch = await traceability.getAgregasiBatchDetail(`BATCH-GUDANGPELABUHAN-${i}`);
        expect(gpBatch.totalQty).to.equal(gkBatch.totalQty);
      }

      // 3. Agregasi ke Pusat (Level 7) dari BATCH-GUDANGPELABUHAN-1 s.d BATCH-GUDANGPELABUHAN-10 (10 calls)
      for (let i = 1; i <= 10; i++) {
        const gpBatch = await traceability.getAgregasiBatchDetail(`BATCH-GUDANGPELABUHAN-${i}`);
        await traceability.connect(perusahaan).createCompanyBatch(
          `BATCH-PUSAT-${i}`,
          [`BATCH-GUDANGPELABUHAN-${i}`],
          7, // Pusat (Level 7)
          gpBatch.totalQty,
          `Mutu Super-${i}`
        );
        const pBatch = await traceability.getAgregasiBatchDetail(`BATCH-PUSAT-${i}`);
        expect(pBatch.totalQty).to.equal(gpBatch.totalQty);
      }
    });

    it("Percobaan agregasi memutar/mundur tingkat (L7 -> L5) harus ditolak", async function () {
      await expect(
        traceability.connect(perusahaan).createCompanyBatch(
          "BATCH-GK-BACKWARD",
          ["BATCH-PUSAT-1"],
          5, // GudangKab
          100,
          "Mutu Mundur"
        )
      ).to.be.revertedWith("Jalur rantai pasok tidak valid!");
    });
  });
});
