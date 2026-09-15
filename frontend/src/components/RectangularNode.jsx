import React, { useState } from 'react';
import { Handle, Position } from '@xyflow/react';
import { Search, Copy, Check, Landmark, Loader2, Info, Clock, History } from 'lucide-react';

const getCurrencyMeta = (asset = 'ETH', chain = '', addr = '') => {
  const a = (asset || '').toUpperCase();
  const c = (chain || '').toLowerCase();
  if (a === 'BTC' || c === 'bitcoin' || addr.startsWith('1') || addr.startsWith('3') || addr.startsWith('bc1')) {
    return { symbol: 'BTC', name: 'Bitcoin', color: '#f7931a', bg: 'rgba(247, 147, 26, 0.12)', border: 'rgba(247, 147, 26, 0.35)' };
  }
  if (a === 'TRX' || c === 'tron' || addr.startsWith('T')) {
    return { symbol: 'TRX', name: 'TRON', color: '#eb0029', bg: 'rgba(235, 0, 41, 0.12)', border: 'rgba(235, 0, 41, 0.35)' };
  }
  if (a === 'SOL' || c === 'solana') {
    return { symbol: 'SOL', name: 'Solana', color: '#14f195', bg: 'rgba(20, 241, 149, 0.12)', border: 'rgba(20, 241, 149, 0.35)' };
  }
  return { symbol: 'ETH', name: 'Ethereum', color: '#627eea', bg: 'rgba(98, 126, 234, 0.12)', border: 'rgba(98, 126, 234, 0.35)' };
};

const formatCurrencyValue = (val, asset = 'ETH') => {
  if (val === null || val === undefined || val === '') return `0.000 ${asset}`;
  const num = parseFloat(String(val));
  if (isNaN(num)) return `0 ${asset}`;

  const cleanAsset = (asset || 'ETH').toUpperCase();
  if (cleanAsset === 'BTC') {
    if (num < 0.0001 && num > 0) return `${Math.round(num * 1e8).toLocaleString()} sat`;
    return `${num.toFixed(num < 0.05 ? 5 : 3)} BTC`;
  }
  if (cleanAsset === 'TRX') {
    return `${num.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 })} TRX`;
  }
  if (cleanAsset === 'SOL') {
    return `${num.toFixed(2)} SOL`;
  }
  return `${num.toFixed(num < 0.01 ? 4 : 2)} ${cleanAsset}`;
};

export const RectangularNode = ({ id, data, selected }) => {
  const [copied, setCopied] = useState(false);
  const [isExpanding, setIsExpanding] = useState(false);

  // Guarantee resolution of full untruncated address
  const fullAddr = data?.fullAddress || data?.address || (id && !id.includes('...') ? id : '') || '';
  const shortAddr = fullAddr && fullAddr.length > 10 
    ? `${fullAddr.slice(0, 5)}...${fullAddr.slice(-4)}` 
    : (fullAddr || data?.label || 'Unknown');

  const currMeta = getCurrencyMeta(data.asset, data.chain, fullAddr);
  const asset = currMeta.symbol;

  // Determine Node Role & Tagging
  const isSuspect = Boolean(
    data.isSuspect ||
    data.nodeType === 'suspect' ||
    data.type === 'suspect' ||
    data.role === 'suspect' ||
    (data.tags && data.tags.some((t) => typeof t === 'string' && /suspect/i.test(t)))
  );

  const isSearched =
    isSuspect ||
    data.isSearched ||
    data.nodeType === 'investigated' ||
    data.isTarget ||
    data.depth === 0 ||
    data.role === 'investigated';
  
  const isVasp = !isSearched && Boolean(
    data.nodeType === 'known_entity' ||
    data.isVasp === true ||
    (data.entityType && /exchange|vasp|custodial/i.test(data.entityType)) ||
    (data.tags && data.tags.some((t) => typeof t === 'string' && /vasp|exchange|coindcx|binance|wazirx|kraken|coinbase|bybit|kucoin/i.test(t))) ||
    (data.entityName && /exchange|vasp|coindcx|binance|wazirx|kraken|coinbase|bybit|kucoin/i.test(data.entityName))
  );

  const tags = data.tags || [];
  const isAppearedBefore = tags.some(t => /appeared in (your |.*)previous investigations/i.test(t));
  const isMultiInvestigator = tags.some(t => /searched by \d+ investigators before/i.test(t));
  const isTaggedCrossCase = isAppearedBefore || isMultiInvestigator;

  const riskScore = data.riskScore ?? 0;
  const riskLevel = (data.riskLevel || (riskScore >= 75 ? 'CRITICAL' : riskScore >= 50 ? 'HIGH' : riskScore >= 20 ? 'MEDIUM' : 'LOW')).toUpperCase();

  // Whole Node Coloring (For Tagging Only, Not for Suspicion):
  // - VASP: Whole node has gold background (#eab308)
  // - Target Root / Suspect Wallet: Whole node has blue background (#0071e3)
  // - Cross-Case Tagged: Whole node has forensic purple background (#af52de)
  // - Standard Peers: Clean card background (suspicion stays on risk badge)
  let nodeBg = 'var(--bg-card)';
  let borderStyle = '1px solid var(--border-subtle)';
  let glowStyle = 'none';
  let themeColor = '#34c759';

  if (isVasp) {
    nodeBg = 'linear-gradient(145deg, rgba(234, 179, 8, 0.22) 0%, rgba(202, 138, 4, 0.12) 100%)';
    borderStyle = '1.5px solid #eab308';
    glowStyle = '0 0 10px rgba(234, 179, 8, 0.25)';
    themeColor = '#eab308';
  } else if (isSearched) {
    nodeBg = 'linear-gradient(145deg, rgba(0, 113, 227, 0.18) 0%, rgba(0, 113, 227, 0.08) 100%)';
    borderStyle = '1.5px solid #0071e3';
    glowStyle = '0 0 10px rgba(0, 113, 227, 0.25)';
    themeColor = '#0071e3';
  } else if (isTaggedCrossCase) {
    nodeBg = 'linear-gradient(145deg, rgba(175, 82, 222, 0.18) 0%, rgba(175, 82, 222, 0.08) 100%)';
    borderStyle = '1.5px solid #af52de';
    glowStyle = '0 0 10px rgba(175, 82, 222, 0.25)';
    themeColor = '#af52de';
  } else {
    nodeBg = 'var(--bg-card)';
    borderStyle = '1px solid var(--border-subtle)';
    themeColor = riskScore >= 75 ? '#af52de' : riskScore >= 50 ? '#ff453a' : riskScore >= 20 ? '#ff9f0a' : '#34c759';
  }

  const title = data.entityName || data.name || (isSuspect && data.depth !== 0 ? 'Suspect Wallet' : isSearched ? 'Target Wallet' : isVasp ? 'Verified VASP' : shortAddr);
  
  // Robust Volume Calculation: fallback across all possible keys so volume is never 0
  let balanceRaw = data.balance ?? data.balanceEth ?? data.totalTransferred ?? data.totalAmount ?? data.totalVolume ?? '0';
  if ((balanceRaw === '0' || balanceRaw === 0 || !balanceRaw) && data.totalReceivedFromParent && data.totalReceivedFromParent !== '0') {
    balanceRaw = data.totalReceivedFromParent;
  }
  if ((balanceRaw === '0' || balanceRaw === 0 || !balanceRaw) && data.totalSent && data.totalSent !== '0') {
    balanceRaw = data.totalSent;
  }

  const txCount = data.txCount ?? data.transactionCount ?? 0;

  // Timestamp extraction and formatting
  const rawTime = data.timestamp || data.lastSeen || data.firstSeen || null;
  const formatTime = (ts) => {
    if (!ts) return null;
    try {
      const d = new Date(ts);
      if (isNaN(d.getTime())) return null;
      return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' }) + ', ' +
        d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit', hour12: false });
    } catch {
      return null;
    }
  };
  const formattedTime = formatTime(rawTime);

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

    if (data?.onTrack) {
      setIsExpanding(true);
      // Safety fallback: guaranteed reset after 10s to eliminate stuck loading state
      const safetyTimer = setTimeout(() => {
        setIsExpanding(false);
      }, 10000);

      const payload = {
        ...data,
        id: id || fullAddr,
        address: fullAddr,
        fullAddress: fullAddr,
      };

      data.onTrack(payload, () => {
        clearTimeout(safetyTimer);
        setIsExpanding(false);
      });
    }
  };

  const handleOpenDetail = (e) => {
    if (e) e.stopPropagation();
    if (data?.onOpen) {
      data.onOpen({
        ...data,
        id: id || fullAddr,
        address: fullAddr,
        fullAddress: fullAddr,
        asset,
        currencyMeta: currMeta,
      });
    }
  };

  return (
    <div 
      className={`custom-rect-node ${selected ? 'selected' : ''}`}
      onDoubleClick={handleOpenDetail}
      style={{
        width: 218,
        minWidth: 218,
        maxWidth: 218,
        background: nodeBg,
        border: selected ? `2px solid ${themeColor}` : borderStyle,
        boxShadow: selected ? `0 0 14px ${themeColor}50, var(--shadow-md)` : glowStyle,
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
          <span className="node-title" title={title} style={{ color: isSearched ? '#0071e3' : isVasp ? '#ca8a04' : isTaggedCrossCase ? '#af52de' : 'var(--text-primary)' }}>
            {title}
          </span>
          <span
            style={{
              fontSize: 8.5,
              fontWeight: 700,
              padding: '1px 4px',
              borderRadius: 3,
              color: currMeta.color,
              background: currMeta.bg,
              border: `1px solid ${currMeta.border}`,
              letterSpacing: '0.02em',
              flexShrink: 0,
            }}
            title={`${currMeta.name} Network Asset`}
          >
            {currMeta.symbol}
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

      {/* Timestamp Line (Transaction Time) */}
      {formattedTime && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 3.5, fontSize: 8.5, color: 'var(--text-tertiary)', margin: '1px 0 3px', fontFamily: 'ui-monospace, monospace' }}>
          <Clock size={8} />
          <span>{formattedTime}</span>
        </div>
      )}

      {/* Badges */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', margin: '3px 0', gap: 4, flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 3 }}>
          {isSearched ? (
            <span className="apple-badge" style={{ background: 'rgba(0, 113, 227, 0.16)', color: '#0071e3', fontWeight: 600 }}>
              {isSuspect && data.depth !== 0 ? 'Suspect Wallet' : 'Target Root'}
            </span>
          ) : isVasp ? (
            <span className="apple-badge" style={{ background: 'rgba(234, 179, 8, 0.22)', color: '#b45309', display: 'inline-flex', alignItems: 'center', gap: 3, fontWeight: 700 }}>
              <Landmark size={8.5} />
              VASP
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

          {isAppearedBefore && (
            <span className="apple-badge" style={{ background: 'rgba(175, 82, 222, 0.18)', color: '#af52de', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: 2 }} title="This wallet appeared in your previous investigations">
              <History size={7.5} />
              Prior Case
            </span>
          )}
          {isMultiInvestigator && !isAppearedBefore && (
            <span className="apple-badge" style={{ background: 'rgba(175, 82, 222, 0.18)', color: '#af52de', fontWeight: 600 }} title="Searched by multiple investigators before">
              Multi-LEA
            </span>
          )}
        </div>

        {data.depth !== undefined && (
          <span style={{ fontSize: 8.5, color: 'var(--text-tertiary)', fontWeight: 500 }}>
            Hop {data.depth}
          </span>
        )}
      </div>

      {/* Metadata Grid */}
      <div className="node-meta-grid">
        <div>
          <div className="meta-item-label" style={{ display: 'flex', alignItems: 'center', gap: 3 }}>
            <span style={{ width: 4, height: 4, borderRadius: '50%', background: currMeta.color }} />
            Amount / Vol
          </div>
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
