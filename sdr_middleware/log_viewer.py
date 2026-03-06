import json
from web3 import Web3
from dotenv import load_dotenv
from datetime import datetime
import os

load_dotenv()

w3 = Web3(Web3.HTTPProvider(os.getenv("RPC_URL")))
with open("abi.json") as f:
    abi = json.load(f)

contract = w3.eth.contract(address=os.getenv("CONTRACT_ADDRESS"), abi=abi)

JAM_RSSI_FLOOR = -40

def is_jam(rssi, prev_rssi):
    if rssi > JAM_RSSI_FLOOR:
        return True
    if prev_rssi is not None and abs(rssi - prev_rssi) >= 20:
        return True
    return False

def view_logs():
    total = contract.functions.totalReadings().call()

    print("\n" + "═" * 75)
    print(f"        SDR SIGNAL LOG — {total} readings")
    print("═" * 75)
    print(f"{'ID':<5} │ {'Freq (MHz)':<12} │ {'RSSI':<7} │ {'Detected':<10} │ {'Status':<8} │ Time")
    print("─" * 75)

    prev_rssi = None
    for i in range(total):
        r        = contract.functions.getReading(i).call()
        freq_mhz = r[1] / 1_000_000
        rssi     = r[2]
        detected = "✅" if r[3] else "❌"
        time     = datetime.fromtimestamp(r[4]).strftime("%Y-%m-%d %H:%M:%S")
        jam      = is_jam(rssi, prev_rssi)
        status   = "🚨 JAM" if jam else "✅ OK "

        print(f"{i:<5} │ {freq_mhz:<12.2f} │ {rssi:<7} │ {detected:<10} │ {status:<8} │ {time}")
        prev_rssi = rssi

    print("═" * 75 + "\n")

if __name__ == "__main__":
    view_logs()