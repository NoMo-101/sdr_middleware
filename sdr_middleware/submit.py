#submit.py
from connect import w3, contract, WALLET, PRIVATE_KEY

def submit_reading(freq_hz, rssi, detected, meta_hash=None):
    if meta_hash is None:
        meta_hash = bytes(32)

    tx = contract.functions.submitReading(
        freq_hz,
        rssi,
        detected,
        meta_hash
    ).build_transaction({
        "from": WALLET,
        "nonce": w3.eth.get_transaction_count(WALLET),
        "gas": 200000,
    })

    signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f"✅ Transaction sent: {tx_hash.hex()}")

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"✅ Confirmed in block: {receipt.blockNumber}")
    return tx_hash