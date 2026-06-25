// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title RoleManager
 * @dev Mengelola peran (role) pengguna dalam ekosistem rantai pasok kakao.
 *      Mengikuti prinsip immutability blockchain: peran tidak pernah dihapus,
 *      hanya dinonaktifkan (deactivated) dan bisa diganti dengan peran baru.
 */
contract RoleManager {

    // ==========================================
    // VARIABEL STATE
    // ==========================================

    // Alamat admin (deployer kontrak)
    address public admin;

    // Daftar role yang valid (whitelist)
    // Nilai: Penangkar, Petani, Pengepul, Perusahaan
    string[] private validRoles;

    // Struct untuk menyimpan data peran pengguna
    // isActive = false berarti peran telah dinonaktifkan (bukan dihapus)
    struct UserRoleData {
        string  role;       // Nama peran yang aktif/terakhir
        bool    isActive;   // Status aktif peran
        uint256 assignedAt; // Timestamp saat peran terakhir di-assign
        uint256 deactivatedAt; // Timestamp saat peran dinonaktifkan (0 jika masih aktif)
    }

    // Pemetaan: address pengguna → data peran
    mapping(address => UserRoleData) private userRoles;

    // Tracker: nama role → daftar address anggota
    mapping(string => address[]) private roleMembers;

    // ==========================================
    // EVENTS (semua aktivitas tercatat di block)
    // ==========================================

    /// @dev Dipancarkan saat peran diberikan kepada pengguna
    event RoleAssigned(
        address indexed user,
        string role,
        uint256 timestamp
    );

    /// @dev Dipancarkan saat peran pengguna dinonaktifkan (bukan dihapus)
    event RoleDeactivated(
        address indexed user,
        string previousRole,
        uint256 timestamp
    );

    /// @dev Dipancarkan saat hak admin dipindahkan
    event AdminTransferred(
        address indexed previousAdmin,
        address indexed newAdmin,
        uint256 timestamp
    );

    // ==========================================
    // MODIFIERS
    // ==========================================

    modifier onlyAdmin() {
        require(msg.sender == admin, "Akses Ditolak: Anda bukan Admin");
        _;
    }

    // ==========================================
    // KONSTRUKTOR
    // ==========================================

    constructor() {
        admin = msg.sender;

        // Inisialisasi whitelist role yang valid
        validRoles.push("Penangkar");
        validRoles.push("Petani");
        validRoles.push("Pengepul");
        validRoles.push("Perusahaan");
    }

    // ==========================================
    // FUNGSI INTERNAL (Helper)
    // ==========================================

    /**
     * @dev Memeriksa apakah string role termasuk dalam whitelist yang valid.
     */
    function _isValidRole(string memory _role) internal view returns (bool) {
        for (uint256 i = 0; i < validRoles.length; i++) {
            if (keccak256(abi.encode(validRoles[i])) == keccak256(abi.encode(_role))) {
                return true;
            }
        }
        return false;
    }

    // ==========================================
    // FUNGSI ADMIN
    // ==========================================

    /**
     * @notice Memberikan peran kepada pengguna (hanya Admin).
     * @dev Jika pengguna sudah punya peran aktif, peran lama otomatis dinonaktifkan
     *      sebelum peran baru diberikan. Prinsip: tidak ada data yang dihapus.
     * @param _user  Alamat wallet pengguna yang akan diberikan peran
     * @param _role  Nama peran (harus ada di whitelist: Penangkar/Petani/Pengepul/Perusahaan)
     */
    function assignRole(address _user, string memory _role) public onlyAdmin {
        require(_user != address(0), "Alamat pengguna tidak valid");
        require(_isValidRole(_role), string(abi.encodePacked(
            "Role tidak valid! Role yang tersedia: Penangkar, Petani, Pengepul, Perusahaan. Input: ", _role
        )));

        // Jika pengguna sudah punya peran aktif, tolak transaksi
        require(!userRoles[_user].isActive, "Wallet address sudah terdaftar dalam sistem");

        // Assign peran baru
        userRoles[_user] = UserRoleData({
            role:          _role,
            isActive:      true,
            assignedAt:    block.timestamp,
            deactivatedAt: 0
        });

        // Daftarkan ke tracker role members
        roleMembers[_role].push(_user);

        emit RoleAssigned(_user, _role, block.timestamp);
    }

    /**
     * @notice Menonaktifkan peran pengguna (hanya Admin).
     * @dev Mengikuti prinsip immutability blockchain: data tidak dihapus,
     *      hanya ditandai tidak aktif dengan flag isActive = false.
     *      Riwayat peran tetap tersimpan secara permanen di blockchain.
     * @param _user Alamat wallet pengguna yang akan dinonaktifkan perannya
     */
    function deactivateRole(address _user) public onlyAdmin {
        require(userRoles[_user].isActive, "Pengguna tidak memiliki peran aktif");

        string memory previousRole = userRoles[_user].role;

        // Nonaktifkan peran (TIDAK menghapus data)
        userRoles[_user].isActive      = false;
        userRoles[_user].deactivatedAt = block.timestamp;

        emit RoleDeactivated(_user, previousRole, block.timestamp);
    }

    /**
     * @notice Memindahkan hak admin ke alamat lain (hanya Admin).
     * @param _newAdmin Alamat wallet admin baru
     */
    function transferAdmin(address _newAdmin) public onlyAdmin {
        require(_newAdmin != address(0), "Alamat admin baru tidak valid");
        require(_newAdmin != admin, "Alamat baru sama dengan admin saat ini");

        address previousAdmin = admin;
        admin = _newAdmin;

        emit AdminTransferred(previousAdmin, _newAdmin, block.timestamp);
    }

    // ==========================================
    // FUNGSI VIEW (Query — tidak mengubah state)
    // ==========================================

    /**
     * @notice Mengecek apakah pengguna memiliki peran tertentu yang AKTIF.
     * @param _user  Alamat wallet pengguna
     * @param _role  Nama peran yang akan dicek
     * @return bool  true jika pengguna memiliki peran tersebut dan statusnya aktif
     */
    function hasRole(address _user, string memory _role) public view returns (bool) {
        if (!userRoles[_user].isActive) return false;
        return keccak256(abi.encode(userRoles[_user].role)) == keccak256(abi.encode(_role));
    }

    /**
     * @notice Mengambil nama peran aktif dari pengguna.
     * @param _user Alamat wallet pengguna
     * @return string Nama peran (string kosong jika tidak punya peran aktif)
     */
    function getRole(address _user) public view returns (string memory) {
        if (!userRoles[_user].isActive) return "";
        return userRoles[_user].role;
    }

    /**
     * @notice Mengambil data peran lengkap dari pengguna (termasuk status aktif & timestamp).
     * @param _user Alamat wallet pengguna
     * @return role         Nama peran terakhir
     * @return isActive     Status aktif peran
     * @return assignedAt   Timestamp saat peran terakhir di-assign
     * @return deactivatedAt Timestamp saat peran dinonaktifkan (0 jika masih aktif)
     */
    function getRoleData(address _user) public view returns (
        string memory role,
        bool isActive,
        uint256 assignedAt,
        uint256 deactivatedAt
    ) {
        UserRoleData memory data = userRoles[_user];
        return (data.role, data.isActive, data.assignedAt, data.deactivatedAt);
    }

    /**
     * @notice Mengambil daftar semua address yang pernah/saat ini memiliki role tertentu.
     * @dev List ini mencakup member yang rolenya sudah dinonaktifkan.
     *      Untuk memfilter hanya yang aktif, cek hasRole() per address.
     * @param _role Nama peran yang ingin dicari anggotanya
     * @return address[] Daftar alamat wallet anggota
     */
    function getMembersByRole(string memory _role) public view returns (address[] memory) {
        require(_isValidRole(_role), "Role tidak valid");
        return roleMembers[_role];
    }

    /**
     * @notice Mengambil daftar semua role yang terdaftar di whitelist.
     * @return string[] Daftar nama role yang valid
     */
    function getValidRoles() public view returns (string[] memory) {
        return validRoles;
    }
}