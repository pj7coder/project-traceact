# 🚀 Quick Start Guide

## 📋 Prerequisites
- **Python**: 3.10+
- **Node.js**: 18+

## ⚡ 1-Click Launch (Recommended)

Double-click `start.cmd` or run in CMD / PowerShell:
```cmd
start.cmd
```
This automatically:
1. Activates Python `venv` and runs the FastAPI backend on port `8001`.
2. Launches Next.js frontend on port `3000`.
3. Opens the default browser at `http://localhost:3000`.

---

## 🖥️ Manual Startup (Terminal 1)

From the project root directory:

```powershell
# Optional: Setup virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r backend/requirements.txt

# Run FastAPI server
python -m uvicorn backend.main:app --reload --port 8001
```

- **API URL**: [http://localhost:8001](http://localhost:8001)
- **API Docs (Swagger)**: [http://localhost:8001/docs](http://localhost:8001/docs)
- **Health Check**: [http://localhost:8001/api/health](http://localhost:8001/api/health)

---

## 🌐 2. Start Frontend (Terminal 2)

In a new terminal:

```powershell
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start Next.js dev server
npm run dev
```

- **Dashboard UI**: [http://localhost:3000](http://localhost:3000)

---

## 🎯 3. Sample Wallets for Testing (All 3 Currencies)

### 🔷 Ethereum (ETH)
- **Vitalik Buterin**: `0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045`
- **Binance Hot Wallet**: `0x28C6c06298d514Db089934071355E5743bf21d60`
- **Ethereum Foundation**: `0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe`

### 🔶 Bitcoin (BTC)
- **Binance BTC Hot Wallet**: `1NDyJtNTjmwk5xPNhjgAMu4HDHigtobu1s`
- **Native SegWit (Bech32)**: `bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq`
- **Satoshi Genesis Target**: `1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa`

### 🔴 TRON (TRX / USDT-TRC20)
- **Tether USDT TRC-20 Router**: `TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t`
- **WazirX Tron Deposit Gateway**: `TNUC9Qb1rRpS5CbWLmNmxK1Ubinance11`
- **Active Tron Counterparty**: `TYDzsYUEpvnYmQk4zGP9sWWcTEd2MiAtW6`
