# 🛡️ Automated Cryptocurrency Wallet Attribution Engine
### Smart India Hackathon (SIH) 2026 — Day 1 Foundation

Automated Attribution of Unknown Cryptocurrency Wallets to Nearest Virtual Asset Service Providers (VASPs) through Blockchain Intelligence APIs.

---

## 📌 Project Overview

During cybercrime and financial fraud investigations involving cryptocurrencies, law enforcement agencies and forensic analysts often start with an **unknown Ethereum suspect wallet**. The ultimate objective of this project is to automate the attribution of these wallets to the nearest regulated **Virtual Asset Service Provider (VASP / Exchange)** for KYC subpoena execution.

### **Day 1 Objective (Completed)**
Day 1 establishes the **core blockchain investigation foundation**:
1. **Ethereum Address Validation**: Instant syntactic and checksum validation.
2. **Live Blockchain Data Ingestion**: Direct fetching of real on-chain balance, gas metrics, and raw transactions from Ethereum mainnet (via Blockscout REST API v2 and Ethereum JSON-RPC with Etherscan fallback).
3. **Transaction Normalization**: Converting disparate blockchain payloads into a unified, chain-agnostic canonical model.
4. **1-Hop Connected Wallet Discovery**: Identifying unique sender (inflow) and recipient (outflow) counterparties, computing transaction counts and total ETH volume.
5. **Interactive 1-Hop Relationship Graph**: Visualizing suspect-counterparty topology with React Flow, featuring radial layout, interactive inspection, direction-based filtering, and animated transaction flows.
6. **Cybersecurity Investigation Dashboard**: Dark-mode, high-density investigation UI with wallet overview KPI cards, paginated transaction ledger, and counterparty breakdown.

---

## 🏗️ Architecture & Component Design

```
SIH_2026/
├── backend/
│   ├── api/
│   │   └── routes.py              # FastAPI endpoints (/api/wallet/analyze, /api/health)
│   ├── config/
│   │   └── settings.py            # Pydantic BaseSettings for timeouts, RPCs, API keys
│   ├── models/                    # Data models & persistence layer
│   ├── schemas/
│   │   └── wallet.py              # Pydantic schemas: NormalizedTransaction, ConnectedWallet, GraphData
│   ├── services/
│   │   ├── blockchain_service.py  # Isolated provider (Blockscout v2 + Etherscan + Public JSON-RPC)
│   │   ├── transaction_normalizer.py # Standardizes raw provider responses into canonical model
│   │   ├── wallet_service.py      # Computes balances, transaction flow stats, peer discovery
│   │   └── graph_service.py       # Constructs 1-hop radial graph with aggregated weighted edges
│   ├── utils/
│   │   └── validators.py          # Strict Ethereum regex and checksum validators
│   ├── main.py                    # FastAPI application entrypoint with CORS & logging
│   ├── requirements.txt           # Python backend dependencies
│   └── .env.example
├── frontend/
│   ├── app/
│   │   ├── globals.css            # Dark cyber theme, React Flow styles, custom animations
│   │   ├── layout.tsx             # Root layout with metadata
│   │   └── page.tsx               # Main investigation workspace
│   ├── components/
│   │   ├── Navbar.tsx             # Header with network status & SIH branding
│   │   ├── WalletSearch.tsx       # Address input, real-time validation, sample target picks
│   │   ├── WalletOverview.tsx     # KPI metrics: Balance, Tx count, In/Out breakdown, Peers
│   │   ├── GraphVisualization.tsx # Interactive 1-hop React Flow graph with custom nodes
│   │   ├── TransactionsTable.tsx  # Paginated transaction ledger with copy & Etherscan links
│   │   ├── ConnectedWalletsList.tsx # Counterparty cards with volume breakdown and pivot action
│   │   └── NodeDetailsModal.tsx   # Topology inspector drawer for graph nodes
│   ├── services/
│   │   └── api.ts                 # Typed API client for FastAPI backend
│   ├── types/
│   │   └── wallet.ts              # TypeScript interfaces matching backend models
│   ├── utils/
│   │   └── formatters.ts          # Address shortening, Wei-to-ETH conversion, date formatting
│   ├── package.json
│   ├── tailwind.config.js
│   └── tsconfig.json
├── .env.example
└── README.md
```

---

## ⚡ Tech Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | Next.js 14, React 18, TypeScript | High-performance reactive web application |
| **Styling** | Tailwind CSS | Custom cybersecurity dark-mode design system |
| **Graph Engine** | `@xyflow/react` (React Flow) | Hardware-accelerated 1-hop visual transaction topology |
| **Backend** | Python 3.11+, FastAPI, Uvicorn | Asynchronous, high-throughput REST API |
| **Data Validation** | Pydantic v2 | Strict schema validation and serialization |
| **Blockchain Client** | HTTPX (Async), Blockscout v2, JSON-RPC | Zero-auth real-time Ethereum mainnet querying |

---

## 🚀 Getting Started

### 1. Prerequisites
- **Node.js**: v18.0.0 or higher (v22+ recommended)
- **Python**: v3.10 or higher (v3.13 tested)

### 2. Clone and Setup Environment Variables

Copy the example environment files:
```bash
# Root / Backend config
cp backend/.env.example backend/.env
```

> **Note on API Keys:** The system is pre-configured to query **Blockscout REST API v2** and **Public Ethereum JSON-RPC** out of the box with zero API key required. If you wish to use Etherscan, simply add `ETHERSCAN_API_KEY=your_key` to `backend/.env`.

---

### 3. Start the Backend Server

```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Run FastAPI server
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8001
```
- Backend will be available at: `http://localhost:8001`
- Interactive Swagger API docs: `http://localhost:8001/docs`
- Health check: `http://localhost:8001/api/health`

---

### 4. Start the Frontend Application

```bash
# Open a new terminal and navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start Next.js development server
npm run dev
```
- Frontend application will be available at: `http://localhost:3000`

---

## 🔍 How Wallet Analysis Works

1. **Input & Validation**:
   - The user inputs a 42-character hexadecimal Ethereum address (`0x...`).
   - The frontend and backend validate the address using strict regex `^0x[a-fA-F0-9]{40}$`.
2. **Blockchain Querying**:
   - `blockchain_service.py` connects asynchronously to Ethereum mainnet to fetch the real ETH balance and raw transaction history.
3. **Transaction Normalization**:
   - `transaction_normalizer.py` converts raw transactions into a canonical schema: `txHash`, `fromAddress`, `toAddress`, `value` (in ETH), `valueWei`, `direction` (`incoming` / `outgoing` / `self`), `blockNumber`, `timestamp`, `gasUsed`, and `fee`.
4. **Counterparty Identification**:
   - `wallet_service.py` iterates through all transactions, isolates distinct connected addresses, calculates aggregate transaction counts, and computes total ETH volumes transferred in both directions.
5. **Topology Generation**:
   - `graph_service.py` places the target wallet at the center `(400, 300)` and places all 1-hop counterparties in a clean radial geometry. Multiple transactions between the same wallet pair are aggregated into unified directed edges with transaction count and volume labels.
6. **Dashboard Visualization**:
   - The frontend renders KPI summary cards, the interactive React Flow canvas, a paginated transaction ledger, and counterparty breakdown cards.

---

## 🎯 Verification & Sample Wallets

You can test the system using any valid Ethereum address or use the built-in quick test buttons:
- **Vitalik Buterin (`vitalik.eth`)**: `0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045`
- **Ethereum Foundation**: `0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe`
- **Binance Hot Wallet**: `0x28C6c06298d514Db089934071355E5743bf21d60`

---

## 📋 Current Day 1 Scope & Limitations

### ✅ What is Built Today:
- Real Ethereum mainnet data ingestion (balances, gas, fees, transactions).
- Canonical multi-chain transaction normalization.
- 1-hop counterparty detection with incoming/outgoing volume aggregations.
- Interactive 1-hop graph with custom nodes, edge badges, minimap, and node inspector.
- Robust error handling for invalid addresses, empty wallets, rate limits, and network errors.

### ⏳ Future Roadmap (Upcoming Days):
- **VASP & Exchange Attribution**: Clustering and matching deposit addresses to Binance, Coinbase, Kraken, OKX, WazirX, CoinDCX, etc.
- **Multi-Hop Recursive Tracing**: Graph expansion beyond 1-hop to trace illicit fund flows through intermediate hops.
- **Multi-Chain Expansion**: Bitcoin (UTXO model), Polygon, Arbitrum, BSC, and Solana.
- **Risk Scoring & Mixer Detection**: Identifying interactions with Tornado Cash, bridges, and high-risk entities.
- **AI-Powered Forensic Summary**: Automated natural language case report generation for LEAs.
- **Law Enforcement & SAHYOG Integration**: Generating standardized 91 CrPC notice templates for legal compliance.
