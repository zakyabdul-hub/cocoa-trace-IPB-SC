// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// ==========================================
// INTERFACE — Menghubungkan ke RoleManager.sol
// ==========================================
interface IRoleManager {
    function hasRole(address _user, string memory _role) external view returns (bool);
}

/**
 * @title MasterData
 * @dev Menyimpan data master untuk Varietas Benih dan Lahan yang terdaftar.
 *      Menyediakan fungsi getter lengkap untuk mendukung tampilan list di UI Streamlit.
 */
contract MasterData {

    // ==========================================
    // VARIABEL STATE
    // ==========================================

    // Referensi ke kontrak RoleManager
    IRoleManager public roleManager;

    // ==========================================
    // STRUKTUR DATA
    // ==========================================

    struct Varietas {
        string  idVarietas;
        string  skPelepasan;
        uint256 masaEdar;
        address penangkar;
        uint256 timestamp;
    }

    struct Lahan {
        string  idLahan;
        string  noSTDB;
        string  koordinat;
        uint256 luas;
        string  idVar1;
        string  idVar2;
        bool    isBebasDeforestasi;
        address petani;
        uint256 timestamp;
    }

    // ==========================================
    // PEMETAAN (Database On-Chain)
    // ==========================================

    // Data utama — query by ID
    mapping(string => Varietas) public dataVarietas;
    mapping(string => Lahan)    public dataLahan;

    // Tracker ID — untuk mendapatkan list semua ID di UI
    string[] public allVarietasIds;
    string[] public allLahanIds;

    // Tracker per wallet — untuk filter "lahan milik saya"
    mapping(address => string[]) public lahanByPetani;
    mapping(address => string[]) public varietasByPenangkar;

    // ==========================================
    // EVENTS (tersimpan di Transaction Log block)
    // ==========================================

    /// @dev Dipancarkan saat varietas baru berhasil didaftarkan
    event VarietasRegistered(
        string  indexed idVarietas,
        string  skPelepasan,
        uint256 masaEdar,
        address indexed penangkar,
        uint256 timestamp
    );

    /// @dev Dipancarkan saat lahan baru berhasil didaftarkan
    event LahanRegistered(
        string  indexed idLahan,
        string  noSTDB,
        string  koordinat,
        uint256 luas,
        address indexed petani,
        uint256 timestamp
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
     */
    constructor(address _roleManagerAddress) {
        roleManager = IRoleManager(_roleManagerAddress);
    }

    // ==========================================
    // FUNGSI REGISTRASI (Write)
    // ==========================================

    /**
     * @notice Mendaftarkan varietas benih baru (hanya Penangkar).
     * @param _idVar        ID unik varietas
     * @param _skPelepasan  Nomor SK Pelepasan varietas
     * @param _masaEdar     Masa edar varietas (dalam hari/tahun — sesuai konvensi UI)
     */
    function registerVariety(
        string memory _idVar,
        string memory _skPelepasan,
        uint256 _masaEdar
    ) public onlyRole("Penangkar") {
        require(
            dataVarietas[_idVar].timestamp == 0,
            "Gagal: ID Varietas sudah terdaftar!"
        );
        require(bytes(_idVar).length > 0, "ID Varietas tidak boleh kosong");
        require(bytes(_skPelepasan).length > 0, "SK Pelepasan tidak boleh kosong");

        dataVarietas[_idVar] = Varietas({
            idVarietas:  _idVar,
            skPelepasan: _skPelepasan,
            masaEdar:    _masaEdar,
            penangkar:   msg.sender,
            timestamp:   block.timestamp
        });

        // Daftarkan ke tracker global dan tracker per penangkar
        allVarietasIds.push(_idVar);
        varietasByPenangkar[msg.sender].push(_idVar);

        emit VarietasRegistered(_idVar, _skPelepasan, _masaEdar, msg.sender, block.timestamp);
    }

    /**
     * @notice Mendaftarkan lahan baru (hanya Petani).
     * @param _idLahan             ID unik lahan
     * @param _noSTDB              Nomor STDB lahan
     * @param _koordinat           Koordinat geografis lahan
     * @param _luas                Luas lahan (dalam satuan yang disepakati, misal: m2)
     * @param _idVar1              ID Varietas utama yang ditanam di lahan ini
     * @param _idVar2              ID Varietas kedua (opsional, isi "" jika tidak ada)
     * @param _isBebasDeforestasi  Status bebas deforestasi (harus true untuk mendaftar)
     */
    function registerLand(
        string memory _idLahan,
        string memory _noSTDB,
        string memory _koordinat,
        uint256 _luas,
        string memory _idVar1,
        string memory _idVar2,
        bool _isBebasDeforestasi
    ) public onlyRole("Petani") {
        // 1. Cek duplikasi ID Lahan
        require(
            dataLahan[_idLahan].timestamp == 0,
            "Gagal: ID Lahan sudah terdaftar!"
        );
        require(bytes(_idLahan).length > 0, "ID Lahan tidak boleh kosong");

        // 2. Validasi status bebas deforestasi
        require(
            _isBebasDeforestasi == true,
            "Ditolak: Lahan terindikasi masuk Kawasan Hutan!"
        );

        // 3. Validasi Chaining: Varietas 1 harus terdaftar
        require(
            dataVarietas[_idVar1].timestamp != 0,
            "Varietas 1 fiktif / belum didaftarkan Penangkar!"
        );

        // 4. Validasi Varietas 2 (hanya jika diisi)
        if (bytes(_idVar2).length > 0) {
            require(
                dataVarietas[_idVar2].timestamp != 0,
                "Varietas 2 fiktif / belum didaftarkan Penangkar!"
            );
        }

        // Simpan data lahan
        dataLahan[_idLahan] = Lahan({
            idLahan:           _idLahan,
            noSTDB:            _noSTDB,
            koordinat:         _koordinat,
            luas:              _luas,
            idVar1:            _idVar1,
            idVar2:            _idVar2,
            isBebasDeforestasi: _isBebasDeforestasi,
            petani:            msg.sender,
            timestamp:         block.timestamp
        });

        // Daftarkan ke tracker global dan tracker per petani
        allLahanIds.push(_idLahan);
        lahanByPetani[msg.sender].push(_idLahan);

        emit LahanRegistered(_idLahan, _noSTDB, _koordinat, _luas, msg.sender, block.timestamp);
    }

    // ==========================================
    // FUNGSI GETTER — List & Filter (Read-only)
    // ==========================================

    /**
     * @notice Mengambil semua ID Varietas yang pernah terdaftar.
     * @dev Digunakan UI Streamlit untuk menampilkan daftar varietas.
     * @return string[] Array semua ID Varietas
     */
    function getAllVarietasIds() public view returns (string[] memory) {
        return allVarietasIds;
    }

    /**
     * @notice Mengambil jumlah total varietas yang terdaftar.
     * @return uint256 Jumlah varietas
     */
    function getTotalVarietas() public view returns (uint256) {
        return allVarietasIds.length;
    }

    /**
     * @notice Mengambil semua ID Lahan yang pernah terdaftar.
     * @dev Digunakan UI Streamlit untuk menampilkan daftar lahan.
     * @return string[] Array semua ID Lahan
     */
    function getAllLahanIds() public view returns (string[] memory) {
        return allLahanIds;
    }

    /**
     * @notice Mengambil jumlah total lahan yang terdaftar.
     * @return uint256 Jumlah lahan
     */
    function getTotalLahan() public view returns (uint256) {
        return allLahanIds.length;
    }

    /**
     * @notice Mengambil semua ID Lahan milik petani tertentu.
     * @param _petani Alamat wallet petani
     * @return string[] Array ID Lahan milik petani tersebut
     */
    function getLahanByPetani(address _petani) public view returns (string[] memory) {
        return lahanByPetani[_petani];
    }

    /**
     * @notice Mengambil semua ID Varietas yang didaftarkan oleh penangkar tertentu.
     * @param _penangkar Alamat wallet penangkar
     * @return string[] Array ID Varietas milik penangkar tersebut
     */
    function getVarietasByPenangkar(address _penangkar) public view returns (string[] memory) {
        return varietasByPenangkar[_penangkar];
    }
}