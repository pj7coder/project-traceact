import React, { useState } from 'react';
import { Copy, Check, ArrowDownLeft, ArrowUpRight } from 'lucide-react';

const formatCurrencyValue = (val, asset = 'ETH') => {
  if (val === null || val === undefined || val === '') return `0.0000 ${asset}`;
  const num = parseFloat(String(val));
  if (isNaN(num)) return `0 ${asset}`;

  const cleanAsset = (asset || 'ETH').toUpperCase();
  if (cleanAsset === 'BTC') {
    return `${num.toFixed(num < 0.01 ? 6 : 4)} BTC`;
  }
  if (cleanAsset === 'TRX') {
    return `${num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} TRX`;
  }
  if (cleanAsset === 'SOL') {
    return `${num.toFixed(3)} SOL`;
  }
  return `${num.toFixed(num < 0.1 ? 4 : 3)} ${cleanAsset}`;
};

export const WalletOverviewCard = ({ wallet, metadata }) => {
  const [copied, setCopied] = useState(false);

  if (!wallet) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(wallet.address);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const riskLevel = (wallet.riskLevel || 'LOW').toUpperCase();
  const riskScore = wallet.riskScore ?? 0;
  const asset = (wallet.asset || (wallet.chain === 'bitcoin' ? 'BTC' : wallet.chain === 'tron' ? 'TRX' : wallet.chain === 'solana' ? 'SOL' : 'ETH')).toUpperCase();
  const balance = wallet.balance || '0';
  const txTotal = wallet.transactionCount ?? 0;
  const incoming = wallet.incomingCount ?? 0;
  const outgoing = wallet.outgoingCount ?? 0;
  const counterparties = wallet.uniqueConnectedWallets ?? metadata?.totalPeersDiscovered ?? 0;
  const tags = wallet.tags || [];

  const getRiskClass = (level) => {
    switch (level) {
      case 'CRITICAL': return 'badge-critical';
      case 'HIGH': return 'badge-high';
      case 'MEDIUM': return 'badge-medium';
      case 'CLEAN': return 'badge-clean';
      default: return 'badge-low';
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      {/* Top Address & Risk Strip */}
      <div
        style={{
          background: 'var(--bg-card)',
          borderRadius: 'var(--radius-sm)',
          border: '1px solid var(--border-subtle)',
          padding: '10px 14px',
          boxShadow: 'var(--shadow-sm)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 10,
        }}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ fontSize: 9.5, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Investigated Address ({wallet.chain || 'Ethereum'})
            </span>
            <span className={`apple-badge ${getRiskClass(riskLevel)}`}>
              {riskLevel} ({riskScore}/100)
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 13, fontFamily: 'ui-monospace, monospace', fontWeight: 600, color: 'var(--text-primary)' }}>
              {wallet.address}
            </span>
            <button
              onClick={handleCopy}
              className="apple-icon-btn"
              style={{ width: 22, height: 22 }}
              title="Copy Address"
            >
              {copied ? <Check size={11} color="#34c759" /> : <Copy size={11} />}
            </button>
          </div>
        </div>

        {/* Forensic Tags */}
        {tags.length > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 5, flexWrap: 'wrap' }}>
            {tags.map((t, idx) => (
              <span
                key={idx}
                style={{
                  fontSize: 10,
                  padding: '2px 8px',
                  borderRadius: 'var(--radius-pill)',
                  background: 'var(--bg-tag)',
                  border: '1px solid var(--border-subtle)',
                  color: 'var(--text-secondary)',
                  fontWeight: 500,
                }}
              >
                {t}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Metrics Row (Compact 4 Cards) */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
          gap: 10,
        }}
      >
        {/* Balance */}
        <div
          style={{
            background: 'var(--bg-card)',
            borderRadius: 'var(--radius-xs)',
            border: '1px solid var(--border-subtle)',
            padding: '10px 12px',
            boxShadow: 'var(--shadow-sm)',
          }}
        >
          <div style={{ fontSize: 9.5, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.03em', marginBottom: 2 }}>
            On-Chain Balance
          </div>
          <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>
            {formatCurrencyValue(balance, asset)}
          </div>
          <div style={{ fontSize: 9.5, color: 'var(--text-tertiary)', marginTop: 2 }}>
            Extracted from ledger
          </div>
        </div>

        {/* Transactions Breakdown */}
        <div
          style={{
            background: 'var(--bg-card)',
            borderRadius: 'var(--radius-xs)',
            border: '1px solid var(--border-subtle)',
            padding: '10px 12px',
            boxShadow: 'var(--shadow-sm)',
          }}
        >
          <div style={{ fontSize: 9.5, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.03em', marginBottom: 2 }}>
            Total Transactions
          </div>
          <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>
            {txTotal} <span style={{ fontSize: 11, fontWeight: 500, color: 'var(--text-secondary)' }}>txs</span>
          </div>
          <div style={{ display: 'flex', gap: 8, fontSize: 9.5, color: 'var(--text-secondary)', marginTop: 2 }}>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 2 }}>
              <ArrowDownLeft size={10} color="#34c759" /> {incoming} In
            </span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 2 }}>
              <ArrowUpRight size={10} color="#ff9f0a" /> {outgoing} Out
            </span>
          </div>
        </div>

        {/* Counterparties */}
        <div
          style={{
            background: 'var(--bg-card)',
            borderRadius: 'var(--radius-xs)',
            border: '1px solid var(--border-subtle)',
            padding: '10px 12px',
            boxShadow: 'var(--shadow-sm)',
          }}
        >
          <div style={{ fontSize: 9.5, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.03em', marginBottom: 2 }}>
            Counterparties
          </div>
          <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>
            {counterparties} <span style={{ fontSize: 11, fontWeight: 500, color: 'var(--text-secondary)' }}>peers</span>
          </div>
          <div style={{ fontSize: 9.5, color: 'var(--text-tertiary)', marginTop: 2 }}>
            Discovered nodes
          </div>
        </div>

        {/* Activity Window */}
        <div
          style={{
            background: 'var(--bg-card)',
            borderRadius: 'var(--radius-xs)',
            border: '1px solid var(--border-subtle)',
            padding: '10px 12px',
            boxShadow: 'var(--shadow-sm)',
          }}
        >
          <div style={{ fontSize: 9.5, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.03em', marginBottom: 2 }}>
            Activity Timeline
          </div>
          <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-primary)', marginTop: 2 }}>
            {wallet.lastSeen ? new Date(wallet.lastSeen).toLocaleDateString() : 'Active'} (Latest)
          </div>
          <div style={{ fontSize: 9.5, color: 'var(--text-tertiary)', marginTop: 2 }}>
            First: {wallet.firstSeen ? new Date(wallet.firstSeen).toLocaleDateString() : 'Observed'}
          </div>
        </div>
      </div>
    </div>
  );
};
