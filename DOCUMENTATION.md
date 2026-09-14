# 🛡️ Project TraceACT — Comprehensive System Documentation & Technical Blueprint
### Smart India Hackathon (SIH) 2026 — Forensic Blockchain Intelligence & VASP Attribution Engine
**Designed for:** Indian Cyber Crime Coordination Centre (I4C), Law Enforcement Agencies (LEAs), and the SAHYOG Ecosystem  
**Classification:** Law Enforcement Forensic Intelligence Platform  
**Version:** 2.0.0 (Production / Demonstration Grade)

---

## 📑 Table of Contents

1. [Executive Summary & Vision](#1-executive-summary--vision)
2. [Problem Statement & The Attribution Challenge](#2-problem-statement--the-attribution-challenge)
3. [Core Concept & Architectural Philosophy](#3-core-concept--architectural-philosophy)
4. [Complete Technology Stack](#4-complete-technology-stack)
5. [End-to-End System Architecture & Data Flow](#5-end-to-end-system-architecture--data-flow)
6. [Repository Structure & Codebase Organization](#6-repository-structure--codebase-organization)
7. [Core Engines & Algorithmic Design](#7-core-engines--algorithmic-design)
   - 7.1 Multi-Chain Auto-Detection & Resilient Data Ingestion
   - 7.2 Multi-Hop BFS Graph Traversal & Path Reconstruction
   - 7.3 Deterministic VASP Attribution Engine
   - 7.4 16-Priority Law Enforcement Rule Engine & Dynamic System Logic
   - 7.5 Unknown VASP Discovery & Service Clustering (`UC-YYYY-XXXX`)
   - 7.6 Investigation Intelligence Decision Pipeline & Taint Accounting
   - 7.7 Law Enforcement Reporting & Section 91 CrPC Notice Generator
   - 7.8 24/7 Automated Background Tracking & Alerting Suite
   - 7.9 NetworkX Graph Analytics & Centrality Engine
   - 7.10 Deterministic Step-Wise Investigation SOP Playbook
8. [Verified VASP Directory & Intelligence Knowledge Base](#8-verified-vasp-directory--intelligence-knowledge-base)
9. [Database Persistence & Zero-Config High Availability Architecture](#9-database-persistence--zero-config-high-availability-architecture)
10. [REST API Reference & Data Contracts](#10-rest-api-reference--data-contracts)
11. [User Interface & Investigation Workstation Walkthrough](#11-user-interface--investigation-workstation-walkthrough)
12. [Legal, Regulatory & Evidentiary Admissibility Framework](#12-legal-regulatory--evidentiary-admissibility-framework)
13. [Installation, Setup & Deployment Guide](#13-installation-setup--deployment-guide)
14. [Testing, Verification & Reference Demo Scenarios](#14-testing-verification--reference-demo-scenarios)
15. [Future Roadmap & Extensibility](#15-future-roadmap--extensibility)

---

## 1. Executive Summary & Vision

Cryptocurrency theft, ransomware extortion, phishing drainers, illegal betting syndicates, and online financial fraud schemes present a critical bottleneck to modern criminal investigations: **pseudo-anonymity**. Criminal actors exploit unhosted, private self-custodial wallets to obscure money trails, hopping across intermediate wallets, peeling chains, and decentralized protocols.

However, illicit crypto proceeds cannot be utilized in the real economy without **cash-out / off-ramping** into fiat currency. This requires routing through **Virtual Asset Service Providers (VASPs)** — centralized cryptocurrency exchanges, custodial brokers, and payment gateways. Regulated VASPs collect mandatory **Know Your Customer (KYC)** records, including government-issued identity documents (Aadhaar, PAN, Passports), verified bank accounts, IP connection logs, and mobile phone numbers.

**Project TraceACT** is an automated, enterprise-grade blockchain forensic intelligence platform engineered specifically for **Law Enforcement Agencies (LEAs)**, the **Indian Cyber Crime Coordination Centre (I4C)**, State Police Cyber Crime Cells, and the **SAHYOG platform**. 

TraceACT bridges the gap between raw, pseudo-anonymous blockchain ledgers and actionable real-world legal requisitions. Starting with an unknown suspect wallet, TraceACT automatically executes multi-hop fund-flow tracing, eliminates peeling and layering obfuscation, attributes the fund endpoints to verified regulated VASPs or identifies unknown custodial clusters, calculates mathematical taint accounting, and outputs court-admissible **Section 91 CrPC (or Section 94 BNSS)** statutory notice requisitions for immediate account freezing.

---

## 2. Problem Statement & The Attribution Challenge

### The Forensic Problem
When an investigator receives a cybercrime complaint (e.g., from the National Cyber Crime Reporting Portal - NCRP):
1. **The Starting Point is Opaque:** The complainant provides only a transaction hash or an unknown destination wallet address (e.g., `0x71C836...`).
2. **Layering & Hopping Obfuscation:** Illicit actors immediately peel, split, and jump funds across 2 to 5 intermediate wallets to defeat naive 1-hop lookups.
3. **Manual Analysis Latency:** Manually cross-referencing block explorers (Etherscan, Blockchain.com, TronScan) takes days, allowing suspects time to cash out.
4. **Attribution Ambiguity:** A raw wallet address does not indicate which exchange it belongs to or whether it is an omnibus hot wallet, a deposit contract, or an unhosted personal wallet.
5. **Legal Requisition Overload:** Investigators are faced with multiple endpoints and do not know which exchange holds the majority of the stolen assets, leading to shotgun subpoena requests.

### TraceACT's Core Mission
Automate the end-to-end attribution lifecycle in **under 3 seconds**:
```
[Unknown Suspect Wallet] 
       │
       ▼ (Multi-Chain Auto Detection)
[Live On-Chain Multi-Hop BFS Traversal]
       │
       ▼ (Rule Engine + Unknown VASP Heuristics)
[Taint Accounting & Minimum Intervention Set]
       │
       ▼ (Court-Admissible Evidence Dossier)
[Section 91 CrPC Notice to Nodal Officer for Immediate Account Freeze]
```

---

## 3. Core Concept & Architectural Philosophy

TraceACT is built on seven core foundational principles:

1. **Deterministic Attribution First:** Attribution to verified VASPs is strictly rule-based, deterministic, and verifiable against verified on-chain manifests and regulatory registries (FIU-IND, Etherscan verified labels, exchange deposit routers). AI/LLMs are never used to guess cryptographic wallet ownership.
2. **Mathematical Taint Accounting & Fund Conservation:** Tracks funds using Proportional Taint Accounting. Incorporates a hard Conservation Check that flags any balance inflation or external co-mingling exceeding ±5%.
3. **Minimum Intervention Set (MIS):** Solves the Law Enforcement Subpoena Problem by computing the minimal set of VASPs that must be served legal notices to capture at least 70% to 90% of stolen proceeds.
4. **Adversarial Attribution Challenging:** Automatically formulates counter-hypotheses (e.g., CoinJoin mixing, cross-chain bridge, merchant payment, dusting attack) to stress-test attribution confidence before a police officer signs an official requisition.
5. **Unknown VASP Behavioral Discovery:** Identifies unlabelled commercial entities (unregistered brokers, syndicate sweepers, OTC desks) using 28+ behavioral indicators without falsely claiming verified identity.
6. **Zero-Configuration Resilient Architecture:** Operates seamlessly whether MongoDB or external explorer APIs are live or down, utilizing an asynchronous JSON-backed in-memory database fallback (`EmbeddedAsyncCollection`) and local mock sandbox fallbacks.
7. **Admissibility in Courts of Law:** All data outputs are formatted for Section 65B of the Indian Evidence Act, 1872 / Bharatiya Sakshya Adhiniyam, 2023, accompanied by cryptographic SHA-256 evidence integrity hashes.

---

## 4. Complete Technology Stack

### 4.1 Frontend Layer
| Component | Technology | Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Framework** | React.js | `18.3.1` | Declarative, component-driven UI architecture |
| **Build Tool** | Vite | `6.2.0` | Ultra-fast HMR and optimized production bundling |
| **Graph Visualization Engine** | `@xyflow/react` (React Flow) | `12.4.4` | Hardware-accelerated interactive node-edge topology canvas with custom SVG badges and minimap |
| **Iconography** | Lucide React | `1.16.0` | Clean, modern vector icons for forensic indicators |
| **Styling & Theme** | Vanilla CSS (CSS Variables) | Native | Apple Dark Cyberpunk theme, glassmorphism, responsive high-density layouts |
| **API Client** | Native Fetch / Async JavaScript | ES2022 | Typed API client interfacing with FastAPI endpoints |

### 4.2 Backend Layer
| Component | Technology | Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Web Framework** | FastAPI | `>=0.110.0` | High-throughput asynchronous ASGI web framework with OpenAPI / Swagger |
| **ASGI Server** | Uvicorn (Standard) | `>=0.28.0` | High-performance asynchronous HTTP server |
| **HTTP Engine** | HTTPX (Async) | `>=0.27.0` | Asynchronous non-blocking HTTP requests for multi-chain explorers and RPCs |
| **Data Validation** | Pydantic v2 & Pydantic-Settings | `>=2.6.0` | Strict data typing, schema enforcement, and environment variable configuration |
| **Environment Config** | Python-Dotenv | `>=1.0.1` | Dynamic runtime `.env` loading |
| **Language Runtime** | Python | `3.11+` | Core execution environment |
| **Graph Analytics Engine** | NetworkX | `>=3.0` | Topological betweenness centrality, money-mule bottlenecks, cycle detection, and confidence calibration |

### 4.3 Database & Storage Layer
| Component | Technology | Implementation | Purpose |
| :--- | :--- | :--- | :--- |
| **Primary Database** | MongoDB | Motor `>=3.3.0` & PyMongo `>=4.6.0` | High-performance document storage for wallet records, graphs, cases, and notices |
| **Embedded Fallback** | `EmbeddedAsyncCollection` | Custom Python class (`mongo.py`) | In-memory, disk-persisted (`data/db_store.json`) async collection ensuring 100% uptime when MongoDB is absent |
| **VASP Directory** | Static JSON Directory | `data/vasp_directory.json` | 25 verified Indian & Global VASP profiles with FIU-IND registrations, KYC status, and nodal contacts |
| **Entity Directory** | Static JSON Directory | `data/known_entities.json` | Curated database of tagged exchanges, mixers, ransomware, and OFAC-sanctioned wallets |

### 4.4 Multi-Chain Blockchain Adapters
| Chain | Protocol Type | Primary Data Source | Fallback Data Source |
| :--- | :--- | :--- | :--- |
| **Ethereum / EVM** | Account-based | Blockscout REST API v2 | Public Ethereum JSON-RPC & Etherscan API |
| **Bitcoin** | UTXO-based | Blockstream REST API | Blockchain.info API & Local Mock Sandbox |
| **Tron (TRC-20)** | Account-based | TronGrid REST API | TronScan REST API & Local Mock Sandbox |
| **Solana** | Account-based | Solana Mainnet-Beta JSON-RPC | Public Solana RPC & Local Mock Sandbox |

### 4.5 Artificial Intelligence & Local LLM Layer
| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Local LLM Host** | Ollama | `http://127.0.0.1:11434` (Local, zero cloud leakage, privacy-preserving) |
| **Model** | `llama3.2:3b` / `mistral` | Generates executive summaries, crime typology narratives, and Section 91 CrPC legal notices |
| **Template Fallback** | Pure Python Determinate Generator | Generates official statutory reports when Ollama is offline |

### 4.6 Communications & Automation Layer
| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Background Scheduler** | Python `asyncio` Task Loop | Runs 60-minute automated periodic ledger balance and transaction diffing |
| **Notification Engine** | Python `smtplib` & Email MIME | Automated SMTP email alerts to nodal officers and cyber cell desks (`alerts@sahyog-lea.gov.in`) |

---

## 5. End-to-End System Architecture & Data Flow

```
                                  USER BROWSER (INVESTIGATOR)
                                                │
                          ┌─────────────────────┴─────────────────────┐
                          ▼                                           ▼
               [Interactive React Flow Canvas]              [Forensic Report & CrPC View]
                          │                                           ▲
                          │ HTTP REST                                 │
                          ▼                                           │
             ┌────────────────────────────────────────────────────────┴────────┐
             │                   FASTAPI APPLICATION BACKEND                   │
             │                         (Port 8001)                             │
             └──────┬──────────────┬──────────────┬──────────────┬─────────────┘
                    │              │              │              │
                    ▼              ▼              ▼              ▼
           [Multi-Chain Svc] [Tracing Svc] [Attribution] [Rule Engine]
             │   │   │   │         │              │              │
   ┌─────────┘   │   │   └─────┐   │ (BFS Tree)   │ (Nearest)    │ (16 Rules)
   ▼             ▼   ▼         ▼   ▼              ▼              ▼
[Ethereum]    [BTC] [Tron]   [Solana]      [Investigation Engine]
   │             │   │         │                  │
   └─────────────┴───┴─────────┘                  ├─► Taint Accounting (Part K)
                 │                                ├─► Conservation Check (Part L)
                 ▼                                ├─► Minimum Intervention Set (MIS)
      [Normalized Transaction]                    ├─► Attribution Challenges
                 │                                └─► Unknown VASP Clustering
                 ▼                                               │
       [Database Layer (mongo.py)]                               ▼
       ├─ Motor / PyMongo (Local/Cloud Mongo)          [Report Service (LLM)]
       └─ EmbeddedAsyncCollection (db_store.json)      ├─ Ollama Local llama3.2:3b
                                                       └─ Statutory Sec 91 CrPC
```

### Data Pipeline Sequence
1. **Input:** The investigator enters a suspect cryptocurrency address into the UI.
2. **Auto-Detection:** `multi_chain_service.detect_chain` recognizes the encoding (EVM `0x`, Bitcoin `bc1`/`1`/`3`, Tron `T`, Solana Base58) and triggers validation.
3. **Ingestion & Normalization:** The respective chain adapter queries live endpoints or falls back gracefully to sandbox data, standardizing transactions into `NormalizedTransaction`.
4. **BFS Multi-Hop Tracing:** `tracing_service` traverses outward (1 to 5 hops), evaluating transactions concurrently per layer, eliminating cycles, and aggregating edges.
5. **VASP Attribution:** `attribution_service` matches nodes against the 25 verified VASPs in `vasp_directory.json` and `known_entities.json`. It applies hop and branch penalties to determine the nearest verified VASP.
6. **Heuristics & Rule Engine:** `rule_engine` checks the wallet against 16 prioritized rules (sanctions, ransomware, peel chains, high velocity), applying investigator-tuned sensitivity profiles (`balanced`, `strict`, `fraud_syndicate`, `relaxed`, `custom`).
7. **Decision Pipeline:** `investigation_engine` executes taint accounting, verifies value conservation, calculates VASP Actionability Scores, computes the Minimum Intervention Set (MIS), and tests alternative adversarial explanations.
8. **Unknown VASP Discovery:** `vasp_discovery_service` isolates unlabelled high-volume consolidation hubs and assigns `UC-YYYY-XXXX` cluster tags.
9. **Dossier & Legal Requisition:** `report_service` invokes Ollama (or local deterministic templates) to assemble a 16-section investigative dossier and ready-to-serve Section 91 CrPC notice.
10. **Persistence & Monitoring:** The investigation docket is saved in MongoDB / `db_store.json`, and if enabled, registered for 60-minute live tracking.

---

## 6. Repository Structure & Codebase Organization

```
SIH_2026/
├── backend/
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py                  # All REST endpoints (Analyze, Trace, Attribute, Investigate, Report, Settings)
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py                # Pydantic BaseSettings (APIs, RPCs, DB, Ollama, SMTP, LEA profile)
│   ├── database/
│   │   ├── __init__.py
│   │   └── mongo.py                   # High-availability Motor client + EmbeddedAsyncCollection disk fallback
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── wallet.py                  # Pydantic models for transactions, overviews, traces, nodes, edges
│   │   └── attribution.py             # Pydantic models for attribution, VASP candidates, dossiers, reports
│   ├── services/
│   │   ├── __init__.py
│   │   ├── blockchain_service.py      # Ethereum ingestion (Blockscout v2, Etherscan, Public JSON-RPC)
│   │   ├── transaction_normalizer.py  # Converts raw multi-source payloads into canonical schema
│   │   ├── wallet_service.py          # 1-hop counterparty aggregator and balance calculator
│   │   ├── graph_service.py           # Constructs 1-hop radial layout graphs
│   │   ├── multi_chain_service.py     # Multi-chain address auto-detector and BTC/Tron/Solana adapters
│   │   ├── tracing_service.py         # Multi-hop BFS graph traversal engine with cycle prevention
│   │   ├── entity_service.py          # Entity database and VASP directory lookup manager
│   │   ├── attribution_service.py     # Deterministic nearest VASP attribution calculator
│   │   ├── rule_engine.py             # 16-priority forensic rule engine and continuous scoring
│   │   ├── vasp_discovery_service.py  # Unknown VASP behavioral feature extractor and clustering
│   │   ├── investigation_engine.py    # Decision pipeline: Taint accounting, MIS, VASP actionability
│   │   ├── graph_expansion_service.py # Incremental on-demand node branch expansion
│   │   ├── report_service.py          # 16-section LEA forensic report & Section 91 CrPC notice generator
│   │   ├── live_tracking_service.py   # Periodic background tracker (60-min interval) and diff engine
│   │   ├── email_service.py           # Asynchronous SMTP alert dispatcher
│   │   └── history_service.py         # Search history, case indexing, and tag manager
│   ├── utils/
│   │   ├── __init__.py
│   │   └── validators.py              # Cryptographic address validators for EVM, BTC, Tron, Solana
│   ├── main.py                        # FastAPI entrypoint, lifespan manager, CORS, logging
│   ├── requirements.txt               # Backend Python dependencies
│   └── .env.example                   # Example environment configuration
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   └── client.js              # Typed API communication wrapper for all backend routes
│   │   ├── components/
│   │   │   ├── Sidebar.jsx            # Left navigation sidebar (Graph, Suspicion, Dossier, Report, Settings)
│   │   │   ├── SearchBar.jsx          # Address input, chain pills, hop sliders, sample wallet presets
│   │   │   ├── WalletOverviewCard.jsx # Target KPI summary: balance, asset, tx count, peers, risk badge
│   │   │   ├── GraphView.jsx          # React Flow canvas, zoom controls, mini-map, legend, branch expander
│   │   │   ├── RectangularNode.jsx    # Custom React Flow node card with address, VASP badge, risk color
│   │   │   ├── NodeDetailModal.jsx    # Inspector modal displaying node details, counterparties, and actions
│   │   │   ├── TransactionList.jsx    # Paginated tabular transaction ledger with explorer links
│   │   │   ├── SuspicionPointsView.jsx# 16 forensic rules view with profile selector and weight sliders
│   │   │   ├── InvestigationGuideView.jsx # Decision pipeline view: Taint, MIS, VASP ranking, Unknown clusters
│   │   │   ├── ForensicReportView.jsx # 16-section LEA report view, Section 91 CrPC notice, copy/print
│   │   │   └── SettingsModal.jsx      # Modal for configuring API keys, RPCs, Ollama, SMTP, and LEA profile
│   │   ├── App.jsx                    # Root React component managing forensic investigation state
│   │   ├── main.jsx                   # React DOM entrypoint
│   │   └── index.css                  # Apple Dark Cyberpunk stylesheet, CSS variables, glassmorphism
│   ├── package.json                   # Frontend dependencies (@xyflow/react, lucide-react, vite)
│   ├── vite.config.js                 # Vite bundler configuration
│   └── index.html                     # HTML5 shell
├── data/
│   ├── db_store.json                  # JSON-backed database persistence store (auto-created if no Mongo)
│   ├── known_entities.json            # Curated tagged entities (mixers, scams, exchanges, sanctions)
│   └── vasp_directory.json            # 25 verified Indian & Global VASP directory records
├── start.cmd                          # 1-Click Windows Production Launcher
├── package.json                       # Root script manager
└── README.md                          # Quickstart documentation
```

---

## 7. Core Engines & Algorithmic Design

### 7.1 Multi-Chain Auto-Detection & Resilient Data Ingestion
**Service:** `backend/services/multi_chain_service.py` & `backend/utils/validators.py`

#### Chain Detection Logic
The system automatically classifies addresses into their native chains using regular expression inspection and checksum analysis:
1. **Ethereum / EVM:** Matches `^0x[a-fA-F0-9]{40}$`. Validates EIP-55 mixed-case checksum. Also suggests alternative EVM chains (BNB Chain, Polygon, Arbitrum).
2. **Bitcoin:**
   - Native SegWit (Bech32) / Taproot (Bech32m): Matches `^(bc1[a-z0-9]{39,59}|bc1p[a-z0-9]{58})$`.
   - Legacy P2PKH: Matches `^1[a-km-zA-HJ-NP-Z1-9]{25,34}$` (Base58Check).
   - Script P2SH: Matches `^3[a-km-zA-HJ-NP-Z1-9]{25,34}$` (Base58Check).
3. **Tron:** Matches `^T[a-zA-HJ-NP-Z0-9]{33}$` (Base58Check TRC-20 account prefix).
4. **Solana:** Matches `^[1-9A-HJ-NP-Za-km-z]{32,44}$` (Ed25519 Base58 public key).

#### Resilient Ingestion
All chain queries implement fallback cascades:
- **Ethereum:** Blockscout API v2 (`https://eth.blockscout.com/api/v2`) ➔ Public JSON-RPC (`eth_getBalance`, `eth_getBlockByNumber`) ➔ Etherscan API.
- **Bitcoin:** Blockstream API (`https://blockstream.info/api/address/{addr}`) ➔ Local Sandbox Mock.
- **Tron:** TronGrid API ➔ TronScan API ➔ Local Sandbox Mock.
- **Solana:** Solana Mainnet-Beta RPC (`getBalance`, `getSignaturesForAddress`) ➔ Local Sandbox Mock.

---

### 7.2 Multi-Hop BFS Graph Traversal & Path Reconstruction
**Service:** `backend/services/tracing_service.py`

#### Traversal Algorithm
The `MultiHopTracingEngine` executes a level-by-level **Breadth-First Search (BFS)** traversal:
- **Concurrence:** Level $L_{k}$ queries all discovery counterparties in parallel using `asyncio.gather`, minimizing HTTP latency.
- **Cycle Prevention:** Maintains a globally tracked `visited_addresses` set and path-edge signature set to prevent loops caused by circular wash trading or syndicate loops.
- **Filters:** Filters out dust transactions below `minimumTransferValue` and ignores transactions outside `[startTimestamp, endTimestamp]`.
- **Node Capping:** Enforces `maxNodes` (default: 50, max: 100) to protect memory and browser rendering performance.

#### Deterministic Graph Layout
To ensure clear visual comprehension, coordinates are computed using a deterministic **Left-to-Right Hierarchy**:
$$X_{\text{coord}} = 100 + (\text{hopDepth} \times 320)$$
$$Y_{\text{coord}} = 100 + (i \times 160) - \left(\frac{(\text{nodesInLevel} - 1) \times 160}{2}\right)$$
This positions the root suspect at the far left ($X=100$), intermediate hops in the middle, and terminal VASP deposit endpoints at the right.

---

### 7.3 Deterministic VASP Attribution Engine
**Service:** `backend/services/attribution_service.py` & `backend/services/entity_service.py`

#### Attribution Formula
Given a terminal node $N$, its attribution confidence score $C(N)$ is calculated as:
$$C(N) = C_{\text{base}} - (P_{\text{hop}} \times d) - (P_{\text{branch}} \times b)$$

Where:
- $C_{\text{base}}$: Base confidence of the entity record ($95\%$ for verified FIU-IND registry, $85\%$ for public explorer labels, $65\%$ for heuristic tags).
- $d$: Hop distance from the root suspect wallet ($d \in [1, 5]$).
- $P_{\text{hop}}$: Hop distance penalty ($10\%$ per hop).
- $b$: Number of intermediate split branches ($5\%$ per branch).
- $P_{\text{branch}}$: Co-mingling branch penalty.

#### Endpoint Classification
The attribution engine distinguishes between:
1. **Direct Deposit Router:** Smart contract or unique account address generated by an exchange exclusively for a customer deposit (e.g., CoinDCX Deposit Contract). **Action:** Immediate Section 91 CrPC notice to identify the depositor's KYC.
2. **Exchange Omnibus Hot Wallet:** Public pooling wallet used to batch withdrawals (e.g., Binance Hot Wallet 14). Indicates funds have been consolidated into internal exchange accounting.

---

### 7.4 16-Priority Law Enforcement Rule Engine & Dynamic System Logic
**Service:** `backend/services/rule_engine.py`

The rule engine evaluates transactions against 16 prioritized forensic rules, outputting a composite **0–100 Suspicion Score**:

| Priority | Rule ID | Category | Severity | Default Weight | Key Detection Trigger |
| :---: | :--- | :--- | :--- | :---: | :--- |
| **P1** | `P1_SANCTIONED_ADDRESSES` | Sanctions | CRITICAL | $+100$ | Direct interaction with OFAC, UN, or EU sanctioned addresses |
| **P2** | `P2_RANSOMWARE_INTERACTION` | Extortion | CRITICAL | $+95$ | Linkage to known ransomware payout addresses (LockBit, BlackCat) |
| **P3** | `P3_RECEIVING_STOLEN_FUNDS_HACKS` | Theft | CRITICAL | $+92$ | Interaction with exploit drainers, stolen funds, or protocol hack pools |
| **P4** | `P4_SCAMS_MALICIOUS_CONTRACTS` | Fraud | CRITICAL | $+88$ | Interaction with phishing drainers, fraudulent tokens, or scam contracts |
| **P5** | `P5_ILLICIT_SERVICES_MIXERS` | Obfuscation | HIGH | $+83$ | Deposits/withdrawals via Tornado Cash, Blender, or CoinJoin pools |
| **P6** | `P6_RAPID_MOVEMENT_OF_FUNDS` | Laundering | HIGH | $+75$ | Funds received and $>50\%$ forwarded within minutes (pass-through / peel) |
| **P7** | `P7_MULTIPLE_WALLETS_AS_ONE_CLUSTER` | Syndicate | HIGH | $+70$ | Bi-directional loops and co-spending across peer wallets |
| **P8** | `P8_SUSPICIOUS_TRANSACTION_PATTERN` | Velocity | HIGH | $+65$ | Concentrated burst of $\ge 10$ automated transactions |
| **P9** | `P9_RECEIVING_SENDING_LARGE_AMOUNTS` | Exposure | MEDIUM | $+52$ | Individual transactions exceeding chain threshold (e.g., $>5.0$ ETH, $>0.5$ BTC) |
| **P10** | `P10_MAKING_LARGE_NUMBER_OF_TRANSACTIONS` | Activity | MEDIUM | $+45$ | Lifetime transaction count $\ge 100$ operations |
| **P11** | `P11_INDIRECT_EXPOSURE_SUSPICIOUS_WALLETS` | Downstream | MEDIUM | $+35$ | Indirect exposure to flagged mixers or hacks at Hop 2 or Hop 3 |
| **P12** | `P12_CREATING_A_NEW_WALLET` | Fresh Target | MEDIUM | $+34$ | Wallet age $<5$ transactions but transferring large volumes |
| **P13** | `P13_NO_VASP_ACCOUNT` | Unhosted | LOW-MED | $+25$ | Pure unhosted hopping with zero 1-hop regulated VASP links |
| **P14** | `P14_HOLDING_A_LOT_OF_ETH` | Custody | INFO | $+15$ | High on-chain liquid balance ($>15$ ETH, $>3$ BTC, $>20,000$ TRX) |
| **P15** | `P15_SENDING_ETH_DIRECTLY_TO_PERSON` | P2P | INFO | $+11$ | Unhosted direct peer-to-peer asset transfers outside smart contracts |
| **P16** | `P16_DAY_TO_DAY_PURPOSES` | Dampener | CLEAN | $-20$ | Verified interactions with regulated exchanges with zero illicit nexus |

#### Composite Scoring Formula
$$S_{\text{raw}} = \left( W_{\text{max}} \times 0.86 \right) + \sum_{i=1}^{k} \frac{W_i \times 0.16}{1.7 + 0.35i} + V_{\text{vol}} + D_{\text{damp}}$$
$$S_{\text{final}} = \min\left(99, \max\left(1, \text{round}\left(S_{\text{raw}} \times M_{\text{sensitivity}}\right)\right)\right)$$

Where $W_{\text{max}}$ is the highest triggered weight, $V_{\text{vol}}$ is volume scaling, $D_{\text{damp}}$ is the negative dampener from clean VASP activity, and $M_{\text{sensitivity}}$ is the investigator's tuning multiplier.

#### Investigator System Logic Profiles
- **Balanced (Standard LEA SOP):** $M_{\text{sensitivity}} = 1.0$, balanced thresholds.
- **Strict (Terror Financing / Ransomware):** $M_{\text{sensitivity}} = 1.25$, VASP dampener disabled, burst velocity lowered to 5 txs.
- **Fraud Syndicate (Peeling Chains & Mules):** Weight overrides: P6 ($+90$), P7 ($+75$), P13 ($+45$).
- **Relaxed (Commercial / OTC Trader):** $M_{\text{sensitivity}} = 0.75$ for high-net-worth commercial profiles.
- **Custom:** Investigator overrides weights, disables individual rules, or tunes thresholds via sliders.

---

### 7.5 Unknown VASP Discovery & Service Clustering (`UC-YYYY-XXXX`)
**Service:** `backend/services/vasp_discovery_service.py`

Criminal syndicates frequently use unlabelled commercial infrastructure: private OTC desks, illegal gambling collection hubs, or unlicensed instant swap platforms. TraceACT discovers these unknown entities without asserting unverified ownership.

#### 28+ Behavioral Feature Extraction
Extracts features across:
- **Aggregation:** `unique_senders`, `unique_receivers`, `sender_receiver_ratio`
- **Consolidation:** Many-to-one inflow vs outflow ratios
- **Velocity:** Transactions per hour/day, burst intervals
- **Retention:** Median hours funds sit before movement (`balance_retention_time_hours`)
- **Sweep Frequency:** Automated sweep percentage within 2 hours of receipt
- **Destination Concentration:** Percentage of funds flowing to top 3 repeated destination addresses

#### VASP Behavior Score (0–100)
A weighted composite score reflecting exchange-like custodial operation:
- **Score $\ge 75$:** Strong VASP-Like Behaviour (Probable Custodial Service)
- **Score $50–74$:** Moderate VASP-Like Behaviour
- **Score $25–49$:** Weak VASP-Like Behaviour
- **Score $< 25$:** Retail Personal Wallet

#### Cluster Identifier Assignment
When an unknown entity exhibits a score $\ge 75$ and controls multiple connected addresses, it is assigned an official case cluster tag:
$$\text{Cluster ID} = \text{UC-}YYYY\text{-}\text{XXXX} \quad (\text{e.g., UC-2026-0042})$$
All reports strictly append the mandatory statutory disclaimer:
> `HEURISTIC CLASSIFICATION — NOT VERIFIED ATTRIBUTION`

---

### 7.6 Investigation Intelligence Decision Pipeline & Taint Accounting
**Service:** `backend/services/investigation_engine.py`

#### 1. Proportional Taint Accounting
Tracks what fraction of the original stolen funds ($V_{\text{original}}$) reached which endpoints:
$$V_{\text{original}} = V_{\text{known\_vasp}} + V_{\text{unknown\_vasp}} + V_{\text{unresolved}} + V_{\text{fees}}$$

#### 2. Fund Conservation Check
Verifies accounting integrity. If the accounted funds exceed the original suspicious volume by $>5\%$, the system issues a formal anomaly flag:
> `CONSERVATION ANOMALY: Total accounted funds exceed initial case value by X%. Indicative of external un-tainted co-mingling or multi-source deposit pooling.`

#### 3. VASP Actionability Scoring
Ranks VASPs by how viable and urgent it is to serve a legal notice:
$$\text{Score}_{\text{action}} = (E_{\text{amount}} \times 0.35) + (R_{\text{regulatory}} \times 0.30) + (K_{\text{kyc}} \times 0.20) + (H_{\text{hop}} \times 0.15)$$
- Indian FIU-IND registered entities receive higher priority due to direct Section 91 CrPC compliance officers.

#### 4. Minimum Intervention Set (MIS)
Solves the set-cover optimization problem using a greedy algorithm to identify the smallest subset of VASPs required to cover $\ge 70\%$ of the stolen assets. This prevents investigators from wasting resources serving dozens of subpoenas.

#### 5. Attribution Challenge Engine (Adversarial Counter-Hypotheses)
To prevent wrongful asset freezing, the engine automatically challenges the attribution by testing:
- Could this be an automated CoinJoin mixing transaction?
- Could this be a cross-chain bridge router rather than an exchange?
- Could this be a dust transaction or promotional airdrop?
- Could this be a retail merchant payment?
If alternative hypotheses hold merit, the confidence level is downgraded, and human review is flagged.

---

### 7.7 Law Enforcement Reporting & Section 91 CrPC Notice Generator
**Service:** `backend/services/report_service.py`

#### 16-Section Investigation Dossier
The report service compiles a comprehensive dossier containing:
1. **Case Docket & Header:** Case ID, Investigator ID, Agency, Timestamp, SHA-256 Hash.
2. **Executive Summary:** Natural language overview of fund origins, hops, and terminal destinations.
3. **Suspect Entity Profile:** Analyzed address, balance, creation time, transaction count.
4. **Primary Attribution Findings:** Nearest verified VASP, hop distance, volume received.
5. **Multi-Hop Traversal Manifest:** Chronological, step-by-step transaction ledger.
6. **Proportional Taint Accounting Breakdown:** Known VASP, Unknown VASP, Unresolved, Fees.
7. **Conservation of Value Verification:** Integrity check and co-mingling analysis.
8. **VASP Actionability Ranking Table:** Prioritized list of target entities with contact details.
9. **Minimum Intervention Set (MIS) Recommendation:** Optimal subpoena action plan.
10. **Potential Service Clusters:** Deep dive into `UC-YYYY-XXXX` clusters.
11. **Attribution Challenge Analysis:** Counter-hypotheses and confidence adjustments.
12. **Identified Evidence Gaps & Blind Spots:** Missing data points and suggested remedies.
13. **Forensic Timeline of Events:** Chronological reconstruction of suspect fund movements.
14. **Strategic Investigative Next Actions:** Ranked next steps (PRESERVE_EVIDENCE, ISSUE_NOTICE).
15. **Statutory Requisition (Section 91 CrPC Notice):** Fully filled legal requisition.
16. **Legal Admissibility & Certificate under Section 65B BSA:** Cryptographic certificate.

#### Statutory Section 91 CrPC Notice Template
TraceACT automatically formats legal notices according to the standards of the Indian Code of Criminal Procedure / Section 94 of Bharatiya Nagarik Suraksha Sanhita (BNSS):
- Addressed to: **The Nodal Compliance Officer, [VASP Name]**
- Requisitioning: KYC Dossier (Aadhaar, PAN, Passport, Phone), Linked Bank Account Numbers, IP Login Logs, and Immediate Debit Freeze under Section 102 CrPC / Section 106 BNSS.

---

### 7.8 24/7 Automated Background Tracking & Alerting Suite
**Service:** `backend/services/live_tracking_service.py` & `backend/services/email_service.py`

- **Scheduler:** Runs an asynchronous loop checking monitored wallets every 60 minutes.
- **Diff Engine:** Fetches latest on-chain balance and transaction history, comparing against the stored baseline snapshot.
- **Alert Dispatch:** If a new transaction or balance delta is detected, the engine generates an in-app notification and dispatches an automated SMTP email to the assigned investigator with transaction hashes and updated risk scores.

---

### 7.9 NetworkX Graph Analytics & Centrality Engine
**Service:** `backend/services/graph_analytics_service.py`

TraceACT integrates `networkx` to compute topological graph properties across discovered nodes and edges:
- **Betweenness Centrality (`nx.betweenness_centrality`):** Evaluates which intermediary node lies on the highest fraction of shortest paths. Nodes exceeding $\ge 0.10$ centrality (excluding the root suspect and terminal sink VASPs) are classified as **Critical Bottleneck Mules** (`CRITICAL_BOTTLENECK_MULE`).
- **PageRank & Degree Centralities:** Measures structural absorption prestige to distinguish between high fan-out splitters and terminal deposit sinks.
- **Cycle & Wash-Trading Detection (`nx.simple_cycles`):** Detects circular fund loops ($A \rightarrow B \rightarrow C \rightarrow A$) commonly used by fraud syndicates to simulate volume.
- **Topological Confidence Calibration:** Enhances attribution confidence if the flow from suspect to terminal VASP is strictly acyclic (DAG verified) and penalizes confidence if wash-trading loops are detected.

---

### 7.10 Deterministic Step-Wise Investigation SOP Playbook
**Service:** `backend/services/investigation_engine.py` & `frontend/src/components/InvestigationGuideView.jsx`

Generates a 100% deterministic, zero-LLM Standard Operating Procedure (SOP) tailored to the specific case under Indian Criminal Law (CrPC/BNSS/BSA):
- **Phase 1: Immediate Containment (0–2h "Golden Window"):**
  - **Step 1 (Critical):** Cryptographic Evidence Preservation & SHA-256 Block Height Hashing (Section 65B BSA / Section 65B IEA).
  - **Step 2 (Critical):** Emergency Statutory Debit Freeze Requisition to Primary Actionable VASP (Section 91 & 102 CrPC / Section 94 & 106 BNSS).
- **Phase 2: Active Interdiction (2–24h):**
  - **Step 3 (High):** Interdiction of Key Bottleneck Money Mule identified via NetworkX Betweenness Centrality (Tracing gas-funding exchange origin).
  - **Step 4 (High):** Secondary VASP Subpoenas fulfilling the Minimum Intervention Set (MIS) to secure $\ge 70\%$ case fund coverage.
  - **Step 5 (Medium):** Inquiry and Host Notice for Unknown Service Clusters (`UC-YYYY-XXXX`).
- **Phase 3: Judicial Recovery & Trial (24–72h):**
  - **Step 6 (Medium):** Deployment of 24/7 Automated Blockchain Sentry on unresolved residue funds.
  - **Step 7 (Critical):** Final Police Charge-Sheet Annexures Assembly & Section 65B BSA Certificate for the Trial Court.

---

## 8. Verified VASP Directory & Intelligence Knowledge Base

**Data Store:** `data/vasp_directory.json` & `data/known_entities.json`

The system comes pre-loaded with 25 comprehensively profiled Virtual Asset Service Providers across Indian and Global jurisdictions:

### 8.1 Indian Regulated VASPs (FIU-IND Registered)
1. **CoinDCX** (*Neblio Technologies Pvt Ltd*) — Reg: `FIU-IND/2023/VASP/0012`
2. **WazirX** (*Zanmai Labs Pvt Ltd*) — Reg: `FIU-IND/2023/VASP/0001`
3. **CoinSwitch Kuber** (*Bitcipher Labs LLP*) — Reg: `FIU-IND/2023/VASP/0004`
4. **ZebPay** (*Awlencan Innovations India Ltd*) — Reg: `FIU-IND/2023/VASP/0002`
5. **Mudrex** (*Mudrex India Pvt Ltd*) — Reg: `FIU-IND/2023/VASP/0018`
6. **Giottus Technologies** — Reg: `FIU-IND/2023/VASP/0009`
7. **BuyUCoin** (*iBlock Technologies*) — Reg: `FIU-IND/2023/VASP/0015`
8. **SunCrypto** (*Angel Webtech Pvt Ltd*) — Reg: `FIU-IND/2023/VASP/0022`

### 8.2 Global & Offshore VASPs (With LEA Compliance Portals)
- **Binance Global** (Offshore registered with FIU-IND; dedicated law enforcement portal)
- **Coinbase Global** (US / FinCEN, FCA registered)
- **Kraken** (*Payward Inc.*)
- **OKX**, **Bybit**, **KuCoin**, **Bitfinex**, **HTX (Huobi)**, **Gate.io**, **Bitget**, **MEXC**, **Bitstamp**, **Crypto.com**, **Gemini**, **Paxful**, **Bithumb**.

Each directory record includes:
- Official Corporate Legal Name & Jurisdiction
- Regulatory Status & Registration Identifiers
- Mandatory KYC Policy & Verification Source
- Known Deposit Routers and Cold/Hot Wallets (ETH, BTC, TRX, SOL)
- Dedicated Nodal Compliance Officer Email and Law Enforcement Portal URLs

---

## 9. Database Persistence & Zero-Config High Availability Architecture

**Implementation:** `backend/database/mongo.py`

TraceACT is designed to be **fail-safe**. Investigators in the field or hackathon judges often test code without running a local MongoDB daemon.

```
                  Database Request (e.g. find_one, update_one)
                                       │
                                       ▼
                     Is MongoDB Server Connected?
                                  /         \
                             YES /           \ NO
                                ▼             ▼
                      [Motor / PyMongo]   [EmbeddedAsyncCollection]
                                              │
                                              ├─► Memory Dict (Immediate Read/Write)
                                              └─► File Sync (data/db_store.json)
```

- **When MongoDB is Running:** The platform uses Motor's asynchronous connection pool (`mongodb://localhost:27017/sih_forensics`).
- **When MongoDB is Offline:** The system automatically initializes `EmbeddedAsyncCollection`, which provides an identical async API (`find_one`, `find`, `insert_one`, `update_one`). It keeps records in memory and asynchronously persists them to `data/db_store.json`.
- **Zero Loss:** Switching between MongoDB and the fallback is completely transparent to the application.

---

## 10. REST API Reference & Data Contracts

All endpoints are served under `/api` at `http://localhost:8001`. Interactive Swagger documentation is available at `/docs`.

### 10.1 Multi-Chain Detection & Validation
- **Endpoint:** `POST /api/wallet/detect`
- **Payload:** `{"address": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"}`
- **Response:**
  ```json
  {
    "address": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
    "detectedChain": "ethereum",
    "confidence": "HIGH",
    "formatName": "EVM Hexadecimal (20-byte account)",
    "symbol": "ETH",
    "suggestedAlternativeChains": ["bnb", "polygon"],
    "validationStatus": true,
    "message": "Matched EVM 40-character hexadecimal account address."
  }
  ```

### 10.2 1-Hop Wallet Analysis
- **Endpoint:** `POST /api/wallet/analyze`
- **Payload:** `{"chain": "ethereum", "address": "0x71C836489B990038848971201991802901238910"}`
- **Response:** Returns `WalletOverview`, list of `NormalizedTransaction`, list of `ConnectedWallet`, and 1-hop radial `GraphData`.

### 10.3 Multi-Hop BFS Transaction Tracing
- **Endpoint:** `POST /api/wallet/trace`
- **Payload:**
  ```json
  {
    "chain": "ethereum",
    "address": "0x71C836489B990038848971201991802901238910",
    "maxDepth": 3,
    "direction": "both",
    "minimumTransferValue": "0.1",
    "maxNodes": 50
  }
  ```
- **Response:** Returns `TraceFundsResponse` with BFS nodes, directed edges, reconstructed fund paths, and execution metrics.

### 10.4 Deterministic VASP Attribution
- **Endpoint:** `POST /api/wallet/attribution`
- **Payload:** Same as `AttributionRequest` (includes optional `systemLogic` filter overrides).
- **Response:** Returns `AttributionResponse` containing `nearestVasp`, `vaspCandidates`, `paths`, and `graph`.

### 10.5 Dynamic Heuristics & System Logic Evaluation
- **Endpoint:** `POST /api/wallet/evaluate-heuristics`
- **Payload:**
  ```json
  {
    "address": "0x71C836...",
    "chain": "ethereum",
    "systemLogic": {
      "profile": "fraud_syndicate",
      "sensitivityMultiplier": 1.2,
      "largeTransferThreshold": 2.5
    }
  }
  ```

### 10.6 Incremental Branch Expansion
- **Endpoint:** `POST /api/investigation/expand-node`
- **Payload:** `{"targetAddress": "0x3344b...", "chain": "ethereum", "currentGraph": {...}}`
- **Description:** Fetches counterparties for a selected node and appends them to the active canvas without resetting the graph.

### 10.7 Unified Investigation Decision Pipeline
- **Endpoint:** `POST /api/investigate`
- **Payload:** `AttributionRequest`
- **Response:** Returns complete `InvestigationDossierResponse` containing Taint Accounting, VASP Actionability Rankings, Minimum Intervention Set (MIS), Unknown VASP candidates, Attribution Challenges, Evidence Gaps, and Full 16-Section LEA Report.

### 10.8 Canonical SIH 2026 Reference Demo
- **Endpoint:** `POST /api/investigations/demo`
- **Description:** Instantly returns the canonical multi-branch hackathon evaluation scenario (`CASE-2026-SIH-DEMO-001`) with CoinDCX, Binance, and Unknown Cluster UC-42.

### 10.9 Case Docket Management
- `GET /api/investigations` — List saved cases in database
- `POST /api/investigations/save` — Save or update case docket
- `GET /api/investigations/{case_id}` — Retrieve full case docket
- `DELETE /api/investigations/{case_id}` — Delete case from archive
- `GET /api/investigations/{case_id}/report` — Retrieve stored 16-section report

### 10.10 Monitored Wallets & Live Tracking
- `POST /api/tracking/enable` — Register wallet for 60-minute monitoring
- `POST /api/tracking/disable` — Unregister wallet
- `POST /api/tracking/check-now/{address}` — Manually trigger immediate tracking diff
- `GET /api/tracking/monitored` — List all monitored wallets
- `GET /api/tracking/notifications` — Retrieve in-app notification feed

### 10.11 Verified VASP & Entity Directory
- `GET /api/vasps` — Returns all 25 registered VASPs
- `GET /api/entities` — Returns all known tagged blockchain entities

### 10.12 System Settings & Runtime Configuration
- `GET /api/settings` — Returns current runtime configuration and DB status
- `POST /api/settings` — Updates API keys, RPC endpoints, Ollama host, SMTP credentials
- `GET /api/health` — System health check

---

## 11. User Interface & Investigation Workstation Walkthrough

The TraceACT frontend is structured as a single-page forensic investigation suite featuring five integrated workspace tabs:

### 11.1 Search & Control Bar
- **Address Input:** Auto-detects chain on paste/type, displaying verified chain badge (ETH, BTC, TRX, SOL).
- **Hop Depth Slider:** Interactively selects BFS traversal depth from 1 to 5 hops.
- **Direction Toggle:** Filters fund flow direction (`both`, `outgoing` funds, `incoming` funds).
- **Min Value Filter:** Real-time filter eliminating dust transactions below a threshold.
- **Forensic Filter Controls:** Configures traversal hop depth (1–5 hops), minimum transfer value filter, and directional fund flow.

### 11.2 Tab 1: Interactive Forensic Graph Canvas (`GraphView.jsx`)
- Built with `@xyflow/react` (React Flow).
- **Custom Nodes (`RectangularNode.jsx`):** Renders high-density cards with short address, full copy button, risk severity color, entity badge (e.g., `Verified VASP: CoinDCX`), and transaction flow stats.
- **Radial & Hierarchical Layouts:** Clear visualization of fund fan-outs and multi-hop peeling.
- **Interactive Controls:** Zoom in/out, fit to view, interactive mini-map, and color-coded risk legend.
- **Node Branch Expander:** Clicking any intermediate node allows the investigator to "Expand Branch" to explore that specific counterparty without resetting the canvas.
- **Inspector Modal (`NodeDetailModal.jsx`):** Displays granular wallet metadata, direct counterparties, and one-click pivot actions.
- **Transaction Ledger Drawer (`TransactionList.jsx`):** Paginated table below the graph showing hashes, block heights, values, and direct links to block explorers.

### 11.3 Tab 2: Suspicion Points & Heuristics Breakdown (`SuspicionPointsView.jsx`)
- Displays the composite 0–100 Suspicion Score with visual circular gauge and risk badge (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`).
- **Forensic Profile Switcher:** Toggle between `balanced`, `strict`, `fraud_syndicate`, `relaxed`, and `custom`.
- **16-Rule Breakdown:** Lists all triggered rules with priority badges, forensic descriptions, and evidentiary triggers.
- **Investigator Sliders:** Sliders to tune sensitivity multiplier, large transfer threshold, and burst velocity in real-time.

### 11.4 Tab 3: Investigation Decision Dossier (`InvestigationGuideView.jsx`)
- **Taint Accounting Panel:** Visualizes funds at Known VASPs vs Unknown Clusters vs Unresolved.
- **Conservation Check Banner:** Confirms mathematical consistency of tracked proceeds.
- **Minimum Intervention Set (MIS) Card:** Highlights the minimal set of VASPs needed to capture $\ge 70\%$ of the stolen assets.
- **VASP Actionability Ranking Table:** Prioritized list of VASPs with actionability scores, amount exposure, jurisdiction, and nodal contacts.
- **Unknown Service Clusters:** Cards detailing detected `UC-YYYY-XXXX` clusters, consolidation ratios, sweep frequencies, and heuristic evidence.
- **Attribution Challenge Hypotheses:** Displays adversarial counter-arguments tested by the system.
- **Next Action Recommendation Cards:** Priority-ranked next investigative steps.

### 11.5 Tab 4: Official Forensic Report & Section 91 CrPC Requisition (`ForensicReportView.jsx`)
- **16-Section Formal Report:** Formatted strictly for law enforcement dockets.
- **Section 91 CrPC Notice Generator:** Formatted legal requisition ready for printing or copying into the SAHYOG portal.
- **Evidence Integrity Certificate:** Displays SHA-256 cryptographic hash of the evidence manifest.
- **Export Capabilities:** One-click "Copy Section 91 Notice", "Copy Full Report", or "Print Formal PDF".

### 11.6 Tab 5: Settings & System Status Modal (`SettingsModal.jsx`)
- Allows runtime configuration of:
  - Blockchain API Keys (Etherscan, TronGrid, TronScan)
  - RPC Endpoints (Ethereum, Blockstream, Solana)
  - Database URI (MongoDB connection string)
  - Ollama LLM Host & Model (`http://127.0.0.1:11434`, `llama3.2:3b`)
  - SMTP Alert Configuration (Host, Port, User, Password, Recipient)
  - Investigator Profile (Officer Name, Badge ID, Agency)

---

## 12. Legal, Regulatory & Evidentiary Admissibility Framework

TraceACT is built in strict compliance with the Indian legal and criminal procedure framework:

### 12.1 Section 91, Code of Criminal Procedure, 1973 (CrPC) / Section 94, Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS)
Empowers any Police Officer or Investigating Officer to issue a formal written summons/order to any person or entity (including cryptocurrency exchanges operating in India or offshore) to produce documents or things necessary for the investigation. TraceACT automatically generates this requisition with specific transaction hashes, timestamps, and destination addresses.

### 12.2 Section 102 CrPC / Section 106 BNSS (Power to Seize Property)
Provides statutory power to freeze property suspected to be stolen or which creates suspicion of the commission of an offence. The requisition requests immediate debit freezes on beneficiary custodial accounts.

### 12.3 Section 65B, Indian Evidence Act, 1872 / Section 63, Bharatiya Sakshya Adhiniyam, 2023 (BSA)
Electronic records are admissible in an Indian court of law only when accompanied by a statutory certificate verifying computer operation, system integrity, and non-tampering. TraceACT computes SHA-256 hashes of all on-chain raw manifests and outputs the certificate text with officer signature blocks.

### 12.4 FIU-IND AML/CFT Guidelines for Virtual Digital Assets (VDA)
In March 2023, the Ministry of Finance brought Virtual Digital Asset Service Providers under the **Prevention of Money Laundering Act (PMLA), 2002**. Registered VASPs are reporting entities mandated to maintain KYC records for 5 years and respond to statutory requests from LEAs and FIU-IND. TraceACT indexes these entities with their official FIU-IND registration numbers.

---

## 13. Installation, Setup & Deployment Guide

### 13.1 Prerequisites
- **Node.js:** v18.0.0 or higher (v22+ recommended)
- **Python:** v3.10 or higher (v3.11 / v3.12 / v3.13 tested)
- **Git** (optional, for version control)
- **MongoDB** (optional; the built-in JSON-backed embedded engine operates seamlessly without it)
- **Ollama** (optional; for local AI narrative generation; fallback templates operate if Ollama is not installed)

### 13.2 Rapid 1-Click Launch (Windows)
Double-click `start.cmd` in the project root. This automated batch script:
1. Checks Python, Node.js, and virtual environment.
2. Checks backend health on port `8001` and starts it if offline.
3. Checks frontend on port `3000` and launches `vite` if offline.
4. Opens `http://localhost:3000` in your default browser.

### 13.3 Manual Step-by-Step Installation

#### Step 1: Clone and Configure Environment
```bash
cd SIH_2026

# Copy example environment file
cp .env.example .env
```

#### Step 2: Backend Setup & Execution
```bash
# Create and activate Python virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install backend dependencies
pip install -r backend/requirements.txt

# Start the FastAPI server on port 8001
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload
```
- **Backend API:** `http://localhost:8001`
- **Swagger Documentation:** `http://localhost:8001/docs`
- **Health Check:** `http://localhost:8001/api/health`

#### Step 3: Frontend Setup & Execution
```bash
# Open a new terminal in the frontend directory
cd frontend

# Install Node.js packages
npm install

# Launch Vite development server on port 3000
npm run dev
```
- **Frontend Workstation:** `http://localhost:3000`

---

## 14. Testing, Verification & Reference Demo Scenarios

TraceACT includes built-in test fixtures and reference targets for evaluation:

### 14.1 The Canonical SIH 2026 Reference Demo Scenario
Click the **"🎯 SIH 2026 Reference Demo Scenario"** button in the search bar or run:
```bash
curl -X POST http://localhost:8001/api/investigations/demo
```
**Case Profile:**
- **Case ID:** `CASE-2026-SIH-DEMO-001`
- **Suspect Root Wallet:** `0x71C836489B990038848971201991802901238910` (Ethereum)
- **Stolen Proceeds:** $10.0$ ETH ($₹10.0$ Lakhs)
- **Branch 1 (5.2 ETH / 52%):** Direct deposit into **CoinDCX** (FIU-IND Registered). Actionability: **92/100 (CRITICAL)**.
- **Branch 2 (2.1 ETH / 21%):** Forwarded through intermediate mule `0x3344b...` into **Binance Global Hot Wallet 14**. Actionability: **78/100 (HIGH)**.
- **Branch 3 (1.4 ETH / 14%):** Forwarded through mule `0x5566c...` into **Unknown Cluster UC-2026-0042** (27 addresses, 611 depositors). Actionability: **61/100 (MEDIUM)**.
- **Branch 4 (1.3 ETH / 13%):** Unresolved funds parked in intermediate unhosted wallet.
- **Minimum Intervention Set (MIS):** Recommends serving notices to **CoinDCX** and **Binance** to achieve **73.0% asset coverage** with just 2 notices.

### 14.2 Real On-Chain Mainnet Targets
- **Vitalik Buterin (`vitalik.eth`):** `0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045` (Validates live balance, gas, fees, and clean dampener).
- **Ethereum Foundation:** `0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe`.
- **Binance Hot Wallet:** `0x28C6c06298d514Db089934071355E5743bf21d60`.
- **Bitcoin Legacy Test:** `1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa` (Satoshi Genesis).
- **Tron TRC-20 Test:** `TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t` (Tether USDT contract).

### 14.3 Running Automated Test Suite
```bash
pytest backend/tests -v
```

---

## 15. Future Roadmap & Extensibility

1. **Cross-Chain Bridge Tracing:** Automated hop linkage across LayerZero, Wormhole, Avalanche Bridge, and THORChain cross-chain liquidity pools.
2. **Deep Web & Darknet Scraper Integration:** Continuous automated ingestion of darknet forum deposit addresses and ransomware ransom notes into `known_entities.json`.
3. **Direct SAHYOG API Webhooks:** Direct cryptographic transmission of Section 91 CrPC notice payloads to the Ministry of Home Affairs (MHA) SAHYOG portal via secure government API gateways.
4. **Machine Learning Clustering (DBSCAN / GNNs):** Integrating Graph Neural Networks (GNNs) for automated multi-chain wallet de-anonymization and sybil cluster discovery.
5. **Hardware Security Module (HSM) Signing:** Digital signing of evidence certificates using officer cryptographic tokens (e-Mudhra / USB crypto tokens).

---

## 📜 Legal Notice & Disclaimer
*Project TraceACT is an academic and investigative software system engineered for the Smart India Hackathon (SIH) 2026. All investigative methodologies, rule engine heuristics, and legal notice generators are designed to assist authorized Law Enforcement Officers and Judicial Authorities in the prevention, detection, and investigation of cybercrime under applicable statutory frameworks.*
