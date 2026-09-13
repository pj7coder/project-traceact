// API Client for TraceACT Backend (port 8001)

const API_BASE = import.meta.env.VITE_API_BASE || '/api';

export async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error(`Status ${res.status}`);
    return await res.json();
  } catch (err) {
    try {
      const fallbackRes = await fetch('http://127.0.0.1:8001/api/health');
      if (fallbackRes.ok) return await fallbackRes.json();
    } catch {}
    throw err;
  }
}

export async function detectChain(address) {
  const res = await fetch(`${API_BASE}/wallet/detect`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ address: address.trim() }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Chain detection failed');
  }
  return await res.json();
}

export async function analyzeWallet(chain, address) {
  const res = await fetch(`${API_BASE}/wallet/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      chain: chain.toLowerCase(),
      address: address.trim(),
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Wallet analysis failed');
  }
  return await res.json();
}

export async function traceWalletFunds({
  chain = 'ethereum',
  address,
  maxDepth = 2,
  direction = 'both',
  minimumTransferValue = '0.0',
}) {
  const res = await fetch(`${API_BASE}/wallet/trace`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      chain: chain.toLowerCase(),
      address: address.trim(),
      maxDepth: Number(maxDepth),
      direction,
      minimumTransferValue: String(minimumTransferValue || '0.0'),
      maxNodes: 50,
      maxTransactionsPerWallet: 40,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Multi-hop tracing failed');
  }
  return await res.json();
}

export async function evaluateHeuristics({
  chain = 'ethereum',
  address,
  multihopNodes = [],
  systemLogic = null,
}) {
  const res = await fetch(`${API_BASE}/wallet/evaluate-heuristics`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      chain: chain.toLowerCase(),
      address: address.trim(),
      multihopNodes,
      systemLogic,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Heuristics evaluation failed');
  }
  return await res.json();
}

export async function runUnifiedInvestigation({
  chain = 'ethereum',
  address,
  maxDepth = 2,
  minimumTransferValue = '0.0',
  direction = 'both',
}) {
  const res = await fetch(`${API_BASE}/investigate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      chain: chain.toLowerCase(),
      address: address.trim(),
      maxDepth: Number(maxDepth),
      direction,
      minimumTransferValue: String(minimumTransferValue || '0.0'),
      maxNodes: 50,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Unified investigation failed');
  }
  return await res.json();
}

export async function generateForensicReport({
  chain = 'ethereum',
  targetAddress,
  caseId = null,
  maxDepth = 2,
}) {
  const res = await fetch(`${API_BASE}/report/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      chain: chain.toLowerCase(),
      targetAddress: targetAddress.trim(),
      caseId,
      maxDepth: Number(maxDepth),
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Report generation failed');
  }
  return await res.json();
}

export async function expandNode({
  chain,
  targetAddress,
  currentNodes = [],
  currentEdges = [],
  maxNewNodes = 8,
}) {
  const res = await fetch(`${API_BASE}/investigation/expand-node`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      chain: chain.toLowerCase(),
      targetAddress: targetAddress.trim(),
      currentNodes,
      currentEdges,
      maxNewNodes,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Branch expansion failed');
  }
  return await res.json();
}

export async function getSystemSettings() {
  const res = await fetch(`${API_BASE}/settings`);
  if (!res.ok) throw new Error('Failed to fetch settings');
  return await res.json();
}

export async function getDemoInvestigation() {
  const res = await fetch(`${API_BASE}/investigations/demo`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Demo investigation failed');
  }
  return await res.json();
}
