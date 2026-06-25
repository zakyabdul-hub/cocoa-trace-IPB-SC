const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("Sistem Ketertelusuran Kakao - Gas Statistics Test", function () {
  let RoleManager, roleManager;
  let MasterData, masterData;
  let Traceability, traceability;

  let admin, penangkar, petani, pengepul, perusahaan, nonUser;

  before(async function () {
    // Mendapatkan signer (alamat akun simulasi)
    [admin, penangkar, petani, pengepul, perusahaan, nonUser] = await ethers.getSigners();

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

  describe("1. Pengujian RoleManager", function () {
    it("Admin harus berhasil memberikan role yang sesuai", async function () {
      await roleManager.connect(admin).assignRole(penangkar.address, "Penangkar");
      await roleManager.connect(admin).assignRole(petani.address, "Petani");
      await roleManager.connect(admin).assignRole(pengepul.address, "Pengepul");
      await roleManager.connect(admin).assignRole(perusahaan.address, "Perusahaan");

      expect(await roleManager.hasRole(penangkar.address, "Penangkar")).to.be.true;
      expect(await roleManager.hasRole(petani.address, "Petani")).to.be.true;
    });

    it("User tanpa role tidak dapat mengakses fungsi yang dilindungi", async function () {
      await expect(
        roleManager.connect(nonUser).assignRole(nonUser.address, "Petani")
      ).to.be.revertedWith("Akses Ditolak: Anda bukan Admin");
    });
  });

  describe("2. Pengujian MasterData", function () {
    it("Penangkar harus bisa mendaftarkan Varietas Benih baru", async function () {
      await masterData.connect(penangkar).registerVariety("VAR-01", "SK-PELEPASAN-01", 365);
      const varData = await masterData.dataVarietas("VAR-01");
      expect(varData.idVarietas).to.equal("VAR-01");
    });

    it("Petani harus bisa mendaftarkan Lahan (yang bebas deforestasi)", async function () {
      await masterData.connect(petani).registerLand(
        "LAND-01",
        "STDB-001",
        "-6.2000, 106.8166",
        5000,
        "VAR-01",
        "",
        true // isBebasDeforestasi
      );
      const landData = await masterData.dataLahan("LAND-01");
      expect(landData.idLahan).to.equal("LAND-01");
    });

    it("Lahan yang terindikasi deforestasi harus ditolak", async function () {
      await expect(
        masterData.connect(petani).registerLand(
          "LAND-02",
          "STDB-002",
          "-6.3000, 106.8200",
          3000,
          "VAR-01",
          "",
          false // isBebasDeforestasi = false
        )
      ).to.be.revertedWith("Ditolak: Lahan terindikasi masuk Kawasan Hutan!");
    });
  });

  describe("3. Pengujian Traceability", function () {
    it("Petani harus bisa mencatat Batch Panen", async function () {
      await traceability.connect(petani).createHarvestBatch("BATCH-HARVEST-01", "LAND-01", 100, true);
      const batchData = await traceability.getHarvestBatchDetail("BATCH-HARVEST-01");
      expect(batchData.idBatchPanen).to.equal("BATCH-HARVEST-01");
      expect(batchData.qtyPanen).to.equal(100n);
    });

    it("Pengepul harus bisa melakukan Agregasi Batch Panen", async function () {
      // Petani buat panen tambahan
      await traceability.connect(petani).createHarvestBatch("BATCH-HARVEST-02", "LAND-01", 150, true);

      // Pengepul melakukan agregasi BATCH-HARVEST-01 & BATCH-HARVEST-02
      await traceability.connect(pengepul).createCollectorBatch(
        "BATCH-COLLECTOR-01",
        ["BATCH-HARVEST-01", "BATCH-HARVEST-02"],
        250
      );

      const collectorBatch = await traceability.getAgregasiBatchDetail("BATCH-COLLECTOR-01");
      expect(collectorBatch.totalQty).to.equal(250n);
    });

    it("Batch yang sudah diagregasi tidak bisa digunakan kembali", async function () {
      await expect(
        traceability.connect(pengepul).createCollectorBatch(
          "BATCH-COLLECTOR-02",
          ["BATCH-HARVEST-01"],
          100
        )
      ).to.be.revertedWith("Gagal: Ada Batch Panen yang sudah diambil pengepul lain!");
    });

    it("Perusahaan harus bisa melakukan agregasi berjenjang (GudangKab -> GudangPelabuhan -> Pusat)", async function () {
      // 1. Agregasi ke GudangKab (TingkatProses 1) dari Pengepul (BATCH-COLLECTOR-01)
      await traceability.connect(perusahaan).createCompanyBatch(
        "BATCH-GUDANGKAB-01",
        ["BATCH-COLLECTOR-01"],
        1, // TingkatProses.GudangKab
        250,
        "Mutu A"
      );

      // 2. Agregasi ke GudangPelabuhan (TingkatProses 2) dari GudangKab
      await traceability.connect(perusahaan).createCompanyBatch(
        "BATCH-GUDANGPELABUHAN-01",
        ["BATCH-GUDANGKAB-01"],
        2, // TingkatProses.GudangPelabuhan
        250,
        "Mutu Ekspor"
      );

      // 3. Agregasi ke Pusat (TingkatProses 3) dari GudangPelabuhan
      await traceability.connect(perusahaan).createCompanyBatch(
        "BATCH-PUSAT-01",
        ["BATCH-GUDANGPELABUHAN-01"],
        3, // TingkatProses.Pusat
        250,
        "Mutu Super"
      );

      const pusatBatch = await traceability.getAgregasiBatchDetail("BATCH-PUSAT-01");
      expect(pusatBatch.totalQty).to.equal(250n);
    });
  });
});
