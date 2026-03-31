# pipeline.py
import json
import hashlib
import numpy as np
import pandas as pd
from dotenv import load_dotenv
import os

from connect import w3, contract, WALLET
from submit import submit_reading

load_dotenv()

# ── Settings ─────────────────────────────────────────
CSV_FILE = "pluto_capture_auto_100-w-time.csv"
JAM_RSSI_SPIKE      = 5
JAM_RSSI_FLOOR      = -10
PU_RSSI_THRESHOLD   = -12
CENTER_FREQ_HZ      = int(os.getenv("CENTER_FREQ_HZ", 915_000_000))
SIGNAL_THRESHOLD_DB = -16.0

# ── IQ → Power ───────────────────────────────────────
def process_iq_file(filepath):
    df = pd.read_csv(filepath)
    df["power_db"] = 20 * np.log10(
        np.maximum(np.sqrt(df["I"]**2 + df["Q"]**2), 1e-10)
    )
    df["detected"] = df["power_db"] > SIGNAL_THRESHOLD_DB
    return df[["Time (s)", "power_db", "detected"]].to_dict("records")

# ── Detection ────────────────────────────────────────
def detect_jam(rssi, prev_rssi):
    if rssi > JAM_RSSI_FLOOR:
        print(f"⚠️  Jam suspected: RSSI {rssi:.2f}dBm above floor")
        return True
    if prev_rssi is not None and abs(rssi - prev_rssi) >= JAM_RSSI_SPIKE:
        print(f"⚠️  Jam suspected: RSSI spiked ({prev_rssi:.2f} → {rssi:.2f})")
        return True
    return False

def detect_pu(rssi, detected):
    if detected and rssi > PU_RSSI_THRESHOLD:
        print(f"📡 Primary User detected: RSSI {rssi:.2f}dBm")
        return True
    return False

def make_meta_hash(jam: bool, pu: bool) -> bytes:
    meta = json.dumps({"jam": jam, "pu": pu}).encode()
    return hashlib.sha256(meta).digest()

# ── Main ─────────────────────────────────────────────
def run():
    prev_rssi = None

    print(f"📡 Contract: {os.getenv('CONTRACT_ADDRESS')}")
    print(f"👛 Wallet:   {WALLET}")
    print(f"📻 Center Freq: {CENTER_FREQ_HZ} Hz\n")

    try:
        samples = process_iq_file(CSV_FILE)
        print(f"🔁 Processing {len(samples)} samples from {CSV_FILE}...\n")

        for sample in samples:
            rssi     = sample["power_db"]
            detected = sample["detected"]
            jam      = detect_jam(rssi, prev_rssi)
            pu       = detect_pu(rssi, detected)
            meta     = make_meta_hash(jam, pu)

            status = "🚨 JAM" if jam else ("📡 PU" if pu else "✅ OK")
            print(f"{status} | {CENTER_FREQ_HZ}Hz | {rssi:.2f}dBm | detected={detected}")

            submit_reading(CENTER_FREQ_HZ, int(rssi), detected, meta)
            prev_rssi = rssi

        print(f"\n✅ Done. {len(samples)} readings submitted to chain.")

    except FileNotFoundError:
        print(f"❌ File not found: {CSV_FILE}")

if __name__ == "__main__":
    run()