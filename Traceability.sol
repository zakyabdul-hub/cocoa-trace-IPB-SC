// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// ==========================================
// INTERFACE (Menghubungkan ke Kontrak Lain)
// ==========================================
interface IRoleManager {
    function hasRole(address _user, string memory _role) external view returns (bool);
}

interface IMasterData {
    // Fungsi bawaan (getter) dari public mapping dataLahan di MasterData.sol
    // Mengembalikan 9 nilai sesuai struktur struct Lahan
    function dataLahan(string memory _id) external view returns (
        string memory, string memory, string memory, uint256, 
        string memory, string memory, bool, address, uint256
    );
}

contract Traceability {
    IRoleManager public roleManager;
    IMasterData public masterData;

    // Enum untuk hierarki rantai pasok (0 = Pengepul, 1 = GudangKab, 2 = GudangPelabuhan, 3 = Pusat)
    enum TingkatProses { Pengepul, GudangKab, GudangPelabuhan, Pusat }

    // ==========================================
    // STRUKTUR DATA
    // ==========================================
    struct BatchPanen {
        string idBatchPanen;
        string idLahan;
        uint256 qtyPanen;
        bool isFermented;
        address petani;
        bool isAggregated; // KUNCI: Pengaman klaim ganda
        uint256 timestamp;
    }

    struct BatchAgregasi {
        string idBatchBaru;
        string[] idSumber;
        TingkatProses tingkat;
        uint256 totalQty;
        string parameterMutu;
        address pemilik;
        bool isAggregated; // KUNCI: Pengaman klaim ganda antar perusahaan
        uint256 timestamp;
    }

    mapping(string => BatchPanen) public dataPanen;
    mapping(string => BatchAgregasi) public dataAgregasi;

    // ==========================================
    // INISIALISASI & MODIFIER
    // ==========================================
    constructor(address _roleManagerAddress, address _masterDataAddress) {
        roleManager = IRoleManager(_roleManagerAddress);
        masterData = IMasterData(_masterDataAddress);
    }

    modifier onlyRole(string memory _role) {
        require(roleManager.hasRole(msg.sender, _role), string(abi.encodePacked("Akses Ditolak: Anda bukan ", _role)));
        _;
    }

    // ==========================================
    // FUNGSI TRANSAKSI & AGREGASI
    // ==========================================

    /**
     * @dev 1. Petani mencatat hasil panen dari lahan yang terdaftar.
     */
    function createHarvestBatch(
        string memory _idBatch,
        string memory _idLahan,
        uint256 _qty,
        bool _isFerment
    ) public onlyRole("Petani") {
        require(dataPanen[_idBatch].timestamp == 0, "ID Batch Panen sudah ada!");

        // Memanggil MasterData untuk mengecek apakah ID Lahan ada.
        // Kita hanya mengambil variabel ke-9 (timestamp) untuk verifikasi eksistensi.
        (,,,,,,,, uint256 lahanTimestamp) = masterData.dataLahan(_idLahan);
        require(lahanTimestamp != 0, "ID Lahan fiktif / tidak terdaftar di Master Data!");

        dataPanen[_idBatch] = BatchPanen({
            idBatchPanen: _idBatch,
            idLahan: _idLahan,
            qtyPanen: _qty,
            isFermented: _isFerment,
            petani: msg.sender,
            isAggregated: false,
            timestamp: block.timestamp
        });
    }

    /**
     * @dev 2. Pengepul menggabungkan banyak Batch Panen (Array) menjadi satu Batch Pengepul.
     */
    function createCollectorBatch(
        string memory _idBaru,
        string[] memory _idSumber,
        uint256 _totalQty
    ) public onlyRole("Pengepul") {
        require(dataAgregasi[_idBaru].timestamp == 0, "ID Batch Pengepul sudah ada!");
        require(_idSumber.length > 0, "Array sumber tidak boleh kosong!");

        // Looping untuk memvalidasi dan mengunci (update state) setiap Batch Panen milik Petani
        for (uint256 i = 0; i < _idSumber.length; i++) {
            string memory idPanen = _idSumber[i];
            require(dataPanen[idPanen].timestamp != 0, "Ada Batch Panen fiktif di dalam Array!");
            require(dataPanen[idPanen].isAggregated == false, "Gagal: Ada Batch Panen yang sudah diambil pengepul lain!");
            
            // KUNCI KEAMANAN: Tandai aset lama telah diagregasi agar tidak bisa dipakai 2 kali
            dataPanen[idPanen].isAggregated = true; 
        }

        dataAgregasi[_idBaru] = BatchAgregasi({
            idBatchBaru: _idBaru,
            idSumber: _idSumber,
            tingkat: TingkatProses.Pengepul,
            totalQty: _totalQty,
            parameterMutu: "Standar Pengepul",
            pemilik: msg.sender,
            isAggregated: false,
            timestamp: block.timestamp
        });
    }

    /**
     * @dev 3. Perusahaan (Gudang/Pusat) menggabungkan batch dari tingkatan sebelumnya.
     */
    function createCompanyBatch(
        string memory _idBaru,
        string[] memory _idSumber,
        TingkatProses _tingkat,
        uint256 _totalQty,
        string memory _mutu
    ) public onlyRole("Perusahaan") {
        require(dataAgregasi[_idBaru].timestamp == 0, "ID Batch Perusahaan sudah ada!");
        require(_idSumber.length > 0, "Array sumber tidak boleh kosong!");
        // Pastikan tidak ada yang input level Pengepul di fungsi ini
        require(_tingkat != TingkatProses.Pengepul, "Level tidak valid untuk fungsi ini!"); 

        for (uint256 i = 0; i < _idSumber.length; i++) {
            string memory idAsal = _idSumber[i];
            require(dataAgregasi[idAsal].timestamp != 0, "Ada Batch sumber fiktif!");
            require(dataAgregasi[idAsal].isAggregated == false, "Gagal: Batch sumber sudah diproses sebelumnya!");
            
            // Validasi rantai berjenjang (Misal: Gudang Pelabuhan (2) HANYA BISA menarik data dari Gudang Kab (1))
            require(uint(dataAgregasi[idAsal].tingkat) == uint(_tingkat) - 1, "Urutan rantai pasok melompat/tidak valid!");

            // Kunci aset sumber
            dataAgregasi[idAsal].isAggregated = true;
        }

        dataAgregasi[_idBaru] = BatchAgregasi({
            idBatchBaru: _idBaru,
            idSumber: _idSumber,
            tingkat: _tingkat,
            totalQty: _totalQty,
            parameterMutu: _mutu,
            pemilik: msg.sender,
            isAggregated: false,
            timestamp: block.timestamp
        });
    }

    // ==========================================
    // FUNGSI GETTER (Dukungan Traceability untuk Frontend)
    // ==========================================
    
    // Fungsi ini khusus agar Python/Streamlit mudah menarik array idSumber
    function getSumberAgregasi(string memory _idBatch) public view returns (string[] memory) {
        return dataAgregasi[_idBatch].idSumber;
    }
}