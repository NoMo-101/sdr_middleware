import json
from web3 import Web3
from dotenv import load_dotenv
import os

load_dotenv()

# Connect to Hardhat local blockchain
w3 = Web3(Web3.HTTPProvider(os.getenv("RPC_URL")))

# Confirm connection
if w3.is_connected():
    print("✅ Connected to blockchain")
else:
    print("❌ Connection failed — is Hardhat node running?")

# Load ABI
with open("abi.json") as f:
    abi = json.load(f)

# Load contract
contract = w3.eth.contract(
    address=os.getenv("CONTRACT_ADDRESS"),
    abi=abi
)

# Load wallet
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
WALLET = w3.eth.account.from_key(PRIVATE_KEY).address
print(f"Wallet: {WALLET}")