import React, { useState } from 'react';
import { Handle, Position } from '@xyflow/react';
import { Search, Copy, Check, Landmark, Loader2, Info } from 'lucide-react';

const formatCurrencyValue = (val, asset = 'ETH') => {
  if (val === null || val === undefined || val === '') return `0.000 ${asset}`;
  const num = parseFloat(String(val));
  if (isNaN(num)) return `0 ${asset}`;

  const cleanAsset = (asset || 'ETH').toUpperCase();
  if (cleanAsset === 'BTC') {
    return `${num.toFixed(num < 0.01 ? 5 : 3)} BTC`;
  }
  if (cleanAsset === 'TRX') {
    return `${num.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 2 })} TRX`;
  }
  if (cleanAsset === 'SOL') {
    return `${num.toFixed(2)} SOL`;
  }
  return `${num.toFixed(num < 0.1 ? 3 : 2)} ${cleanAsset}`;
};

export const RectangularNode = ({ data, selected }) => {
  const [copied, setCopied] = useState(false);
  const [isExpanding, setIsExpanding] = useState(false);

  const fullAddr = data.fullAddress || data.address || data.label || '';
  const shortAddr = fullAddr.length > 10 
    ? `${fullAddr.slice(0, 5)}...${fullAddr.slice(-4)}` 
    : fullAddr;

  // Determine Node Role & Type
  const isSearched = data.nodeType === 'investigated' || data.isTarget || data.depth === 0 || data.role === 'investigated';
  
  const isVasp = !isSearched && Boolean(
    data.nodeType === 'known_entity' ||
    data.isVasp === true ||
    (data.entityType && /exchange|vasp|custodial/i.test(data.entityType)) ||
    (data.tags && data.tags.some(t => /vasp|exchange|coindcx|binance|wazirx|kraken|coinbase|bybit|kucoin/i.test(t))) ||
    (data.entityName && /exchange|vasp|coindcx|binance|wazirx|kraken|coinbase|bybit|kucoin/i.test(data.entityName))
  );

  const riskScore = data.riskScore ?? 0;
  const riskLevel = (data.riskLevel || (riskScore >= 75 ? 'CRITICAL' : riskScore >= 50 ? 'HIGH' : riskScore >= 20 ? 'MEDIUM' : 'LOW')).toUpperCase();

  // Color Mapping:
  // - Searched Target: Blue (#0071e3)
  // - VASP: Gold (#eab308)
  // - Counterparties: Suspicion Engine Score
  let themeColor = '#34c759';
  let borderStyle = '1px solid var(--border-subtle)';
  let glowStyle = 'none';

  if (isSearched) {
    themeColor = '#0071e3';
    borderStyle = '1.5px solid #0071e3';
    glowStyle = '0 0 8px rgba(0, 113, 227, 0.25)';
  } else if (isVasp) {
    themeColor = '#eab308';
    borderStyle = '1.5px solid #eab308';
    glowStyle = '0 0 8px rgba(234, 179, 8, 0.25)';
  } else {
    if (riskScore >= 75 || riskLevel === 'CRITICAL') {
      themeColor = '#af52de';
      borderStyle = '1px solid rgba(175, 82, 222, 0.45)';
    } else if (riskScore >= 50 || riskLevel === 'HIGH') {
      themeColor = '#ff453a';
      borderStyle = '1px solid rgba(255, 69, 58, 0.4)';
    } else if (riskScore >= 20 || riskLevel === 'MEDIUM') {
      themeColor = '#ff9f0a';
      borderStyle = '1px solid rgba(255, 159, 10, 0.35)';
    } else {
      themeColor = '#34c759';
      borderStyle = '1px solid rgba(52, 199, 89, 0.3)';
    }
  }

  const title = data.entityName || data.name || (isSearched ? 'Target Wallet' : isVasp ? 'Verified VASP' : shortAddr);
  const balanceRaw = data.balance || data.totalTransferred || data.totalAmount || data.totalVolume || '0';
  const asset = (data.asset || 'ETH').toUpperCase();
  const txCount = data.txCount ?? data.transactionCount ?? 0;

  const handleCopy = (e) => {
    e.stopPropagation();
    if (fullAddr) {
      navigator.clipboard.writeText(fullAddr);
      setCopied(true);
      setTimeout(() => setCopied(false), 1400);
    }
  };

  const handleTrackClick = (e) => {
    e.stopPropagation();
    if (isExpanding) return;

    if (data.onTrack) {
      setIsExpanding(true);
      // Pass done callback to stop spinner
      data.onTrack(data, () => {
        setIsExpanding(false);
      });
    }
  };

  const handleOpenDetail = (e) => {
    if (e) e.stopPropagation();
    if (data.onOpen) {
      data.onOpen(data);
    }
  };

  return (
    <div 
      className={`custom-rect-node ${selected ? 'selected' : ''}`}
      onDoubleClick={handleOpenDetail}
      style={{
        width: 210,
        minWidth: 210,
        maxWidth: 210,
        border: selected ? `2px solid ${themeColor}` : borderStyle,
        boxShadow: selected ? `0 0 12px ${themeColor}40, var(--shadow-md)` : glowStyle,
      }}
      title="Click to highlight Inflow (Green) / Outflow (Red) · Double-click for full dossier"
    >
      {/* Explicit Multi-Level Left and Right Handles to Eliminate Edge Collisions */}
      <Handle type="target" position={Position.Left} id="left-top" style={{ top: '25%', background: themeColor, width: 5, height: 5, left: -3, border: '1px solid var(--bg-card)' }} />
      <Handle type="source" position={Position.Left} id="left-top-src" style={{ top: '25%', background: themeColor, width: 5, height: 5, left: -3, border: '1px solid var(--bg-card)' }} />
      
      <Handle type="target" position={Position.Left} id="left" style={{ top: '50%', background: themeColor, width: 5, height: 5, left: -3, border: '1px solid var(--bg-card)' }} />
      <Handle type="source" position={Position.Left} id="left-src" style={{ top: '50%', background: themeColor, width: 5, height: 5, left: -3, border: '1px solid var(--bg-card)' }} />
      
      <Handle type="target" position={Position.Left} id="left-bottom" style={{ top: '75%', background: themeColor, width: 5, height: 5, left: -3, border: '1px solid var(--bg-card)' }} />
      <Handle type="source" position={Position.Left} id="left-bottom-src" style={{ top: '75%', background: themeColor, width: 5, height: 5, left: -3, border: '1px solid var(--bg-card)' }} />

      <Handle type="source" position={Position.Right} id="right-top" style={{ top: '25%', background: themeColor, width: 5, height: 5, right: -3, border: '1px solid var(--bg-card)' }} />
      <Handle type="target" position={Position.Right} id="right-top-tgt" style={{ top: '25%', background: themeColor, width: 5, height: 5, right: -3, border: '1px solid var(--bg-card)' }} />
      
      <Handle type="source" position={Position.Right} id="right" style={{ top: '50%', background: themeColor, width: 5, height: 5, right: -3, border: '1px solid var(--bg-card)' }} />
      <Handle type="target" position={Position.Right} id="right-tgt" style={{ top: '50%', background: themeColor, width: 5, height: 5, right: -3, border: '1px solid var(--bg-card)' }} />
      
      <Handle type="source" position={Position.Right} id="right-bottom" style={{ top: '75%', background: themeColor, width: 5, height: 5, right: -3, border: '1px solid var(--bg-card)' }} />
      <Handle type="target" position={Position.Right} id="right-bottom-tgt" style={{ top: '75%', background: themeColor, width: 5, height: 5, right: -3, border: '1px solid var(--bg-card)' }} />

      {/* Top and Bottom Handles for Radial & Matrix Layouts */}
      <Handle type="target" position={Position.Top} id="top" style={{ left: '50%', background: themeColor, width: 5, height: 5, top: -3, border: '1px solid var(--bg-card)' }} />
      <Handle type="source" position={Position.Top} id="top-src" style={{ left: '50%', background: themeColor, width: 5, height: 5, top: -3, border: '1px solid var(--bg-card)' }} />
      
      <Handle type="target" position={Position.Bottom} id="bottom" style={{ left: '50%', background: themeColor, width: 5, height: 5, bottom: -3, border: '1px solid var(--bg-card)' }} />
      <Handle type="source" position={Position.Bottom} id="bottom-src" style={{ left: '50%', background: themeColor, width: 5, height: 5, bottom: -3, border: '1px solid var(--bg-card)' }} />

      {/* Header */}
      <div className="node-header">
        <div className="node-title-wrap">
          <span 
            style={{
              width: 6,
              height: 6,
              borderRadius: '50%',
              backgroundColor: themeColor,
              boxShadow: `0 0 4px ${themeColor}`,
              flexShrink: 0,
            }} 
          />
          <span className="node-title" title={title} style={{ color: isSearched ? '#0071e3' : isVasp ? '#eab308' : 'var(--text-primary)' }}>
            {title}
          </span>
        </div>

        {/* Action buttons: Dossier info and 2-Hop Track */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 3 }}>
          <button
            className="node-track-btn"
            onClick={handleOpenDetail}
            title="View full wallet dossier"
            style={{
              color: 'var(--text-secondary)',
              borderColor: 'var(--border-subtle)',
            }}
          >
            <Info size={9.5} />
          </button>

          <button
            className="node-track-btn"
            onClick={handleTrackClick}
            disabled={isExpanding}
            title={isExpanding ? "Expanding 2 hops..." : `Expand 2 hops from ${shortAddr}`}
            style={{
              color: themeColor,
              borderColor: isVasp ? 'rgba(234, 179, 8, 0.35)' : isSearched ? 'rgba(0, 113, 227, 0.35)' : 'var(--border-subtle)',
              cursor: isExpanding ? 'wait' : 'pointer',
            }}
          >
            {isExpanding ? (
              <Loader2 size={10} style={{ animation: 'spin 0.8s linear infinite' }} />
            ) : (
              <Search size={9.5} strokeWidth={2.4} />
            )}
          </button>
        </div>
      </div>

      {/* Address Line */}
      <div className="node-address">
        <span>{shortAddr}</span>
        <button
          onClick={handleCopy}
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            padding: 1,
            color: 'inherit',
            display: 'flex',
            alignItems: 'center',
          }}
          title="Copy address"
        >
          {copied ? <Check size={9} color="#34c759" /> : <Copy size={9} />}
        </button>
      </div>

      {/* Badges */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', margin: '3px 0' }}>
        {isSearched ? (
          <span className="apple-badge" style={{ background: 'rgba(0, 113, 227, 0.12)', color: '#0071e3' }}>
            Target Root
          </span>
        ) : isVasp ? (
          <span className="apple-badge" style={{ background: 'rgba(234, 179, 8, 0.15)', color: '#ca8a04', display: 'inline-flex', alignItems: 'center', gap: 3 }}>
            <Landmark size={8.5} />
            Verified VASP
          </span>
        ) : (
          <span 
            className="apple-badge" 
            style={{
              background: `rgba(${themeColor === '#af52de' ? '175, 82, 222' : themeColor === '#ff453a' ? '255, 69, 58' : themeColor === '#ff9f0a' ? '255, 159, 10' : '52, 199, 89'}, 0.14)`,
              color: themeColor,
            }}
          >
            {riskLevel} ({riskScore})
          </span>
        )}

        {data.depth !== undefined && (
          <span style={{ fontSize: 8.5, color: 'var(--text-tertiary)', fontWeight: 500 }}>
            Hop {data.depth}
          </span>
        )}
      </div>

      {/* Metadata Grid */}
      <div className="node-meta-grid">
        <div>
          <div className="meta-item-label">Amount / Vol</div>
          <div className="meta-item-value" title={`${balanceRaw} ${asset}`}>
            {formatCurrencyValue(balanceRaw, asset)}
          </div>
        </div>
        <div>
          <div className="meta-item-label">Operations</div>
          <div className="meta-item-value">
            {txCount} txs
          </div>
        </div>
      </div>
    </div>
  );
};
