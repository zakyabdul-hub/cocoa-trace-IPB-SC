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
    enum TingkatProses {
        KelompokTani,       // 0
        PengepulDesa,       // 1
        PengepulKecamatan,  // 2
        PengepulKabupaten,  // 3
        PengepulLuarKab,    // 4
        GudangKab,          // 5
        GudangPelabuhan,    // 6
        Pusat               // 7
    }

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
        (,,,,,,, address pemilikLahan, uint256 lahanTimestamp) = masterData.dataLahan(_idLahan);
        require(
            lahanTimestamp != 0,
            "ID Lahan fiktif / tidak terdaftar di Master Data!"
        );
        require(
            pemilikLahan == msg.sender,
            "Bukan pemilik lahan! Anda tidak berhak mencatat panen untuk lahan ini."
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

    /// @dev Validasi apakah jalur dari tingkat sumber ke tingkat tujuan diperbolehkan
    function isValidRoute(TingkatProses _from, TingkatProses _to) public pure returns (bool) {
        uint256 f = uint256(_from);
        uint256 t = uint256(_to);
        
        // Aturan dasar: tidak boleh mundur atau sama
        if (f >= t) return false;
        
        // KelompokTani(0) / PengepulDesa(1) -> PengepulKecamatan(2) atau PengepulKabupaten(3)
        if (f <= 1) return (t == 2 || t == 3);
        
        // PengepulKecamatan(2) -> PengepulKabupaten(3)
        if (f == 2) return (t == 3);
        
        // PengepulKabupaten(3) -> semua level di atasnya (4, 5, 6, 7)
        if (f == 3) return (t >= 4);
        
        // PengepulLuarKab(4) -> level perusahaan (5, 6, 7)
        if (f == 4) return (t >= 5);
        
        // GudangKab(5) -> GudangPelabuhan(6) atau Pusat(7)
        if (f == 5) return (t >= 6);
        
        // GudangPelabuhan(6) -> Pusat(7)
        if (f == 6) return (t == 7);
        
        return false;
    }

    /// @dev Menggabungkan dua string array di memori
    function _mergeArrays(string[] memory _arr1, string[] memory _arr2) internal pure returns (string[] memory) {
        string[] memory merged = new string[](_arr1.length + _arr2.length);
        uint256 k = 0;
        for (uint256 i = 0; i < _arr1.length; i++) {
            merged[k] = _arr1[i];
            k++;
        }
        for (uint256 i = 0; i < _arr2.length; i++) {
            merged[k] = _arr2[i];
            k++;
        }
        return merged;
    }

    /**
     * @notice Pengepul menggabungkan banyak Batch Panen (L0-L1) atau Agregasi (L2-L4) menjadi satu Batch Pengepul.
     * @dev    Batch sumber akan dikunci (isAggregated = true) setelah diproses untuk mencegah klaim ganda.
     * @param _idBaru   ID unik untuk batch pengepul baru
     * @param _idSumberPanen Array ID batch panen yang dikumpulkan (hanya untuk L0-L1)
     * @param _idSumberAgregasi Array ID batch agregasi yang dikumpulkan (hanya untuk L2-L4)
     * @param _tingkat  Tingkat proses batch pengepul ini (0=KelompokTani, 1=PengepulDesa, ..., 4=PengepulLuarKab)
     * @param _totalQty Total kuantitas setelah agregasi
     */
    function createCollectorBatch(
        string memory _idBaru,
        string[] memory _idSumberPanen,
        string[] memory _idSumberAgregasi,
        TingkatProses _tingkat,
        uint256 _totalQty
    ) public onlyRole("Pengepul") {
        require(
            dataAgregasi[_idBaru].timestamp == 0,
            "ID Batch Pengepul sudah ada!"
        );
        require(
            uint256(_tingkat) <= uint256(TingkatProses.PengepulLuarKab),
            "Tingkat tidak valid untuk Pengepul! Gunakan createCompanyBatch()"
        );
        require(
            _idSumberPanen.length + _idSumberAgregasi.length > 0,
            "Minimal 1 sumber diperlukan!"
        );
        require(_totalQty > 0, "Total kuantitas harus lebih dari 0");

        // Tingkat 0-1 (KelompokTani dan PengepulDesa) hanya menerima BatchPanen
        if (uint256(_tingkat) <= 1) {
            require(
                _idSumberAgregasi.length == 0,
                "KelompokTani/PengepulDesa hanya bisa dari BatchPanen!"
            );
            for (uint256 i = 0; i < _idSumberPanen.length; i++) {
                string memory idPanen = _idSumberPanen[i];
                require(
                    dataPanen[idPanen].timestamp != 0,
                    "Ada Batch Panen fiktif di dalam Array!"
                );
                require(
                    !dataPanen[idPanen].isAggregated,
                    "Gagal: Ada Batch Panen yang sudah diambil pengepul lain!"
                );
                dataPanen[idPanen].isAggregated = true;
            }
        } else {
            // Tingkat 2-4 (Kecamatan, Kabupaten, Luar Kabupaten) hanya menerima BatchAgregasi
            require(
                _idSumberPanen.length == 0,
                "Tingkat ini hanya bisa dari BatchAgregasi!"
            );
            for (uint256 i = 0; i < _idSumberAgregasi.length; i++) {
                string memory idAsal = _idSumberAgregasi[i];
                require(
                    dataAgregasi[idAsal].timestamp != 0,
                    "Ada Batch agregasi fiktif di dalam Array!"
                );
                require(
                    !dataAgregasi[idAsal].isAggregated,
                    "Gagal: Batch agregasi sudah diproses ke tingkat berikutnya!"
                );
                require(
                    isValidRoute(dataAgregasi[idAsal].tingkat, _tingkat),
                    "Jalur rantai pasok tidak valid!"
                );
                dataAgregasi[idAsal].isAggregated = true;
            }
        }

        // Gabungkan sumber
        string[] memory allSources = _mergeArrays(_idSumberPanen, _idSumberAgregasi);

        // Simpan batch agregasi baru
        dataAgregasi[_idBaru] = BatchAgregasi({
            idBatchBaru:   _idBaru,
            idSumber:      allSources,
            tingkat:       _tingkat,
            totalQty:      _totalQty,
            parameterMutu: "Standar Pengepul",
            pemilik:       msg.sender,
            isAggregated:  false,
            timestamp:     block.timestamp
        });

        // Daftarkan ke tracker global dan per pemilik
        batchIdsByLevel[uint256(_tingkat)].push(_idBaru);
        agregasiBatchByPemilik[msg.sender].push(_idBaru);

        emit CollectorBatchCreated(_idBaru, allSources, _totalQty, msg.sender, block.timestamp);
    }

    /**
     * @notice Perusahaan (GudangKab/GudangPelabuhan/Pusat) menggabungkan batch dari tingkatan sebelumnya.
     * @dev    Validasi perutean fleksibel dilakukan melalui fungsi isValidRoute().
     * @param _idBaru   ID unik untuk batch perusahaan baru
     * @param _idSumber Array ID batch dari tingkat sebelumnya
     * @param _tingkat  Tingkat proses batch ini (5=GudangKab, 6=GudangPelabuhan, 7=Pusat)
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

        // Pastikan tingkat perusahaan valid (>= GudangKab)
        require(
            uint256(_tingkat) >= uint256(TingkatProses.GudangKab),
            "Tingkat tidak valid untuk Perusahaan! Gunakan createCollectorBatch()"
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

            // Validasi rantai berjenjang dinamis
            require(
                isValidRoute(dataAgregasi[idAsal].tingkat, _tingkat),
                "Jalur rantai pasok tidak valid!"
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
     *      - _level = 0 : Kelompok Tani
     *      - _level = 1 : Pengepul Desa
     *      - _level = 2 : Pengepul Kecamatan
     *      - _level = 3 : Pengepul Kabupaten
     *      - _level = 4 : Pengepul Luar Kabupaten
     *      - _level = 5 : Gudang Kabupaten
     *      - _level = 6 : Gudang Pelabuhan
     *      - _level = 7 : Pusat
     * @param _level Nomor tingkatan (0-7)
     * @return string[] Array ID Batch di tingkatan tersebut
     */
    function getBatchIdsByLevel(uint256 _level) public view returns (string[] memory) {
        require(_level <= uint256(TingkatProses.Pusat), "Level tidak valid! Rentang valid: 0-7");
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
     * @return tingkat       Tingkat proses (0-7)
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