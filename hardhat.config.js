require("@nomicfoundation/hardhat-toolbox");
require("hardhat-gas-reporter");

module.exports = {
  solidity: {
    version: "0.8.20",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200
      }
    }
  },
  paths: {
    sources: "./contracts", // Look for solidity files in the contracts directory
    tests: "./test",
    cache: "./cache",
    artifacts: "./artifacts"
  },
  gasReporter: {
    enabled: true,
    currency: "USD",
    token: "ETH",
    noColors: false,
    outputFile: "gas-report.txt",
    forceTerminal: true
  }
};
