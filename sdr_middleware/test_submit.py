#test_submit.py
from submit import submit_reading
from connect import contract

# Dummy SDR data — replace with real GNU Radio values later
submit_reading(
    freq_hz=433920000,
    rssi=-72,
    detected=True
)

# Verify it landed
count = contract.functions.totalReadings().call()
print(f"Total readings on chain: {count}")

# Pull it back
reading = contract.functions.getReading(0).call()
print(f"Reading 0: {reading}")