# 🛡️ Project TraceACT — Forensic Blockchain Intelligence & VASP Attribution Engine
### Smart India Hackathon (SIH) 2026
**Target Ecosystem:** Indian Cyber Crime Coordination Centre (I4C), State Police Cyber Crime Cells, and the SAHYOG Ecosystem  
**Classification:** Law Enforcement Forensic Intelligence Platform  
**Platform Version:** 2.0.0 (Production Grade)

Automated Attribution of Unknown Cryptocurrency Wallets to Nearest Virtual Asset Service Providers (VASPs) through Multi-Hop Blockchain Intelligence, NetworkX Graph Analytics, and Statutory Notice Generation.

---

## 📌 Project Overview

During cybercrime and financial fraud investigations involving cryptocurrencies, law enforcement agencies and forensic analysts often start with an **unknown cryptocurrency suspect wallet**. The ultimate objective of **Project TraceACT** is to automate the attribution of these wallets to the nearest regulated **Virtual Asset Service Provider (VASP / Exchange)** for immediate asset freezing and KYC subpoena execution under Indian Law (Section 91 & 102 CrPC / Section 94 & 106 BNSS).

TraceACT automates the entire investigation pipeline in **under 3 seconds**:
1. **Multi-Chain Recognition:** Auto-detects and validates Ethereum (EVM), Bitcoin (Bech32/SegWit/P2PKH), Tron (TRC-20), and Solana addresses.
2. **Multi-Hop BFS Fund Traversal:** Level-by-level concurrent Breadth-First Search tracing funds 1 to 5 hops outward with cycle/loop prevention.
3. **Deterministic VASP Attribution:** Direct on-chain matching against 25 verified Indian (FIU-IND registered) and global exchanges with hop and branching penalties.
4. **NetworkX Graph Analytics:** Computes betweenness centrality, PageRank, wash-trading cycle detection, and identifies critical money-mule bottlenecks (`CRITICAL_BOTTLENECK_MULE`).
5. **16-Priority Forensic Rule Engine:** Calculates a continuous 0–100 Suspicion Score with customizable investigator system logic profiles (`balanced`, `strict`, `fraud_syndicate`, `relaxed`, `custom`).
6. **Unknown VASP Behavioral Discovery:** Extracts 28+ behavioral features to detect unlabelled commercial hubs and assigns `UC-YYYY-XXXX` cluster tags.
7. **Proportional Taint Accounting & Conservation Check:** Mathematically tracks fund flows and flags balance inflation/contamination anomalies.
8. **Minimum Intervention Set (MIS):** Solves set-cover optimization to find the minimum set of VASPs needed to freeze $\ge 70\%$ of stolen proceeds.
9. **Deterministic Step-Wise SOP Playbook (Zero LLM):** Generates a 7-step chronological action plan for investigators with statutory citations and deadlines.
10. **Statutory Notice & Section 65B BSA Certificate Generator:** Formats ready-to-serve Section 91 CrPC notices for the SAHYOG portal with SHA-256 evidence integrity hashes.
11. **24/7 Automated Background Sentry:** 60-minute periodic ledger balance tracking with automated SMTP alerts (`alerts@sahyog-lea.gov.in`).

---

## ⚡ Tech Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend UI** | React 18, Vite 6, Vanilla CSS (CSS Variables) | Apple Dark Cyberpunk high-density forensic workstation |
| **Graph Visualization** | `@xyflow/react` (React Flow 12.4.4) | Hardware-accelerated interactive node-edge topology canvas with minimap |
| **Backend Framework** | Python 3.11+, FastAPI, Uvicorn | Asynchronous, high-throughput REST API |
| **Graph Analytics Engine**| NetworkX (v3.0+) | Betweenness centrality, bottleneck mule identification, wash-trading cycle detection |
| **Data Validation** | Pydantic v2 & Pydantic-Settings | Strict schema validation, serialization, and runtime configuration |
| **Database & Persistence**| MongoDB (Motor/PyMongo) + `EmbeddedAsyncCollection` | High-availability database with automatic JSON-backed disk fallback (`db_store.json`) |
| **Blockchain Client** | HTTPX (Async), Blockscout v2, Blockstream, TronGrid, Solana RPC | Multi-chain real-time on-chain ledger querying with sandbox fallbacks |
| **Local AI / Report** | Ollama (`llama3.2:3b`) + Python Deterministic Generator | Generates 16-section investigative dossiers and Section 91 CrPC legal notices |

---

## 🚀 Quick Launch (Windows)

Simply double-click `start.cmd` in the root directory:
```cmd
start.cmd
```
This automated launcher checks your environment, starts the FastAPI backend on port `8001`, starts the Vite frontend on port `3000`, and opens your browser automatically.

### Manual Startup

#### Backend Setup
```bash
# Activate virtual environment
.\venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Run FastAPI backend
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload
```
- Interactive Swagger API Documentation: `http://localhost:8001/docs`
- Health Check: `http://localhost:8001/api/health`

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
- Frontend Workstation: `http://localhost:3000`

---

## 🎯 Verification & Demo Scenario

To test the full investigation pipeline with 1 click, click the **"🎯 SIH 2026 Reference Demo Scenario"** preset in the search bar or run:
```bash
curl -X POST http://localhost:8001/api/investigations/demo
```
**Case Profile (`CASE-2026-SIH-DEMO-001`):**
- **Suspect Target:** `0x71C836489B990038848971201991802901238910` (10.0 ETH cyber theft).
- **Branch 1 (5.2 ETH / 52%):** Direct deposit into **CoinDCX** (FIU-IND Registered). Actionability: **92/100 (CRITICAL)**.
- **Branch 2 (2.1 ETH / 21%):** Forwarded through intermediate mule `0x3344b...` into **Binance Global**. Actionability: **78/100 (HIGH)**.
- **Branch 3 (1.4 ETH / 14%):** Forwarded into **Unknown Cluster UC-2026-0042** (27 addresses, 611 depositors).
- **Minimum Intervention Set (MIS):** Recommends serving notices to **CoinDCX** and **Binance** to achieve **73.0% asset coverage** with just 2 targeted notices.

---

## 📚 Essential Project Documentation

- **[DOCUMENTATION.md](DOCUMENTATION.md):** Complete 800-line master technical documentation covering system architecture, mathematical formulas, algorithms, data contracts, and legal frameworks.
- **[question.md](question.md):** Hackathon evaluation master guide with 37 curated Q&As covering theory, technical implementation, legal admissibility (CrPC/BNSS/BSA), and curveball judge questions.

---

## 🧪 Automated Testing

Run the complete backend test suite (41 tests covering multi-hop tracing, VASP attribution, NetworkX analytics, and deterministic playbooks):
```bash
pytest backend/tests -v
```

---

## 📜 Legal Notice & Compliance
*Project TraceACT is engineered for the Smart India Hackathon (SIH) 2026. All investigative methodologies, rule engine heuristics, and legal notice generators are designed to assist authorized Law Enforcement Officers and Judicial Authorities in the prevention, detection, and investigation of cybercrime under applicable statutory frameworks.*
