// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// 1. Membuat "Jembatan" (Interface) untuk memanggil fungsi dari RoleManager.sol
interface IRoleManager {
    function hasRole(address _user, string memory _role) external view returns (bool);
}

contract MasterData {
    // Variabel untuk menyimpan alamat kontrak RoleManager
    IRoleManager public roleManager;

    // ==========================================
    // STRUKTUR DATA (Berdasarkan Class Diagram)
    // ==========================================
    struct Varietas {
        string idVarietas;
        string skPelepasan;
        uint256 masaEdar;
        address penangkar;
        uint256 timestamp;
    }

    struct Lahan {
        string idLahan;
        string noSTDB;
        string koordinat;
        uint256 luas;
        string idVar1;
        string idVar2;
        bool isBebasDeforestasi;
        address petani;
        uint256 timestamp;
    }

    // Pemetaan (Database) untuk menyimpan aset
    mapping(string => Varietas) public dataVarietas;
    mapping(string => Lahan) public dataLahan;

    // Event untuk log riwayat
    event VarietasRegistered(string idVarietas, address indexed penangkar);
    event LahanRegistered(string idLahan, address indexed petani);

    // ==========================================
    // INISIALISASI & KEAMANAN
    // ==========================================
    
    // Saat mendeploy MasterData, kita harus memasukkan alamat RoleManager yang sudah di-deploy sebelumnya
    constructor(address _roleManagerAddress) {
        roleManager = IRoleManager(_roleManagerAddress);
    }

    // Modifier (Penjaga Pintu) agar fungsi hanya bisa diakses oleh role tertentu
    modifier onlyRole(string memory _role) {
        require(roleManager.hasRole(msg.sender, _role), string(abi.encodePacked("Akses Ditolak: Anda bukan ", _role)));
        _;
    }

    // ==========================================
    // FUNGSI REGISTRASI
    // ==========================================

    /**
     * @dev Fitur Create Aset Benih (Hanya Penangkar)
     */
    function registerVariety(
        string memory _idVar,
        string memory _skPelepasan,
        uint256 _masaEdar
    ) public onlyRole("Penangkar") {
        // Mencegah duplikasi ID (timestamp == 0 berarti data belum ada)
        require(dataVarietas[_idVar].timestamp == 0, "Gagal: ID Varietas sudah terdaftar!");

        dataVarietas[_idVar] = Varietas({
            idVarietas: _idVar,
            skPelepasan: _skPelepasan,
            masaEdar: _masaEdar,
            penangkar: msg.sender,
            timestamp: block.timestamp
        });

        emit VarietasRegistered(_idVar, msg.sender);
    }

    /**
     * @dev Fitur Create Aset Lahan (Hanya Petani)
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
        require(dataLahan[_idLahan].timestamp == 0, "Gagal: ID Lahan sudah terdaftar!");
        
        // 2. Validasi Bebas Deforestasi (Data Boolean yang dilempar dari Streamlit Python)
        require(_isBebasDeforestasi == true, "Ditolak: Lahan terindikasi masuk Kawasan Hutan!");

        // 3. Verifikasi Chaining: Apakah Benih yang diinput benar-benar ada di database?
        require(dataVarietas[_idVar1].timestamp != 0, "Varietas 1 fiktif / belum didaftarkan Penangkar!");
        
        // Cek Varietas 2 (Hanya jika diisi/tidak kosong)
        if (bytes(_idVar2).length > 0) {
            require(dataVarietas[_idVar2].timestamp != 0, "Varietas 2 fiktif / belum didaftarkan Penangkar!");
        }

        // Simpan Data Lahan secara permanen
        dataLahan[_idLahan] = Lahan({
            idLahan: _idLahan,
            noSTDB: _noSTDB,
            koordinat: _koordinat,
            luas: _luas,
            idVar1: _idVar1,
            idVar2: _idVar2,
            isBebasDeforestasi: _isBebasDeforestasi,
            petani: msg.sender,
            timestamp: block.timestamp
        });

        emit LahanRegistered(_idLahan, msg.sender);
    }
}