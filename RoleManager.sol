// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract RoleManager {
    
    // Alamat dompet penyebar kontrak (biasanya akun pemerintah atau sistem pusat)
    address public admin;

    // Pemetaan dari alamat dompet (wallet) ke nama peran (role)
    mapping(address => string) private userRoles;

    // Event untuk mencatat aktivitas di blockchain (berguna untuk log di Streamlit)
    event RoleAssigned(address indexed user, string role);
    event RoleRemoved(address indexed user, string previousRole);

    // Modifier: Hanya admin yang bisa mengeksekusi fungsi tertentu
    modifier onlyAdmin() {
        require(msg.sender == admin, "Akses Ditolak: Anda bukan Admin");
        _;
    }

    // Konstruktor dijalankan sekali saat kontrak di-deploy
    constructor() {
        admin = msg.sender; // Set deployer sebagai admin
    }

    /**
     * @dev Memberikan peran tertentu kepada alamat pengguna.
     * Hanya bisa dipanggil oleh Admin.
     */
    function assignRole(address _user, string memory _role) public onlyAdmin {
        userRoles[_user] = _role;
        emit RoleAssigned(_user, _role);
    }

    /**
     * @dev Menghapus peran dari alamat pengguna.
     * Hanya bisa dipanggil oleh Admin.
     */
    function removeRole(address _user) public onlyAdmin {
        string memory previousRole = userRoles[_user];
        userRoles[_user] = ""; // Mengosongkan string
        emit RoleRemoved(_user, previousRole);
    }

    /**
     * @dev Mengecek apakah pengguna memiliki peran tertentu.
     * Karena Solidity tidak bisa membandingkan string secara langsung,
     * kita harus menggunakan hash (keccak256).
     */
    function hasRole(address _user, string memory _role) public view returns (bool) {
        // Membandingkan hash dari kedua string menggunakan abi.encode
        return keccak256(abi.encode(userRoles[_user])) == keccak256(abi.encode(_role));
    }
    
    /**
     * @dev (Fungsi Tambahan) Mengambil nama peran dari pengguna.
     * Sangat berguna untuk verifikasi login/sesi di frontend Streamlit.
     */
    function getRole(address _user) public view returns (string memory) {
        return userRoles[_user];
    }
}