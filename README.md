# SDR Signal Log — Middleware Pipeline
**AAMU Research Project** | SDR + Blockchain Jamming Detection

---

## What This Does

Captures raw IQ signal data from a PlutoSDR device via GNU Radio, converts it to power/RSSI values, detects jamming events and Primary User presence, and permanently logs everything to a smart contract on the blockchain. Data is tamper-proof and can never be edited or deleted.

```
PlutoSDR Hardware → GNU Radio → IQ CSV file → pipeline.py → Blockchain → log_viewer.py
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
pip install web3 python-dotenv numpy pandas
```

### Step 5 — Create Your .env File
Create a new file called `.env` in the `sdr_middleware` folder and paste this in:
```
RPC_URL=http://127.0.0.1:8545
PRIVATE_KEY=0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
CONTRACT_ADDRESS=paste_after_deploying
CENTER_FREQ_HZ=915000000
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
2. Open your contract file
3. Click the **Solidity Compiler** tab on the left and click **Compile**
4. Click the **Deploy & Run** tab on the left
5. Change **Environment** to **Hardhat Provider**
6. Click **Deploy**
7. Copy the contract address shown under **Deployed Contracts**
8. Paste it into your `.env` file as `CONTRACT_ADDRESS`
9. Click the **ABI** button in the Compiler tab to copy it
10. Paste the ABI into `abi.json` replacing everything that was there

> ⚠️ Every time Hardhat restarts you must update CONTRACT_ADDRESS in .env AND refresh abi.json. Both must match the new deployment or the scripts will fail.

---

### Terminal 2 — Run the Pipeline
```bash
python pipeline.py
```

This processes the IQ CSV file, converts raw signal data to power values, detects jamming and Primary User events, and submits every reading to the contract. Runs once through the file and exits.

---

### View Everything Logged On Chain
```bash
python log_viewer.py
```

---

## How The Pipeline Works

### IQ Data → Power → RSSI

The PlutoSDR outputs raw IQ (In-phase/Quadrature) samples. These are the lowest level representation of a radio signal. The pipeline converts them to a usable power value using:

```
amplitude = sqrt(I² + Q²)
power_db  = 20 × log10(amplitude)
```

This gives you a signal strength in dBm that can be compared against thresholds.

### Signal Detection
A reading is marked as `detected=True` if the power is above the signal threshold:
```python
SIGNAL_THRESHOLD_DB = -16.0   # below this = noise, above = signal present
```

### Jam Detection
Two conditions trigger a jam flag:
```python
JAM_RSSI_FLOOR = -10    # signal above this is abnormally strong
JAM_RSSI_SPIKE = 5      # jump of 5+ dBm between readings is suspicious
```

### Primary User Detection
A Primary User is flagged if a signal is detected AND RSSI is above the PU threshold:
```python
PU_RSSI_THRESHOLD = -12   # above this with detection = PU likely present
```

### Meta Hash
Each reading stores a cryptographic fingerprint of its jam and PU state:
```python
meta = json.dumps({"jam": jam, "pu": pu}).encode()
metaHash = hashlib.sha256(meta).digest()
```
This allows anyone to verify the jam/PU flags for any reading by recomputing the hash.

---

## Baseline Signal Characterization

Based on real PlutoSDR captures at 915 MHz the normal signal range is:

| Metric | Value |
|---|---|
| Normal RSSI range | -12 to -15 dBm |
| Jam threshold (floor) | -10 dBm |
| PU threshold | -12 dBm |
| Signal detection floor | -16 dBm |

These thresholds will be updated as more captures with jamming events become available.

---

## Project File Structure

```
sdr_middleware/
├── .env                          ← your secrets (never share or commit this)
├── .gitignore                    ← keeps .env and node_modules off GitHub
├── abi.json                      ← contract ABI copied from Remix
├── connect.py                    ← sets up blockchain connection
├── submit.py                     ← sends readings to the contract
├── pipeline.py                   ← main script, processes IQ CSV and submits data
├── log_viewer.py                 ← displays all on-chain readings in a table
├── test_submit.py                ← tests that your connection is working
├── pluto_capture_auto_100-w-time.csv  ← real PlutoSDR IQ capture
├── gnu_radio_output.csv          ← simulated test data (legacy)
├── hardhat.config.js             ← Hardhat local blockchain config
├── package.json
└── venv/                         ← Python virtual environment (auto-generated)
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
        int256 rssi;          // signal strength (signed, e.g. -13)
        bool detected;        // signal present?
        uint256 time;         // block timestamp
        bytes32 metaHash;     // SHA256 hash of {jam, pu} state
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

## CSV Format

The pipeline expects raw IQ data in this format, as output by GNU Radio with a PlutoSDR:

```csv
Time (s),I,Q
0,0.21142578,0.002441406
1.00E-06,0.20947266,0.043945312
...
```

| Column | Type | Description |
|---|---|---|
| Time (s) | float | Sample timestamp in seconds |
| I | float | In-phase component of raw IQ signal |
| Q | float | Quadrature component of raw IQ signal |

The pipeline converts I and Q to power_db automatically. There is no need to pre-process the CSV.

---

## Connecting Real GNU Radio Data

When the EE students finish their GNU Radio flowgraph:

1. Get the file path where GNU Radio writes the CSV
2. Confirm the column names match `Time (s)`, `I`, `Q`
3. Update this line in `pipeline.py`:

```python
CSV_FILE = "pluto_capture_auto_100-w-time.csv"   # change to their file path
```

If their column names are different update these lines in `process_iq_file()`:
```python
df["power_db"] = 20 * np.log10(
    np.maximum(np.sqrt(df["I"]**2 + df["Q"]**2), 1e-10)
)
```

Nothing else needs to change.

---

## Testing the Contract in Remix

Use these values to manually test `submitReading()` in Remix:

**Normal signal (should pass):**
```
freqHz:   915000000
rssi:     -13
detected: true
metaHash: 0x0000000000000000000000000000000000000000000000000000000000000000
```

**Bad frequency (should revert):**
```
freqHz:   0
rssi:     -13
detected: true
metaHash: 0x0000000000000000000000000000000000000000000000000000000000000000
```

**Bad RSSI (should revert):**
```
freqHz:   915000000
rssi:     50
detected: true
metaHash: 0x0000000000000000000000000000000000000000000000000000000000000000
```

---

## Current Status

- [x] Smart contract deployed and tested
- [x] Input validation working
- [x] Real PlutoSDR IQ data pipeline working
- [x] IQ to power conversion implemented
- [x] Jam detection implemented and tuned to real signal range
- [x] Primary User detection implemented
- [x] Meta hash storing cryptographic proof of jam/PU state
- [x] Log viewer working
- [x] Baseline signal characterized at 915 MHz (-12 to -15 dBm)
- [ ] Capture with real jamming event (waiting on EE students)
- [ ] Threshold calibration with jamming data
- [ ] Sepolia testnet deployment for permanent storage

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'web3'`**
Your venv is not active. Run `source venv/Scripts/activate` first.

**`ModuleNotFoundError: No module named 'numpy'` or `pandas`**
Run `pip install numpy pandas` inside your active venv.

**`Connection failed — is Hardhat node running?`**
Open a new terminal and run `npx hardhat node` first.

**`BadFunctionCallOutput` error**
Your contract address is outdated. Redeploy in Remix, update `CONTRACT_ADDRESS` in `.env`, and refresh `abi.json`.

**`ID out of range` error**
You are trying to fetch a reading that does not exist yet. Check `totalReadings()` first.

**Pipeline submits nothing**
Make sure your CSV file exists in the project folder and `CSV_FILE` in `pipeline.py` matches the exact filename.

**Remix shows `Error while querying the provider`**
Make sure Hardhat node is running and Environment in Remix is set to Hardhat Provider.

**Warnings about LF/CRLF when running git commands**
These are harmless line ending warnings from Windows. Your files were still added correctly.

---

## Known Limitations

- Hardhat resets every time it restarts — contract must be redeployed each session and `.env` + `abi.json` must be updated
- Jam and PU detection thresholds based on single baseline capture — will be refined with jamming data
- Currently runs on local testnet only, not a live network
- `.env` must be created manually on each machine — it is intentionally not on GitHub
- Pipeline processes static files — live streaming from GNU Radio not yet implemented

---

## Dependencies

| Tool | Purpose |
|---|---|
| web3.py | Python library for talking to Ethereum |
| python-dotenv | Loads `.env` variables into Python |
| numpy | IQ to power conversion math |
| pandas | CSV processing and data manipulation |
| Hardhat | Local Ethereum blockchain for development |
| Remix IDE | Contract deployment and testing (browser based) |
| Node.js | Required to run Hardhat |
