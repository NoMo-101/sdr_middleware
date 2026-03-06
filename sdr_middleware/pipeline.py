import csv
import time
import json
from web3 import Web3
from dotenv import load_dotenv
import os

# ── Config ──────────────────────────────────────────
load_dotenv()

w3 = Web3(Web3.HTTPProvider(os.getenv("RPC_URL")))
with open("abi.json") as f:
    abi = json.load(f)

contract = w3.eth.contract(address=os.getenv("CONTRACT_ADDRESS"), abi=abi)
wallet   = w3.eth.account.from_key(os.getenv("PRIVATE_KEY")).address
key      = os.getenv("PRIVATE_KEY")

# ── Settings ─────────────────────────────────────────
CSV_FILE       = "gnu_radio_output.csv"
POLL_INTERVAL  = 2
JAM_RSSI_SPIKE = 20
JAM_RSSI_FLOOR = -40

# ── Jam Detection ────────────────────────────────────
def detect_jam(rssi, prev_rssi):
    if rssi > JAM_RSSI_FLOOR:
        print(f"⚠️  Jam suspected: RSSI {rssi}dBm above floor")
        return True
    if prev_rssi is not None and abs(rssi - prev_rssi) >= JAM_RSSI_SPIKE:
        print(f"⚠️  Jam suspected: RSSI spiked ({prev_rssi} → {rssi})")
        return True
    return False

# ── Submit ───────────────────────────────────────────
def submit(freq_hz, rssi, detected, jam):
    tx = contract.functions.submitReading(
        freq_hz, rssi, detected, bytes(32)
    ).build_transaction({
        "from":  wallet,
        "nonce": w3.eth.get_transaction_count(wallet),
        "gas":   200000,
    })
    signed  = w3.eth.account.sign_transaction(tx, key)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    w3.eth.wait_for_transaction_receipt(tx_hash)
    status = "🚨 JAM" if jam else "✅ OK "
    print(f"{status} | {freq_hz}Hz | {rssi}dBm | detected={detected}")

# ── Main Loop ────────────────────────────────────────
def run():
    submitted = 0
    prev_rssi = None

    print(f"🔁 Watching {CSV_FILE} every {POLL_INTERVAL}s...")
    print(f"📡 Contract: {os.getenv('CONTRACT_ADDRESS')}")
    print(f"👛 Wallet:   {wallet}\n")

    while True:
        try:
            with open(CSV_FILE) as f:
                rows = list(csv.DictReader(f))

            for row in rows[submitted:]:
                freq_hz  = int(row["frequency"])
                rssi     = int(float(row["power_db"]))
                detected = row["detected"] == "1"
                jam      = detect_jam(rssi, prev_rssi)

                submit(freq_hz, rssi, detected, jam)
                prev_rssi = rssi
                submitted += 1

        except FileNotFoundError:
            print(f"⏳ Waiting for {CSV_FILE}...")

        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    run()