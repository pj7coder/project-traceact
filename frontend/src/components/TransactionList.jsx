import React, { useState } from 'react';
import { Copy, Check, ArrowDownLeft, ArrowUpRight, ExternalLink } from 'lucide-react';

export const TransactionList = ({ transactions = [], targetAddress }) => {
  const [copiedHash, setCopiedHash] = useState(null);

  if (!transactions || transactions.length === 0) {
    return null;
  }

  const handleCopy = (hash) => {
    navigator.clipboard.writeText(hash);
    setCopiedHash(hash);
    setTimeout(() => setCopiedHash(null), 1500);
  };

  const cleanTarget = (targetAddress || '').toLowerCase();

  return (
    <div
      style={{
        background: 'var(--bg-card)',
        borderRadius: 'var(--radius-md)',
        border: '1px solid var(--border-subtle)',
        boxShadow: 'var(--shadow-sm)',
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '16px 20px',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div>
          <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>
            On-Chain Transaction Trail
          </h3>
          <p style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
            Direct raw transaction history returned by ledger normalizer ({transactions.length} entries)
          </p>
        </div>
      </div>

      {/* Table */}
      <div style={{ overflowX: 'auto', maxHeight: 320 }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: 12 }}>
          <thead>
            <tr style={{ background: 'var(--bg-glass-subtle)', color: 'var(--text-tertiary)', borderBottom: '1px solid var(--border-subtle)', fontSize: 11, textTransform: 'uppercase' }}>
              <th style={{ padding: '10px 16px' }}>Tx Hash</th>
              <th style={{ padding: '10px 16px' }}>Direction</th>
              <th style={{ padding: '10px 16px' }}>Counterparty</th>
              <th style={{ padding: '10px 16px' }}>Value</th>
              <th style={{ padding: '10px 16px' }}>Timestamp</th>
              <th style={{ padding: '10px 16px' }}>Status</th>
            </tr>
          </thead>
          <tbody>
            {transactions.slice(0, 50).map((tx, idx) => {
              const isIncoming = tx.direction === 'incoming' || tx.toAddress?.toLowerCase() === cleanTarget;
              const counterparty = isIncoming ? tx.fromAddress : tx.toAddress;
              const shortCounterparty = counterparty ? `${counterparty.slice(0, 6)}...${counterparty.slice(-4)}` : 'N/A';
              const shortHash = tx.txHash ? `${tx.txHash.slice(0, 8)}...${tx.txHash.slice(-6)}` : 'N/A';

              return (
                <tr
                  key={tx.txHash || idx}
                  style={{
                    borderBottom: '1px solid var(--border-subtle)',
                    transition: 'background 0.15s ease',
                  }}
                  className="tx-row"
                >
                  <td style={{ padding: '10px 16px', fontFamily: 'ui-monospace, monospace' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <span>{shortHash}</span>
                      {tx.txHash && (
                        <button
                          onClick={() => handleCopy(tx.txHash)}
                          style={{
                            background: 'none',
                            border: 'none',
                            cursor: 'pointer',
                            color: 'var(--text-tertiary)',
                            padding: 2,
                            display: 'flex',
                          }}
                          title="Copy Tx Hash"
                        >
                          {copiedHash === tx.txHash ? <Check size={11} color="#34c759" /> : <Copy size={11} />}
                        </button>
                      )}
                    </div>
                  </td>
                  <td style={{ padding: '10px 16px' }}>
                    <span
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 4,
                        fontSize: 11,
                        fontWeight: 600,
                        color: isIncoming ? 'var(--risk-clean)' : 'var(--risk-medium)',
                      }}
                    >
                      {isIncoming ? <ArrowDownLeft size={13} /> : <ArrowUpRight size={13} />}
                      {isIncoming ? 'IN' : 'OUT'}
                    </span>
                  </td>
                  <td style={{ padding: '10px 16px', fontFamily: 'ui-monospace, monospace' }}>
                    {shortCounterparty}
                  </td>
                  <td style={{ padding: '10px 16px', fontWeight: 600, color: 'var(--text-primary)' }}>
                    {parseFloat(tx.value || '0').toFixed(4)} {tx.asset || 'ETH'}
                  </td>
                  <td style={{ padding: '10px 16px', color: 'var(--text-secondary)' }}>
                    {tx.timestamp ? new Date(tx.timestamp).toLocaleString() : 'Recent'}
                  </td>
                  <td style={{ padding: '10px 16px' }}>
                    <span className="apple-badge badge-clean">
                      {tx.status || 'Confirmed'}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
