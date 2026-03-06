1. Project Context — What This Research Is Actually About
Right now it just says "SDR + Blockchain Signal Logging" but add a paragraph explaining:

This is an AAMU research project
What VICEROY is
What the goal of the research is (detecting and logging jamming events)
Who is involved (CS students, EE students)


2. Team Roles
## Team
- CS Student 1 — Smart Contract (Solidity, Remix)
- CS Student 2 — Middleware & Integration (Python, web3.py)
- EE Students  — GNU Radio flowgraph + SDR hardware

3. Hardware Requirements
The EE students' setup needs to be documented:
## Hardware Required
- RTL-SDR or compatible USB SDR dongle
- Antenna tuned to target frequency
- Host machine running GNU Radio

4. Current Status / Roadmap
Useful for your research documentation:
## Current Status
- [x] Smart contract deployed and tested
- [x] Middleware pipeline working with simulated data
- [x] Jam detection implemented
- [ ] GNU Radio integration (in progress)
- [ ] Sepolia testnet deployment
- [ ] Final ROC plot and data export

5. Known Limitations
Good for academic honesty in research:
## Known Limitations
- Hardhat resets on every restart — contract must be redeployed each session
- Jam detection thresholds are estimates until real SDR data is available
- Currently runs on local testnet only, not a live network
- .env must be created manually on each machine

6. Contract Details Section
## Contract Details
- Network: Hardhat Local (development)
- Solidity Version: 0.8.20
- Frequency validation: 1 Hz to 300 GHz
- RSSI validation: -150 to 0 dBm

7. How to Export Data for Research
Since this is for a paper, document how to get data out:
## Exporting Data for Research
Run the log viewer and pipe output to a file:
    python log_viewer.py > results.txt

To get raw data back from the contract for CSV export,
use getReading() for each ID from 0 to totalReadings().
