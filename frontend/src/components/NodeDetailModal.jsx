import React from 'react';
import { X, Copy, Check, ExternalLink, Search, ShieldAlert, CheckCircle2, Flame, AlertTriangle } from 'lucide-react';

export const NodeDetailModal = ({ nodeData, onClose, onTrack, onInvestigate }) => {
  const [copied, setCopied] = React.useState(false);

  if (!nodeData) return null;

  const fullAddr = nodeData.fullAddress || nodeData.address || nodeData.label || '';
  const asset = (nodeData.asset || (fullAddr.startsWith('1') || fullAddr.startsWith('3') || fullAddr.startsWith('bc1') ? 'BTC' : fullAddr.startsWith('T') ? 'TRX' : 'ETH')).toUpperCase();
  const balance = nodeData.balance || nodeData.totalTransferred || nodeData.totalAmount || '0';
  const txCount = nodeData.txCount ?? nodeData.transactionCount ?? 0;
  const riskScore = nodeData.riskScore ?? 0;
  const riskLevel = nodeData.riskLevel || 'LOW';
  const entityName = nodeData.entityName || nodeData.name || 'Unattributed Counterparty';
  const entityType = nodeData.entityType || 'Standard Wallet';
  const tags = nodeData.tags || [];

  const getExplorerInfo = (addr = '', a = 'ETH') => {
    if (a === 'BTC' || addr.startsWith('1') || addr.startsWith('3') || addr.startsWith('bc1')) {
      return { name: 'Mempool.space (BTC)', url: `https://mempool.space/address/${addr}`, color: '#f7931a' };
    }
    if (a === 'TRX' || addr.startsWith('T')) {
      return { name: 'TronScan (TRX)', url: `https://tronscan.org/#/address/${addr}`, color: '#eb0029' };
    }
    if (a === 'SOL') {
      return { name: 'Solscan (SOL)', url: `https://solscan.io/account/${addr}`, color: '#14f195' };
    }
    return { name: 'Blockscout (ETH)', url: `https://eth.blockscout.com/address/${addr}`, color: '#0071e3' };
  };

  const explorerInfo = getExplorerInfo(fullAddr, asset);

  const formatModalBalance = (bal, a) => {
    const num = parseFloat(String(bal || '0'));
    if (isNaN(num)) return `0 ${a}`;
    if (a === 'BTC') return `${num.toFixed(num < 0.05 ? 6 : 4)} BTC`;
    if (a === 'TRX') return `${num.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 })} TRX`;
    return `${num.toFixed(num < 0.1 ? 4 : 2)} ${a}`;
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(fullAddr);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div 
              style={{
                width: 12,
                height: 12,
                borderRadius: '50%',
                backgroundColor: nodeData.nodeType === 'investigated' ? '#0071e3' : (nodeData.nodeColor || '#10b981')
              }} 
            />
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <h3 style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)' }}>
                  {entityName}
                </h3>
                <span
                  style={{
                    fontSize: 9.5,
                    fontWeight: 700,
                    padding: '1px 6px',
                    borderRadius: 4,
                    color: explorerInfo.color,
                    background: `${explorerInfo.color}18`,
                    border: `1px solid ${explorerInfo.color}40`,
                  }}
                >
                  {asset}
                </span>
              </div>
              <p style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                {entityType}
              </p>
            </div>
          </div>
          <button className="apple-icon-btn" onClick={onClose}>
            <X size={16} />
          </button>
        </div>

        {/* Address Row */}
        <div 
          style={{
            background: 'var(--bg-glass-subtle)',
            padding: '10px 14px',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--border-subtle)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: 16
          }}
        >
          <span style={{ fontSize: 12, fontFamily: 'ui-monospace, monospace', color: 'var(--text-primary)', wordBreak: 'break-all' }}>
            {fullAddr}
          </span>
          <button 
            className="apple-btn apple-btn-ghost" 
            onClick={handleCopy}
            style={{ padding: '4px 8px', fontSize: 12 }}
          >
            {copied ? <Check size={14} color="#34c759" /> : <Copy size={14} />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>
        </div>

        {/* Metrics Grid */}
        <div 
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(2, 1fr)',
            gap: 12,
            marginBottom: 16
          }}
        >
          <div style={{ padding: '12px', borderRadius: 'var(--radius-sm)', background: 'var(--bg-tag)' }}>
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Current Balance</div>
            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', marginTop: 4 }}>
              {formatModalBalance(balance, asset)}
            </div>
          </div>

          <div style={{ padding: '12px', borderRadius: 'var(--radius-sm)', background: 'var(--bg-tag)' }}>
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Transactions Count</div>
            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', marginTop: 4 }}>
              {txCount} Total
            </div>
          </div>

          <div style={{ padding: '12px', borderRadius: 'var(--radius-sm)', background: 'var(--bg-tag)' }}>
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Risk Level & Score</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 4 }}>
              <span className={`apple-badge badge-${riskLevel.toLowerCase()}`}>
                {riskLevel}
              </span>
              <span style={{ fontSize: 14, fontWeight: 600 }}>{riskScore} / 100</span>
            </div>
          </div>

          <div style={{ padding: '12px', borderRadius: 'var(--radius-sm)', background: 'var(--bg-tag)' }}>
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Hop Distance</div>
            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', marginTop: 4 }}>
              {nodeData.depth !== undefined ? `Hop ${nodeData.depth}` : 'Direct'}
            </div>
          </div>
        </div>

        {/* Tags */}
        {tags.length > 0 && (
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)', textTransform: 'uppercase', marginBottom: 8 }}>
              Forensic Flags & Tags
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {tags.map((t, idx) => (
                <span 
                  key={idx}
                  style={{
                    fontSize: 11,
                    padding: '4px 10px',
                    borderRadius: 'var(--radius-pill)',
                    background: 'var(--bg-tag)',
                    border: '1px solid var(--border-subtle)',
                    color: 'var(--text-secondary)'
                  }}
                >
                  {t}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div style={{ display: 'flex', gap: 8, justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--border-subtle)', paddingTop: 16 }}>
          <a
            href={explorerInfo.url}
            target="_blank"
            rel="noopener noreferrer"
            className="apple-btn apple-btn-secondary"
            style={{ fontSize: 11, display: 'inline-flex', alignItems: 'center', gap: 5, textDecoration: 'none' }}
          >
            <ExternalLink size={13} />
            <span>{explorerInfo.name}</span>
          </a>

          <div style={{ display: 'flex', gap: 8 }}>
            <button 
              className="apple-btn apple-btn-secondary"
              onClick={() => {
                onClose();
                if (onTrack) onTrack(nodeData);
              }}
            >
              <Search size={14} />
              Track & Expand
            </button>
            <button 
              className="apple-btn apple-btn-primary"
              onClick={() => {
                onClose();
                if (onInvestigate) onInvestigate(fullAddr);
              }}
            >
              Investigate Address
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
