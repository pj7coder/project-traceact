# 🎯 Project TraceACT — Comprehensive SIH Hackathon Q&A Master Guide
### Everything Judges Can Ask: Theory, Technical, Non-Technical, Legal & Curveball Questions
**Target Event:** Smart India Hackathon (SIH) 2026  
**Project:** TraceACT — Automated Cryptocurrency Wallet Attribution & Forensic Intelligence Engine  
**Designed For:** Quick review, pitch defense, technical grilling, and panel evaluation.

---

## 📑 Table of Categories

- [1. 💡 Category 1: Elevator Pitch & Problem Statement (Non-Technical)](#1--category-1-elevator-pitch--problem-statement-non-technical)
- [2. 🔬 Category 2: Blockchain Forensics & Theoretical Concepts](#2--category-2-blockchain-forensics--theoretical-concepts)
- [3. ⚙️ Category 3: System Architecture & Technical Implementation](#3--category-3-system-architecture--technical-implementation)
- [4. 🧠 Category 4: Algorithmic Engines, Heuristics & Scoring](#4--category-4-algorithmic-engines-heuristics--scoring)
- [5. ⚖️ Category 5: Law, Police Procedure & Court Admissibility](#5--category-5-law-police-procedure--court-admissibility)
- [6. ⚔️ Category 6: Tough Counter-Questions & Judge Curveballs](#6--category-6-tough-counter-questions--judge-curveballs)
- [7. 🚀 Category 7: Comparison with Chainalysis, Feasibility & Roadmap](#7--category-7-comparison-with-chainalysis-feasibility--roadmap)

---

## 1. 💡 Category 1: Elevator Pitch & Problem Statement (Non-Technical)

### Q1. What is Project TraceACT in one sentence?
**Answer:**  
TraceACT is an automated blockchain forensic intelligence workstation that traces stolen cryptocurrency across multi-hop peeling chains and deterministically attributes the funds to regulated exchanges (VASPs) to generate court-admissible Section 91 CrPC freeze notices for Indian Law Enforcement Agencies.

### Q2. What exact problem are you solving for police officers?
**Answer:**  
When cyber victims lose crypto, police officers only get an unknown alphanumeric wallet address. Criminals hop funds across 3–5 intermediate wallets to confuse investigators. Manually analyzing block explorers takes days, during which criminals cash out. TraceACT automates multi-hop tracing in under 3 seconds and pinpoints the exact exchange where the money landed.

### Q3. Why can’t police just use free block explorers like Etherscan?
**Answer:**  
1. Etherscan only shows **1 hop at a time** — it cannot automatically trace 3 to 5 hops outward.
2. It does not calculate **Taint Accounting** (how much stolen money went where).
3. It does not tell the officer which exchange deposit address belongs to an Indian FIU-IND registered entity.
4. It cannot generate formal Section 91 CrPC legal notices or Section 65B evidence certificates.

### Q4. Who are the end users of this platform?
**Answer:**  
- **Primary:** State Police Cyber Crime Cells, Indian Cyber Crime Coordination Centre (I4C), and the National Cyber Crime Reporting Portal (NCRP / SAHYOG).
- **Secondary:** Financial Intelligence Unit - India (FIU-IND), Enforcement Directorate (ED), CBI, and Central Board of Direct Taxes (CBDT).

### Q5. What happens after an investigator clicks "Generate Report"?
**Answer:**  
The system produces a comprehensive 16-section forensic dossier and an official **Section 91 CrPC (or Section 94 BNSS)** statutory notice pre-filled with the exchange's legal name, compliance officer email, exact deposit transaction hashes, and an order to immediately freeze the criminal's KYC-linked bank account.

---

## 2. 🔬 Category 2: Blockchain Forensics & Theoretical Concepts

### Q6. What is a VASP, and why is VASP attribution the holy grail of crypto forensics?
**Answer:**  
- **VASP:** Virtual Asset Service Provider (centralized cryptocurrency exchanges like CoinDCX, WazirX, Binance).
- **Why it matters:** On-chain wallets are pseudo-anonymous strings. But to convert crypto into real INR/fiat, criminals **must** deposit into a VASP. Regulated VASPs collect mandatory KYC (Aadhaar, PAN, phone numbers, bank accounts). Attributing funds to a VASP turns an anonymous wallet into a real human identity.

### Q7. What is an Unhosted Wallet vs a Custodial Wallet?
**Answer:**  
- **Unhosted (Self-Custody):** Private keys are held by the user (e.g., MetaMask, Trust Wallet, Ledger). No KYC exists; police cannot freeze this wallet directly.
- **Custodial Wallet:** Private keys are controlled by an exchange (e.g., CoinDCX, Binance). The exchange maintains user KYC and can freeze accounts upon legal notice.

### Q8. What is a "Peeling Chain" and how do criminals use it?
**Answer:**  
A peeling chain is a money-laundering technique where a suspect takes a large sum (e.g., 10 ETH), peels off a small amount (e.g., 0.5 ETH) to cash out, and transfers the remainder (9.5 ETH) to a brand-new change address. This process repeats rapidly across multiple hops to simulate normal retail transactions.

### Q9. What is Proportional Taint Accounting?
**Answer:**  
If a suspect wallet receives 10 ETH of illicit funds and has 10 ETH of clean funds (total: 20 ETH), any outbound transfer is considered **50% tainted**. TraceACT tracks these mathematical proportions along every branch so investigators know exactly how much stolen value entered each destination exchange.

### Q10. What is the "Fund Conservation Check"?
**Answer:**  
In physics and accounting, money cannot be created out of thin air. TraceACT checks if:
$$\text{Accounted Funds} = \text{Known VASP} + \text{Unknown Clusters} + \text{Unresolved} + \text{Mining Fees}$$
If the total exceeds the initial stolen amount by $>5\%$, the system flags a **Conservation Anomaly**, indicating external co-mingling or multi-source deposits.

### Q11. What is the Minimum Intervention Set (MIS)?
**Answer:**  
When stolen funds fragment into 10 different exchanges, police cannot issue 10 separate subpoenas in time. TraceACT's MIS algorithm uses a greedy set-cover optimization to find the **smallest number of VASPs needed to freeze $\ge 70\%$ of the stolen money** (e.g., serving notices to just 2 exchanges recovers 73% of the funds).

### Q12. What are "Unknown Service Clusters" (`UC-YYYY-XXXX`)?
**Answer:**  
Not all commercial platforms are registered exchanges. Some are unlicensed OTC desks, illegal betting collection wallets, or bot-driven sweepers. TraceACT detects their exchange-like behavioral patterns (high frequency, rapid sweeping, many depositors) and tags them as an **Unknown Cluster** (e.g., `UC-2026-0042`) without guessing false identities.

---

## 3. ⚙️ Category 3: System Architecture & Technical Implementation

### Q13. What is the complete technology stack used in TraceACT?
**Answer:**  
- **Frontend:** React 18, Vite 6, `@xyflow/react` (React Flow 12) for hardware-accelerated interactive graph topology, Lucide React, and native Vanilla CSS variables.
- **Backend:** Python 3.11+, FastAPI (async ASGI), Uvicorn, Pydantic v2, and Async HTTPX.
- **Graph Analytics:** NetworkX (Betweenness Centrality, PageRank, Cycle Detection, Bottleneck Mule Identification).
- **Blockchain Ingestion:** Blockscout REST API v2, Public Ethereum JSON-RPC, Blockstream (Bitcoin), TronGrid/TronScan (Tron), and Solana RPC.
- **Database:** MongoDB (Motor / PyMongo) with an automatic fail-safe `EmbeddedAsyncCollection` disk persistence (`data/db_store.json`).
- **Forensic AI:** Local Ollama LLM (`llama3.2:3b`) with deterministic fallback templates.

### Q14. How does your multi-hop traversal work without freezing or crashing?
**Answer:**  
We implement an **Asynchronous Breadth-First Search (BFS)** engine:
1. It queries each hop level concurrently using `asyncio.gather`.
2. It maintains a `visited_addresses` and visited edge signature set to **prevent circular loops/cycles**.
3. It enforces strict transfer threshold filters and caps rendering at 50–100 nodes to prevent browser DOM lag.

### Q15. What happens if MongoDB is not installed or the database service goes down?
**Answer:**  
TraceACT has a **zero-downtime architecture**. In `backend/database/mongo.py`, we created an `EmbeddedAsyncCollection`. If MongoDB is unreachable, it automatically stores records in memory and saves them asynchronously to `data/db_store.json`. The app functions with 100% feature parity and zero crashes.

### Q16. Why did you choose React Flow (`@xyflow/react`) instead of D3.js or Cytoscape?
**Answer:**  
React Flow provides seamless hardware-accelerated DOM rendering, native React state integration, customizable SVG node cards, built-in zoom/pan controls, and mini-map capabilities. It allows custom interactive nodes (`RectangularNode.jsx`) with live copy buttons, status pills, and branch expansion triggers.

### Q17. How does the system auto-detect cryptocurrency addresses?
**Answer:**  
`multi_chain_service.py` uses cryptographic regex and prefix matching:
- **EVM (ETH, BNB, Polygon):** `^0x[a-fA-F0-9]{40}$` + EIP-55 checksum.
- **Bitcoin:** Bech32 Native SegWit (`bc1q...`), Taproot (`bc1p...`), Legacy P2PKH (`1...`), Script P2SH (`3...`).
- **Tron (TRC-20):** `^T[a-zA-HJ-NP-Z0-9]{33}$`.
- **Solana:** Base58 string (32 to 44 characters).

### Q18. How does the 60-minute live tracking feature work?
**Answer:**  
`live_tracking_service.py` runs a background `asyncio` task loop every 60 minutes. It checks monitored wallets against their baseline snapshot. If a new transaction or balance change is detected, it triggers an in-app alert and dispatches an automated SMTP email to the investigator (`alerts@sahyog-lea.gov.in`).

---

## 4. 🧠 Category 4: Algorithmic Engines, Heuristics & Scoring

### Q19. How does the 16-Priority Rule Engine calculate the Suspicion Score (0–100)?
**Answer:**  
It inspects on-chain transactions against 16 prioritized rules (P1 Sanctions = $+100$, P2 Ransomware = $+95$, P3 Stolen Funds = $+92$, P5 Mixers = $+83$, P6 Peeling/Rapid Movement = $+75$, down to P16 Clean VASP Dampener = $-20$).  
It uses an anchor formula:
$$S_{\text{raw}} = (\text{Top Weight} \times 0.86) + \sum (\text{Secondary Decay}) + \text{Volume Factor} + \text{Clean Dampeners}$$
The result is scaled by the investigator's sensitivity profile to yield a precise score between 1 and 99.

### Q20. What are the "Investigator System Logic Profiles"?
**Answer:**  
Different cybercrimes require different investigative criteria:
- **Balanced:** Standard baseline SOP for financial fraud.
- **Strict:** 1.25x multiplier, disables clean dampeners; ideal for terror financing & ransomware.
- **Fraud Syndicate:** Boosts rapid movement ($+90$) and unhosted hopping ($+45$); ideal for mule accounts.
- **Relaxed:** 0.75x multiplier; calibrates for high-volume OTC traders.
- **Custom:** Investigator manually tunes sliders and enables/disables specific rules.

### Q21. Why don't you use AI/LLMs to decide wallet attribution?
**Answer:**  
**Judicial integrity.** LLMs can hallucinate. In a criminal trial, an officer cannot tell a High Court judge that "ChatGPT thought this wallet belonged to Binance." Attribution in TraceACT is **100% deterministic and rule-based**, verified against on-chain deposit contracts and official FIU-IND registries. The LLM (Ollama) is only used for drafting natural-language narrative summaries.

### Q22. How does the system extract 28+ behavioral features for unknown VASP discovery?
**Answer:**  
`vasp_discovery_service.py` computes statistical features across:
- **Consolidation Ratio:** Unique senders vs receivers (many-to-one aggregation).
- **Sweep Frequency:** Outflow occurring within 2 hours of inflow.
- **Balance Retention Time:** Median hours funds sit idle before sweeping.
- **Destination Concentration:** Percentage of volume routed to the top repeated destination.
Wallets with exchange-like operational patterns score $\ge 75/100$ and are flagged as probable custodial services.

### Q23. What is the "Attribution Challenge Engine"?
**Answer:**  
It acts as an **adversarial devil's advocate**. Before an officer serves a freeze notice, it automatically checks alternative hypotheses:
- *Could this be a CoinJoin mixing pool?*
- *Could this be a cross-chain liquidity bridge router?*
- *Could this be a merchant payment or a dust attack?*
If counter-hypotheses are valid, it lowers the confidence tier and prompts human corroboration.

---

## 5. ⚖️ Category 5: Law, Police Procedure & Court Admissibility

### Q24. What is Section 91 CrPC (and Section 94 BNSS)?
**Answer:**  
**Section 91 of the Code of Criminal Procedure, 1973** (now Section 94 of the Bharatiya Nagarik Suraksha Sanhita, 2023) empowers an Investigating Police Officer to issue a statutory summons/order to any entity to produce documents, electronic records, or evidence necessary for an investigation. TraceACT auto-generates this exact legal notice.

### Q25. What is Section 102 CrPC (and Section 106 BNSS)?
**Answer:**  
It gives police officers the statutory power to **seize or freeze property** that is suspected to be stolen or linked to an offence. In crypto investigations, this is the legal provision used to order an exchange to place an immediate **debit freeze** on a suspect's account.

### Q26. How is electronic blockchain evidence admissible in an Indian court?
**Answer:**  
Under **Section 65B of the Indian Evidence Act, 1872** (now Section 63 of the Bharatiya Sakshya Adhiniyam, 2023 - BSA), electronic records are admissible only when certified by an authorized officer regarding system integrity, non-tampering, and verified computer operation. TraceACT automatically generates this certificate complete with cryptographic SHA-256 evidence hashes.

### Q27. What is FIU-IND, and why is its registration crucial?
**Answer:**  
**Financial Intelligence Unit - India (FIU-IND)** is the central national agency responsible for receiving and analyzing financial transactions related to money laundering. Since March 2023, all crypto exchanges operating in India must be registered with FIU-IND under PMLA. TraceACT indexes their official registration numbers (e.g., CoinDCX: `FIU-IND/2023/VASP/0012`) so notices go directly to verified Indian compliance officers.

### Q28. What if the stolen cryptocurrency went to an offshore exchange like Binance or Kraken?
**Answer:**  
1. Major offshore exchanges (like Binance) have registered with FIU-IND as offshore reporting entities and maintain dedicated Law Enforcement Request Portals (LERT).
2. TraceACT's report formats the exact evidentiary packet needed for bilateral mutual legal assistance (MLAT), Interpol Purple Notices, or direct LERT portal submission.

---

## 6. ⚔️ Category 6: Tough Counter-Questions & Judge Curveballs

### Q29. "What if the criminal swapped their funds to Monero (XMR)?"
**Answer:**  
Monero uses ring signatures and stealth addresses, making on-chain tracing opaque. However, **criminals cannot buy Monero with cash directly in India** — they must use a swap service, DEX, or centralized exchange. TraceACT traces the trail up to the exact instant swap service or deposit router where the swap was initiated. Serving a Section 91 notice to that swap point yields deposit timestamps, source IP addresses, and linked payout addresses.

### Q30. "What if the suspect used Tornado Cash or a CoinJoin mixer?"
**Answer:**  
TraceACT's Rule Engine explicitly flags mixer interaction (**Priority 5, Weight +83**). The system marks the output addresses as tainted, maps the mixing pool boundary, and flags the transaction as an intentional obfuscation technique in the Section 91 dossier, which establishes criminal mens rea (guilty mind) in court.

### Q31. "How do you distinguish between an exchange deposit address and an omnibus hot wallet?"
**Answer:**  
- **Deposit Router / Address:** A unique address generated for a specific customer deposit. If suspect funds enter here, a notice to the exchange reveals the specific customer's KYC.
- **Omnibus Hot Wallet:** A high-volume pooling wallet containing millions in assets from all users (e.g., Binance 14). TraceACT distinguishes between the two and guides the officer to target the deposit router transaction hash.

### Q32. "What if an innocent person received money from the suspect wallet?"
**Answer:**  
This is why TraceACT uses **Proportional Taint Accounting** and the **Attribution Challenge Engine**. It doesn't naively label every counterparty as criminal. It checks whether the receiving wallet has normal retail patterns (Rule 16 clean dampener) and requires human review if the amount is negligible or looks like a commercial payment.

### Q33. "How do you handle API rate limits during live courtroom demonstrations?"
**Answer:**  
TraceACT implements a resilient 3-layer cascade:
1. Primary: Blockscout REST API v2 (zero-auth, no key needed).
2. Secondary: Public Ethereum JSON-RPC nodes.
3. Fallback: Resilient local sandbox mocks pre-cached in `multi_chain_service.py`. The demo will **never fail** even without internet.

---

## 7. 🚀 Category 7: Comparison with Chainalysis, Feasibility & Roadmap

### Q34. How does TraceACT compare with Chainalysis, Elliptic, or TRM Labs?
**Answer:**  

| Feature | Chainalysis / TRM Labs | Project TraceACT |
| :--- | :--- | :--- |
| **Cost** | Millions of Rupees (₹40–80 Lakhs/year) | **100% Free & Open-Source** for Indian Police |
| **Data Privacy** | Sends sensitive police case data to US cloud servers | **100% Self-Hosted & On-Premises** (Zero data leakage) |
| **Indian Legal System** | Generic international reports | Native **Section 91 CrPC & Section 65B BSA** notices |
| **FIU-IND Integration** | Global exchange tags | 25 Verified Indian & Offshore **FIU-IND Registrations** |
| **Hardware Reqs** | Heavy enterprise setup | Runs on a standard laptop with local Ollama LLM |

### Q35. What is the operational cost of running TraceACT in a police station?
**Answer:**  
**Virtually zero.** TraceACT uses public blockchain RPCs, free block explorer REST tiers, local disk-backed databases (`mongo.py`), and local open-source LLMs (Ollama `llama3.2:3b`). A police cyber cell can run it on an existing office workstation without recurring SaaS subscriptions.

### Q36. What are the current limitations of your project?
**Answer:**  
1. Cross-chain atomic bridge hops (e.g., swapping ETH to SOL via Wormhole) currently require running separate chain searches.
2. Direct integration with the SAHYOG portal is currently export-based (copy/PDF) rather than an automated live government API webhook.

### Q37. What is your future development roadmap?
**Answer:**  
1. **Cross-Chain Bridge Stitching:** Automatically bridging EVM transactions to Solana/Bitcoin through LayerZero and ThorChain liquidity pools.
2. **Direct SAHYOG API Webhook:** Direct, encrypted transmission of Section 91 notices from TraceACT straight into the Ministry of Home Affairs (MHA) portal.
3. **Graph Neural Networks (GNNs):** Implementing AI-driven unsupervised clustering to de-anonymize complex syndicate mule rings automatically.

---

## 💡 Quick Tips for the SIH Jury Presentation

1. **Start with the Impact:** *"Respected jury, in crypto crime, time is money. In the first 60 minutes, stolen crypto moves through 3 hops into an exchange. If police don't freeze it in that window, the money is gone forever. TraceACT automates this in 3 seconds."*
2. **Show, Don't Just Tell:** Trace an authentic target wallet address live on the canvas. It instantly showcases the multi-hop fund flow split into VASPs and counterparties with real on-chain transaction data.
3. **Highlight Legal Compliance:** Emphasize that your report isn't just pretty charts — it generates the **actual Section 91 CrPC notice** with Section 65B BSA cryptographic certificates that an IO (Investigating Officer) can sign and send immediately.
4. **Be Confident on AI:** State clearly: *"We do NOT use AI to guess wallet ownership; our attribution is 100% deterministic and court-admissible. We use AI only for narrative synthesis."*
