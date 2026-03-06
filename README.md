# SDR Signal Log — Middleware Pipeline
**AAMU Research Project** | SDR + Blockchain Jamming Detection

---

## What This Does

Captures radio signal data from GNU Radio (SDR hardware), detects jamming events, and permanently logs everything to a smart contract on the blockchain. Data is tamper-proof and can never be edited or deleted.

```
SDR Hardware → GNU Radio → CSV file → pipeline.py → Blockchain → log_viewer.py
```

---

## What You Need Installed

Before starting, make sure you have these installed:

- [Node.js](https://nodejs.org) — download and install the LTS version
- [Python 3.10+](https://python.org) — download and install
- [Git](https://git-scm.com) — download and install
- [VS Code](https://code.visualstudio.com) — recommended editor
- [Remix IDE](https://remix.ethereum.org) — runs in your browser, no install needed

---

## First Time Setup

### Step 1 — Clone the Repo
Open a terminal and run:
```bash
git clone https://github.com/NoMo-101/sdr_middleware.git
cd sdr_middleware/sdr_middleware
```

### Step 2 — Install Node Dependencies
```bash
npm install
```

### Step 3 — Create Python Virtual Environment
```bash
python -m venv venv
```

Activate it:
```bash
# Windows (Git Bash)
source venv/Scripts/activate

# Mac/Linux
source venv/bin/activate
```

You will see `(venv)` at the start of your terminal line when it is active.

### Step 4 — Install Python Dependencies
```bash
pip install web3 python-dotenv
```

### Step 5 — Create Your .env File
Create a new file called `.env` in the `sdr_middleware` folder and paste this in:
```
RPC_URL=http://127.0.0.1:8545
PRIVATE_KEY=0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
CONTRACT_ADDRESS=paste_after_deploying
```

> ⚠️ The private key above is a public Hardhat test key. It is safe for local development only. Never use a real wallet private key.

### Step 6 — Deploy the Contract
See the **Deploying the Contract** section below, then come back and update `CONTRACT_ADDRESS` in your `.env`.

---

## Starting Up Every Session

Every time you open a new terminal you need to follow these steps. Hardhat resets every time it restarts so you must redeploy the contract each session.

---

### Terminal 1 — Start Hardhat (keep this running the whole time)
```bash
cd sdr_middleware
npx hardhat node
```

You will see a list of test accounts and this message:
```
Started HTTP and WebSocket JSON-RPC server at http://127.0.0.1:8545/
```

Leave this terminal open and do not close it.

---

### Terminal 2 — Activate venv
```bash
cd sdr_middleware
source venv/Scripts/activate
```

---

### Remix — Deploy the Contract
You need to do this every session since Hardhat resets.

1. Go to [remix.ethereum.org](https://remix.ethereum.org)
2. Create a new file and paste in the contract code from the **Contract Code** section below
3. Click the **Solidity Compiler** tab on the left and click **Compile**
4. Click the **Deploy & Run** tab on the left
5. Change **Environment** to **Hardhat Provider**
6. Click **Deploy**
7. Copy the contract address shown under **Deployed Contracts**
8. Paste it into your `.env` file as `CONTRACT_ADDRESS`
9. Click the **ABI** button in the Compiler tab to copy it
10. Paste the ABI into `abi.json` replacing everything that was there

---

### Terminal 2 — Run the Pipeline
```bash
python pipeline.py
```

This watches the CSV file and submits every new reading to the contract automatically. Stop it at any time with `Ctrl+C`.

---

### View Everything Logged On Chain
```bash
python log_viewer.py
```

---

## Contract Code

Copy this into Remix:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract SDRSignalLog {
    struct Reading {
        address reporter;     // who submitted (your oracle/script wallet)
        uint256 freqHz;       // frequency in Hz
        int256 rssi;          // signal strength (signed, e.g. -42)
        bool detected;        // signal present?
        uint256 time;         // block timestamp
        bytes32 metaHash;     // optional: hash of extra off-chain data (IQ file, JSON, etc.)
    }

    Reading[] public readings;

    event ReadingSubmitted(
        uint256 indexed id,
        address indexed reporter,
        uint256 freqHz,
        int256 rssi,
        bool detected,
        bytes32 metaHash,
        uint256 time
    );

    function submitReading(
        uint256 freqHz,
        int256 rssi,
        bool detected,
        bytes32 metaHash
    ) external returns (uint256 id) {

        // Validate frequency range (1 Hz to 300 GHz) and RSSI range (-150 to 0 dBm)
        // Prevents garbage data from being permanently stored on-chain
        require(freqHz > 0 && freqHz <= 300_000_000_000, "Invalid frequency");
        require(rssi >= -150 && rssi <= 0, "RSSI out of range");

        id = readings.length;
        readings.push(Reading({
            reporter: msg.sender,
            freqHz: freqHz,
            rssi: rssi,
            detected: detected,
            time: block.timestamp,
            metaHash: metaHash
        }));

        emit ReadingSubmitted(id, msg.sender, freqHz, rssi, detected, metaHash, block.timestamp);
    }

    // Returns total number of readings logged — derived live from array length, never out of sync
    function totalReadings() external view returns (uint256) {
        return readings.length;
    }

    // Retrieve a single reading by its ID with bounds checking
    function getReading(uint256 id) external view returns (Reading memory) {
        require(id < readings.length, "ID out of range");
        return readings[id];
    }
}
```

---

## Project File Structure

```
sdr_middleware/
├── .env                     ← your secrets (never share or commit this)
├── .gitignore               ← keeps .env and node_modules off GitHub
├── abi.json                 ← contract ABI copied from Remix
├── connect.py               ← sets up blockchain connection
├── submit.py                ← sends readings to the contract
├── pipeline.py              ← main script, watches CSV and submits data
├── log_viewer.py            ← displays all on-chain readings in a table
├── test_submit.py           ← tests that your connection is working
├── gnu_radio_output.csv     ← signal data (real or simulated)
├── hardhat.config.js        ← Hardhat local blockchain config
├── package.json
└── venv/                    ← Python virtual environment (auto-generated)
```

---

## Simulated Test Data

If GNU Radio is not ready yet, create a file called `gnu_radio_output.csv` in the project folder with this data to simulate signal readings:

```csv
timestamp,frequency,power_db,detected
1772744311,433920000,-72,1
1772744312,433920000,-75,1
1772744313,433920000,-78,1
1772744314,433920000,-80,1
1772744315,433920000,-35,1
1772744316,433920000,-33,1
1772744317,433920000,-38,0
1772744318,433920000,-90,0
1772744319,433920000,-88,1
1772744320,433920000,-85,1
1772744321,915000000,-60,1
1772744322,915000000,-62,1
1772744323,915000000,-25,1
1772744324,915000000,-91,0
1772744325,433920000,-72,1
```

Rows 5-7 and row 13 will trigger jam detection. When GNU Radio is ready just replace this file with real output.

---

## Connecting Real GNU Radio Data

When the EE students finish their GNU Radio flowgraph:

1. Get the CSV column names from their output
2. Get the file path where GNU Radio writes the CSV
3. Update these lines at the top of `pipeline.py`:

```python
CSV_FILE = "gnu_radio_output.csv"   # change to their file path
```

And update the column names in the `run()` function:
```python
freq_hz  = int(row["frequency"])         # match their column name
rssi     = int(float(row["power_db"]))   # match their column name
detected = row["detected"] == "1"        # match their column name
```

Nothing else needs to change.

---

## Jam Detection

The pipeline automatically flags readings as jammed based on two conditions:

| Condition | Threshold | What It Means |
|---|---|---|
| RSSI above floor | > -40 dBm | Signal is abnormally strong |
| RSSI spike | ≥ 20 dBm jump | Sudden unexplained change |

These thresholds are at the top of `pipeline.py` and can be adjusted once you have real data:
```python
JAM_RSSI_SPIKE = 20
JAM_RSSI_FLOOR = -40
```

---

## Testing the Contract in Remix

Use these values to manually test `submitReading()` in Remix:

**Normal signal (should pass):**
```
freqHz:   433920000
rssi:     -72
detected: true
metaHash: 0x0000000000000000000000000000000000000000000000000000000000000000
```

**Jamming signal (should pass but flag as jam):**
```
freqHz:   433920000
rssi:     -35
detected: true
metaHash: 0x0000000000000000000000000000000000000000000000000000000000000000
```

**Bad frequency (should revert):**
```
freqHz:   0
rssi:     -72
detected: true
metaHash: 0x0000000000000000000000000000000000000000000000000000000000000000
```

**Bad RSSI (should revert):**
```
freqHz:   433920000
rssi:     50
detected: true
metaHash: 0x0000000000000000000000000000000000000000000000000000000000000000
```

---

## Current Status

- [x] Smart contract deployed and tested
- [x] Input validation working
- [x] Middleware pipeline working with simulated data
- [x] Jam detection implemented
- [x] Log viewer working
- [ ] GNU Radio integration (waiting on EE students)
- [ ] Jam detection thresholds tuned with real data
- [ ] Sepolia testnet deployment for permanent storage

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'web3'`**
Your venv is not active. Run `source venv/Scripts/activate` first.

**`Connection failed — is Hardhat node running?`**
Open a new terminal and run `npx hardhat node` first.

**`BadFunctionCallOutput` error**
Your contract address is outdated. Redeploy in Remix and update `CONTRACT_ADDRESS` in `.env`.

**`ID out of range` error**
You are trying to fetch a reading that does not exist yet. Check `totalReadings()` first.

**Pipeline submits nothing**
Make sure `gnu_radio_output.csv` exists in the project folder with the correct column names.

**Remix shows `Error while querying the provider`**
Make sure Hardhat node is running and Environment in Remix is set to Hardhat Provider.

**Warnings about LF/CRLF when running git commands**
These are harmless line ending warnings from Windows. Your files were still added correctly.

---

## Known Limitations

- Hardhat resets every time it restarts — contract must be redeployed each session
- Jam detection thresholds are estimates until real SDR data is available
- Currently runs on local testnet only, not a live network
- `.env` must be created manually on each machine — it is intentionally not on GitHub

---

## Dependencies

| Tool | Purpose |
|---|---|
| web3.py | Python library for talking to Ethereum |
| python-dotenv | Loads `.env` variables into Python |
| Hardhat | Local Ethereum blockchain for development |
| Remix IDE | Contract deployment and testing (browser based) |
| Node.js | Required to run Hardhat |
