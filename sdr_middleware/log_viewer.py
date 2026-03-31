# log_viewer.py
import json
import hashlib
from web3 import Web3
from dotenv import load_dotenv
from datetime import datetime
import os

load_dotenv()

w3 = Web3(Web3.HTTPProvider(os.getenv("RPC_URL")))
with open("abi.json") as f:
    abi = json.load(f)

contract = w3.eth.contract(address=os.getenv("CONTRACT_ADDRESS"), abi=abi)

# ── Must match pipeline.py ────────────────────────────
JAM_RSSI_FLOOR    = -10
JAM_RSSI_SPIKE    = 5
PU_RSSI_THRESHOLD = -12

def decode_meta_hash(meta_bytes, jam, pu):
    """Verify the stored metaHash matches what we'd expect for jam/pu combo."""
    expected = hashlib.sha256(
        json.dumps({"jam": jam, "pu": pu}).encode()
    ).digest()  
    return meta_bytes == expected

def get_status(rssi, detected, prev_rssi, meta_bytes):
    jam = rssi > JAM_RSSI_FLOOR or (
        prev_rssi is not None and abs(rssi - prev_rssi) >= JAM_RSSI_SPIKE
    )
    pu = detected and rssi > PU_RSSI_THRESHOLD

    # Cross-check against stored metaHash
    verified = decode_meta_hash(meta_bytes, jam, pu)
    tag = "⚠️ HASH MISMATCH" if not verified else ""

    if jam:
        return f"🚨 JAM {tag}"
    elif pu:
        return f"📡 PU  {tag}"
    else:
        return f"✅ OK  {tag}"

def view_logs():
    total = contract.functions.totalReadings().call()

    print("\n" + "═" * 85)
    print(f"        SDR SIGNAL LOG — {total} readings")
    print("═" * 85)
    print(f"{'ID':<5} │ {'Freq (MHz)':<12} │ {'RSSI':<7} │ {'Det':<5} │ {'Status':<20} │ Time")
    print("─" * 85)

    prev_rssi = None
    for i in range(total):
        r          = contract.functions.getReading(i).call()
        freq_mhz   = r[1] / 1_000_000
        rssi       = r[2]
        detected   = r[3]
        timestamp  = datetime.fromtimestamp(r[4]).strftime("%Y-%m-%d %H:%M:%S")
        meta_bytes = r[5]

        det_icon = "✅" if detected else "❌"
        status   = get_status(rssi, detected, prev_rssi, meta_bytes)

        print(f"{i:<5} │ {freq_mhz:<12.2f} │ {rssi:<7} │ {det_icon:<5} │ {status:<20} │ {timestamp}")
        prev_rssi = rssi

    print("═" * 85 + "\n")

if __name__ == "__main__":
    view_logs()