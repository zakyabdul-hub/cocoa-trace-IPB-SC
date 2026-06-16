// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// ==========================================
// INTERFACE - Menghubungkan ke Kontrak Lain
// ==========================================

interface IRoleManager {
    function hasRole(address _user, string memory _role) external view returns (bool);
}

interface IMasterData {
    // Getter otomatis dari public mapping dataLahan di MasterData.sol
    function dataLahan(string memory _id) external view returns (
        string memory idLahan,
        string memory noSTDB,
        string memory koordinat,
        uint256 luas,
        string memory idVar1,
        string memory idVar2,
        bool isBebasDeforestasi,
        address petani,
        uint256 timestamp
    );
}

/**
 * @title Traceability
 * @dev Mencatat seluruh alur rantai pasok kakao dari panen hingga ekspor/pusat.
 *      Setiap batch dicatat secara permanen dan dapat ditelusuri asal-usulnya.
 *
 * Hierarki Tingkat Proses:
 *   0 = Pengepul        (mengambil dari Batch Panen Petani)
 *   1 = GudangKab       (mengambil dari Batch Pengepul)
 *   2 = GudangPelabuhan (mengambil dari Batch GudangKab)
 *   3 = Pusat           (mengambil dari Batch GudangPelabuhan)
 */
contract Traceability {

    // ==========================================
    // VARIABEL STATE
    // ==========================================

    IRoleManager public roleManager;
    IMasterData  public masterData;

    // Enum hierarki rantai pasok
    enum TingkatProses { Pengepul, GudangKab, GudangPelabuhan, Pusat }

    // ==========================================
    // STRUKTUR DATA
    // ==========================================

    struct BatchPanen {
        string  idBatchPanen;
        string  idLahan;
        uint256 qtyPanen;
        bool    isFermented;
        address petani;
        bool    isAggregated; // true = sudah diambil pengepul, tidak bisa diklaim ulang
        uint256 timestamp;
    }

    struct BatchAgregasi {
        string        idBatchBaru;
        string[]      idSumber;     // ID batch dari tingkat sebelumnya
        TingkatProses tingkat;
        uint256       totalQty;
        string        parameterMutu;
        address       pemilik;
        bool          isAggregated; // true = sudah diproses ke tingkat berikutnya
        uint256       timestamp;
    }

    // ==========================================
    // PEMETAAN (Database On-Chain)
    // ==========================================

    // Data utama - query by ID
    mapping(string => BatchPanen)    public dataPanen;
    mapping(string => BatchAgregasi) public dataAgregasi;

    // Tracker Global - untuk UI: tampilkan semua batch
    // Semua ID batch panen (Level 0 / Petani)
    string[] public allHarvestBatchIds;

    // Semua ID batch agregasi per tingkatan
    // Key: uint(TingkatProses) -> 0=Pengepul, 1=GudangKab, 2=GudangPelabuhan, 3=Pusat
    mapping(uint256 => string[]) public batchIdsByLevel;

    // Tracker Per Wallet - untuk UI: tampilkan batch milik saya
    // ID batch panen milik masing-masing petani
    mapping(address => string[]) public harvestBatchByPetani;

    // ID batch agregasi milik masing-masing pemilik (pengepul/perusahaan)
    mapping(address => string[]) public agregasiBatchByPemilik;

    // ==========================================
    // EVENTS (tersimpan di Transaction Log block)
    // ==========================================

    /**
     * @dev Dipancarkan saat petani membuat batch panen baru.
     *      Event ini + semua parameter-nya tersimpan permanen di block Ethereum/EVM.
     *      Dapat diquery dari Python: contract.events.HarvestBatchCreated.get_logs()
     */
    event HarvestBatchCreated(
        string  indexed idBatchPanen,
        string          idLahan,
        uint256         qtyPanen,
        bool            isFermented,
        address indexed petani,
        uint256         timestamp
    );

    /**
     * @dev Dipancarkan saat pengepul membuat batch agregasi dari batch panen petani.
     */
    event CollectorBatchCreated(
        string  indexed idBatchBaru,
        string[]        idSumber,
        uint256         totalQty,
        address indexed pengepul,
        uint256         timestamp
    );

    /**
     * @dev Dipancarkan saat perusahaan (GudangKab/GudangPelabuhan/Pusat)
     *      membuat batch agregasi dari tingkatan sebelumnya.
     */
    event CompanyBatchCreated(
        string  indexed idBatchBaru,
        string[]        idSumber,
        TingkatProses   tingkat,
        uint256         totalQty,
        string          parameterMutu,
        address indexed pemilik,
        uint256         timestamp
    );

    // ==========================================
    // MODIFIERS
    // ==========================================

    modifier onlyRole(string memory _role) {
        require(
            roleManager.hasRole(msg.sender, _role),
            string(abi.encodePacked("Akses Ditolak: Anda bukan ", _role))
        );
        _;
    }

    // ==========================================
    // KONSTRUKTOR
    // ==========================================

    /**
     * @param _roleManagerAddress Alamat kontrak RoleManager yang sudah di-deploy
     * @param _masterDataAddress  Alamat kontrak MasterData yang sudah di-deploy
     */
    constructor(address _roleManagerAddress, address _masterDataAddress) {
        roleManager = IRoleManager(_roleManagerAddress);
        masterData  = IMasterData(_masterDataAddress);
    }

    // ==========================================
    // FUNGSI TRANSAKSI (Write)
    // ==========================================

    /**
     * @notice Petani mencatat hasil panen dari lahan yang terdaftar di MasterData.
     * @param _idBatch   ID unik untuk batch panen ini
     * @param _idLahan   ID lahan asal panen (harus terdaftar di MasterData)
     * @param _qty       Jumlah hasil panen (dalam kg atau satuan yang disepakati)
     * @param _isFerment Status fermentasi kakao (true = sudah difermentasi)
     */
    function createHarvestBatch(
        string memory _idBatch,
        string memory _idLahan,
        uint256 _qty,
        bool _isFerment
    ) public onlyRole("Petani") {
        require(
            dataPanen[_idBatch].timestamp == 0,
            "ID Batch Panen sudah ada!"
        );
        require(bytes(_idBatch).length > 0, "ID Batch tidak boleh kosong");
        require(_qty > 0, "Jumlah panen harus lebih dari 0");

        // Verifikasi Chaining: pastikan ID Lahan terdaftar di MasterData
        (,,,,,,,, uint256 lahanTimestamp) = masterData.dataLahan(_idLahan);
        require(
            lahanTimestamp != 0,
            "ID Lahan fiktif / tidak terdaftar di Master Data!"
        );

        // Simpan data batch panen
        dataPanen[_idBatch] = BatchPanen({
            idBatchPanen: _idBatch,
            idLahan:      _idLahan,
            qtyPanen:     _qty,
            isFermented:  _isFerment,
            petani:       msg.sender,
            isAggregated: false,
            timestamp:    block.timestamp
        });

        // Daftarkan ke tracker global dan tracker per petani
        allHarvestBatchIds.push(_idBatch);
        harvestBatchByPetani[msg.sender].push(_idBatch);

        emit HarvestBatchCreated(_idBatch, _idLahan, _qty, _isFerment, msg.sender, block.timestamp);
    }

    /**
     * @notice Pengepul menggabungkan banyak Batch Panen menjadi satu Batch Pengepul.
     * @dev    Batch panen sumber akan dikunci (isAggregated = true) setelah diproses
     *         untuk mencegah klaim ganda.
     * @param _idBaru   ID unik untuk batch pengepul baru
     * @param _idSumber Array ID batch panen yang dikumpulkan
     * @param _totalQty Total kuantitas setelah agregasi
     */
    function createCollectorBatch(
        string memory _idBaru,
        string[] memory _idSumber,
        uint256 _totalQty
    ) public onlyRole("Pengepul") {
        require(
            dataAgregasi[_idBaru].timestamp == 0,
            "ID Batch Pengepul sudah ada!"
        );
        require(_idSumber.length > 0, "Array sumber tidak boleh kosong!");
        require(_totalQty > 0, "Total kuantitas harus lebih dari 0");

        // Validasi dan kunci setiap batch panen sumber
        for (uint256 i = 0; i < _idSumber.length; i++) {
            string memory idPanen = _idSumber[i];
            require(
                dataPanen[idPanen].timestamp != 0,
                "Ada Batch Panen fiktif di dalam Array!"
            );
            require(
                !dataPanen[idPanen].isAggregated,
                "Gagal: Ada Batch Panen yang sudah diambil pengepul lain!"
            );

            // Kunci batch panen agar tidak bisa diklaim ulang
            dataPanen[idPanen].isAggregated = true;
        }

        // Simpan batch agregasi baru
        dataAgregasi[_idBaru] = BatchAgregasi({
            idBatchBaru:   _idBaru,
            idSumber:      _idSumber,
            tingkat:       TingkatProses.Pengepul,
            totalQty:      _totalQty,
            parameterMutu: "Standar Pengepul",
            pemilik:       msg.sender,
            isAggregated:  false,
            timestamp:     block.timestamp
        });

        // Daftarkan ke tracker global (level 0 = Pengepul) dan per pemilik
        batchIdsByLevel[uint256(TingkatProses.Pengepul)].push(_idBaru);
        agregasiBatchByPemilik[msg.sender].push(_idBaru);

        emit CollectorBatchCreated(_idBaru, _idSumber, _totalQty, msg.sender, block.timestamp);
    }

    /**
     * @notice Perusahaan (GudangKab/GudangPelabuhan/Pusat) menggabungkan batch
     *         dari tingkatan sebelumnya menjadi batch baru di tingkatan yang lebih tinggi.
     * @dev    Validasi berjenjang memastikan urutan rantai pasok tidak dilangkahi.
     *         Contoh: GudangPelabuhan (tingkat 2) hanya bisa menarik dari GudangKab (tingkat 1).
     * @param _idBaru   ID unik untuk batch perusahaan baru
     * @param _idSumber Array ID batch dari tingkat sebelumnya
     * @param _tingkat  Tingkat proses batch ini (1=GudangKab, 2=GudangPelabuhan, 3=Pusat)
     * @param _totalQty Total kuantitas setelah agregasi
     * @param _mutu     Parameter mutu yang ditetapkan perusahaan
     */
    function createCompanyBatch(
        string memory _idBaru,
        string[] memory _idSumber,
        TingkatProses _tingkat,
        uint256 _totalQty,
        string memory _mutu
    ) public onlyRole("Perusahaan") {
        require(
            dataAgregasi[_idBaru].timestamp == 0,
            "ID Batch Perusahaan sudah ada!"
        );
        require(_idSumber.length > 0, "Array sumber tidak boleh kosong!");
        require(_totalQty > 0, "Total kuantitas harus lebih dari 0");

        // Pastikan tidak input level Pengepul - fungsi ini hanya untuk Perusahaan
        require(
            _tingkat != TingkatProses.Pengepul,
            "Level Pengepul tidak valid untuk fungsi ini, gunakan createCollectorBatch()"
        );

        // Validasi, kunci setiap batch sumber, dan pastikan berjenjang
        for (uint256 i = 0; i < _idSumber.length; i++) {
            string memory idAsal = _idSumber[i];
            require(
                dataAgregasi[idAsal].timestamp != 0,
                "Ada Batch sumber fiktif!"
            );
            require(
                !dataAgregasi[idAsal].isAggregated,
                "Gagal: Batch sumber sudah diproses ke tingkat berikutnya!"
            );

            // Validasi rantai berjenjang:
            // Tingkat batch baru harus = tingkat batch sumber + 1
            require(
                uint256(dataAgregasi[idAsal].tingkat) == uint256(_tingkat) - 1,
                "Urutan rantai pasok tidak valid, tingkatan batch sumber tidak sesuai!"
            );

            // Kunci batch sumber
            dataAgregasi[idAsal].isAggregated = true;
        }

        // Simpan batch agregasi perusahaan
        dataAgregasi[_idBaru] = BatchAgregasi({
            idBatchBaru:   _idBaru,
            idSumber:      _idSumber,
            tingkat:       _tingkat,
            totalQty:      _totalQty,
            parameterMutu: _mutu,
            pemilik:       msg.sender,
            isAggregated:  false,
            timestamp:     block.timestamp
        });

        // Daftarkan ke tracker global per level dan per pemilik
        batchIdsByLevel[uint256(_tingkat)].push(_idBaru);
        agregasiBatchByPemilik[msg.sender].push(_idBaru);

        emit CompanyBatchCreated(_idBaru, _idSumber, _tingkat, _totalQty, _mutu, msg.sender, block.timestamp);
    }

    // ==========================================
    // FUNGSI GETTER - List & Filter (Read-only)
    // ==========================================

    /**
     * @notice Mengambil semua ID Batch Panen yang pernah dibuat (Level Petani).
     * @dev Digunakan UI untuk menampilkan daftar semua batch panen.
     * @return string[] Array semua ID Batch Panen
     */
    function getAllHarvestBatchIds() public view returns (string[] memory) {
        return allHarvestBatchIds;
    }

    /**
     * @notice Mengambil jumlah total batch panen yang terdaftar.
     * @return uint256 Jumlah batch panen
     */
    function getTotalHarvestBatches() public view returns (uint256) {
        return allHarvestBatchIds.length;
    }

    /**
     * @notice Mengambil semua ID Batch berdasarkan tingkatan proses.
     * @dev Gunakan ini untuk menampilkan list batch per level di UI:
     *      - _level = 0 : Semua batch Pengepul
     *      - _level = 1 : Semua batch Gudang Kabupaten
     *      - _level = 2 : Semua batch Gudang Pelabuhan
     *      - _level = 3 : Semua batch Pusat
     * @param _level Nomor tingkatan (0-3)
     * @return string[] Array ID Batch di tingkatan tersebut
     */
    function getBatchIdsByLevel(uint256 _level) public view returns (string[] memory) {
        require(_level <= uint256(TingkatProses.Pusat), "Level tidak valid! Rentang valid: 0-3");
        return batchIdsByLevel[_level];
    }

    /**
     * @notice Mengambil jumlah batch pada tingkatan tertentu.
     * @param _level Nomor tingkatan (0-3)
     * @return uint256 Jumlah batch di level tersebut
     */
    function getTotalBatchByLevel(uint256 _level) public view returns (uint256) {
        require(_level <= uint256(TingkatProses.Pusat), "Level tidak valid!");
        return batchIdsByLevel[_level].length;
    }

    /**
     * @notice Mengambil semua ID Batch Panen milik petani tertentu.
     * @param _petani Alamat wallet petani
     * @return string[] Array ID Batch Panen milik petani tersebut
     */
    function getMyHarvestBatches(address _petani) public view returns (string[] memory) {
        return harvestBatchByPetani[_petani];
    }

    /**
     * @notice Mengambil semua ID Batch Agregasi milik pemilik tertentu.
     * @param _pemilik Alamat wallet pemilik (Pengepul atau Perusahaan)
     * @return string[] Array ID Batch Agregasi milik pemilik tersebut
     */
    function getMyAgregasiBatches(address _pemilik) public view returns (string[] memory) {
        return agregasiBatchByPemilik[_pemilik];
    }

    /**
     * @notice Mengambil array idSumber dari sebuah batch agregasi.
     * @dev Diperlukan karena Solidity tidak bisa mengembalikan array
     *      melalui getter mapping otomatis.
     * @param _idBatch ID batch agregasi yang ingin ditelusuri sumbernya
     * @return string[] Array ID batch sumber
     */
    function getSumberAgregasi(string memory _idBatch) public view returns (string[] memory) {
        return dataAgregasi[_idBatch].idSumber;
    }

    /**
     * @notice Mengambil detail lengkap sebuah batch panen.
     * @param _idBatch ID Batch Panen
     * @return idBatchPanen  ID batch panen
     * @return idLahan       ID lahan asal
     * @return qtyPanen      Jumlah panen
     * @return isFermented   Status fermentasi
     * @return petani        Alamat wallet petani
     * @return isAggregated  Status apakah sudah diagregasi
     * @return timestamp     Waktu pencatatan
     */
    function getHarvestBatchDetail(string memory _idBatch) public view returns (
        string memory idBatchPanen,
        string memory idLahan,
        uint256 qtyPanen,
        bool isFermented,
        address petani,
        bool isAggregated,
        uint256 timestamp
    ) {
        BatchPanen memory b = dataPanen[_idBatch];
        require(b.timestamp != 0, "Batch Panen tidak ditemukan!");
        return (b.idBatchPanen, b.idLahan, b.qtyPanen, b.isFermented, b.petani, b.isAggregated, b.timestamp);
    }

    /**
     * @notice Mengambil detail lengkap sebuah batch agregasi (tanpa array sumber).
     * @dev Untuk array sumber, gunakan getSumberAgregasi() secara terpisah.
     * @param _idBatch ID Batch Agregasi
     * @return idBatchBaru   ID batch ini
     * @return tingkat       Tingkat proses (0-3)
     * @return totalQty      Total kuantitas
     * @return parameterMutu Parameter mutu
     * @return pemilik       Alamat pemilik batch
     * @return isAggregated  Status apakah sudah diproses ke tingkat berikutnya
     * @return timestamp     Waktu pencatatan
     */
    function getAgregasiBatchDetail(string memory _idBatch) public view returns (
        string memory idBatchBaru,
        TingkatProses tingkat,
        uint256 totalQty,
        string memory parameterMutu,
        address pemilik,
        bool isAggregated,
        uint256 timestamp
    ) {
        BatchAgregasi memory b = dataAgregasi[_idBatch];
        require(b.timestamp != 0, "Batch Agregasi tidak ditemukan!");
        return (b.idBatchBaru, b.tingkat, b.totalQty, b.parameterMutu, b.pemilik, b.isAggregated, b.timestamp);
    }
}