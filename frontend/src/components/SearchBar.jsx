import React, { useState, useEffect, useRef } from 'react';
import { Search, X, Loader2, SlidersHorizontal, Settings, ChevronDown } from 'lucide-react';
import { detectChain } from '../api/client';

export const SearchBar = ({
  onSearch,
  loading,
  initialAddress = '',
  hops,
  setHops,
  minAmount,
  setMinAmount,
  direction,
  setDirection,
  onOpenSettings,
}) => {
  const [address, setAddress] = useState(initialAddress);
  const [detectedChain, setDetectedChain] = useState(null); // null when empty
  const [selectedChain, setSelectedChain] = useState(null); // null means Auto Detect, or 'ethereum' | 'bitcoin' | 'tron'
  const [showFilterDropdown, setShowFilterDropdown] = useState(false);
  const [showCurrencyDropdown, setShowCurrencyDropdown] = useState(false);
  const filterRef = useRef(null);
  const currencyRef = useRef(null);

  useEffect(() => {
    if (initialAddress) {
      setAddress(initialAddress);
    }
  }, [initialAddress]);

  // Fast auto-detection based on address format (only when address is present and not manually overridden)
  useEffect(() => {
    if (selectedChain && selectedChain !== 'auto') {
      setDetectedChain(selectedChain);
      return;
    }

    const trimmed = address.trim();
    if (!trimmed) {
      setDetectedChain(null);
      return;
    }

    if (trimmed.startsWith('0x') && trimmed.length >= 10) {
      setDetectedChain('ethereum');
    } else if (trimmed.startsWith('T') && trimmed.length >= 10) {
      setDetectedChain('tron');
    } else if (trimmed.startsWith('1') || trimmed.startsWith('3') || trimmed.startsWith('bc1')) {
      setDetectedChain('bitcoin');
    } else if (trimmed.length >= 32 && trimmed.length <= 44 && !trimmed.startsWith('0x')) {
      setDetectedChain('solana');
    } else {
      setDetectedChain('ethereum');
    }
  }, [address, selectedChain]);

  // Close dropdowns on click outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (filterRef.current && !filterRef.current.contains(e.target)) {
        setShowFilterDropdown(false);
      }
      if (currencyRef.current && !currencyRef.current.contains(e.target)) {
        setShowCurrencyDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);



  const handleSubmit = async (e) => {
    e?.preventDefault();
    const clean = address.trim();
    if (!clean) return;

    let chainToUse = selectedChain && selectedChain !== 'auto' ? selectedChain : detectedChain;
    if (!chainToUse) {
      try {
        const res = await detectChain(clean);
        if (res && (res.detectedChain || res.chain)) {
          chainToUse = res.detectedChain || res.chain;
          setDetectedChain(chainToUse);
        }
      } catch {}
    }
    chainToUse = chainToUse || 'ethereum';

    onSearch({
      address: clean,
      chain: chainToUse,
      hops,
      minAmount,
      direction,
    });
  };

  const handleClear = () => {
    setAddress('');
    setDetectedChain(null);
    setSelectedChain(null);
  };

  const activeChain = selectedChain && selectedChain !== 'auto' ? selectedChain : detectedChain;

  const getCurrencySymbol = () => {
    switch (activeChain) {
      case 'bitcoin': return 'BTC';
      case 'tron': return 'TRX';
      case 'solana': return 'SOL';
      default: return 'ETH';
    }
  };

  return (
    <div style={{ width: '100%', display: 'flex', alignItems: 'center', gap: 10 }}>
      {/* Search Bar Container */}
      <form
        onSubmit={handleSubmit}
        style={{
          flex: 1,
          display: 'flex',
          alignItems: 'center',
          background: 'var(--bg-card)',
          borderRadius: 'var(--radius-pill)',
          border: '1px solid var(--border-subtle)',
          boxShadow: 'var(--shadow-sm)',
          padding: '3px 4px 3px 6px',
          position: 'relative',
        }}
      >
        {/* Filter Option Button (Left to the search icon) */}
        <div ref={filterRef} style={{ position: 'relative' }}>
          <button
            type="button"
            onClick={() => setShowFilterDropdown((prev) => !prev)}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 4,
              padding: '4px 8px',
              borderRadius: 'var(--radius-pill)',
              background: showFilterDropdown ? 'var(--accent-soft)' : 'var(--bg-tag)',
              border: '1px solid var(--border-subtle)',
              color: showFilterDropdown ? 'var(--accent-primary)' : 'var(--text-secondary)',
              cursor: 'pointer',
              fontSize: 11,
              fontWeight: 500,
              transition: 'all 0.18s var(--ease-apple)',
              marginRight: 6,
            }}
            title="Configure hop depth & filter threshold"
          >
            <SlidersHorizontal size={11} />
            <span>{hops} {hops === 1 ? 'Hop' : 'Hops'}</span>
            <ChevronDown size={10} />
          </button>

          {/* Filter Dropdown Menu */}
          {showFilterDropdown && (
            <div
              style={{
                position: 'absolute',
                top: 'calc(100% + 8px)',
                left: 0,
                width: 270,
                background: 'var(--bg-card)',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-subtle)',
                boxShadow: 'var(--shadow-lg)',
                padding: '14px',
                zIndex: 100,
                backdropFilter: 'var(--blur-standard)',
                WebkitBackdropFilter: 'var(--blur-standard)',
                animation: 'fadeIn 0.18s var(--ease-apple)',
              }}
            >


              {/* Hop Depth Selection */}
              <div style={{ marginBottom: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10.5, marginBottom: 5 }}>
                  <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Traversal Hop Depth</span>
                  <span style={{ color: 'var(--accent-primary)', fontWeight: 600 }}>{hops} Hops</span>
                </div>
                <div style={{ display: 'flex', gap: 5 }}>
                  {[1, 2, 3, 4, 5].map((h) => (
                    <button
                      key={h}
                      type="button"
                      onClick={() => setHops(h)}
                      style={{
                        flex: 1,
                        padding: '4px 0',
                        borderRadius: 'var(--radius-xs)',
                        background: hops === h ? 'var(--accent-primary)' : 'var(--bg-tag)',
                        color: hops === h ? '#ffffff' : 'var(--text-primary)',
                        border: '1px solid var(--border-subtle)',
                        fontWeight: 600,
                        cursor: 'pointer',
                        fontSize: 11,
                        transition: 'all 0.15s ease',
                      }}
                    >
                      {h}
                    </button>
                  ))}
                </div>
              </div>

              {/* Transaction Amount Limit */}
              <div style={{ marginBottom: 12 }}>
                <div style={{ fontSize: 10.5, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 5 }}>
                  Min Transfer Limit ({getCurrencySymbol()})
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <input
                    type="number"
                    step="0.001"
                    min="0"
                    value={minAmount}
                    onChange={(e) => setMinAmount(e.target.value)}
                    placeholder="0.00"
                    style={{
                      flex: 1,
                      padding: '5px 8px',
                      borderRadius: 'var(--radius-xs)',
                      background: 'var(--bg-surface)',
                      border: '1px solid var(--border-subtle)',
                      fontSize: 11,
                      color: 'var(--text-primary)',
                      outline: 'none',
                    }}
                  />
                  <span style={{ fontSize: 10, color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>
                    {getCurrencySymbol()}
                  </span>
                </div>
                <span style={{ fontSize: 9.5, color: 'var(--text-tertiary)', marginTop: 3, display: 'block' }}>
                  Filters dust transactions below this value
                </span>
              </div>

              {/* Traversal Direction */}
              <div style={{ marginBottom: 12 }}>
                <div style={{ fontSize: 10.5, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 5 }}>
                  Tracing Direction
                </div>
                <div style={{ display: 'flex', gap: 5 }}>
                  {['both', 'outgoing', 'incoming'].map((dir) => (
                    <button
                      key={dir}
                      type="button"
                      onClick={() => setDirection(dir)}
                      style={{
                        flex: 1,
                        padding: '4px 0',
                        borderRadius: 'var(--radius-xs)',
                        background: direction === dir ? 'var(--accent-soft)' : 'var(--bg-tag)',
                        color: direction === dir ? 'var(--accent-primary)' : 'var(--text-secondary)',
                        border: direction === dir ? '1px solid var(--accent-primary)' : '1px solid var(--border-subtle)',
                        fontSize: 10,
                        textTransform: 'capitalize',
                        fontWeight: 500,
                        cursor: 'pointer',
                      }}
                    >
                      {dir}
                    </button>
                  ))}
                </div>
              </div>

              {/* Done Button */}
              <button
                type="button"
                onClick={() => setShowFilterDropdown(false)}
                className="apple-btn apple-btn-primary"
                style={{ width: '100%', padding: '5px 0', fontSize: 11 }}
              >
                Apply Filters
              </button>
            </div>
          )}
        </div>

        {/* Search Icon */}
        <Search size={14} color="var(--text-tertiary)" style={{ marginRight: 6, flexShrink: 0 }} />

        {/* Address Input */}
        <input
          type="text"
          value={address}
          onChange={(e) => setAddress(e.target.value)}
          placeholder="Enter ETH, BTC, or TRX wallet address..."
          style={{
            flex: 1,
            background: 'transparent',
            border: 'none',
            outline: 'none',
            fontSize: 12,
            color: 'var(--text-primary)',
            fontFamily: address ? 'ui-monospace, monospace' : 'inherit',
          }}
        />

        {/* Clear Button */}
        {address && (
          <button
            type="button"
            onClick={handleClear}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              color: 'var(--text-tertiary)',
              padding: 3,
              marginRight: 4,
              display: 'flex',
            }}
          >
            <X size={12} />
          </button>
        )}

        {/* Interactive Currency / Chain Selector Dropdown */}
        <div ref={currencyRef} style={{ position: 'relative' }}>
          <button
            type="button"
            onClick={() => setShowCurrencyDropdown((prev) => !prev)}
            style={{
              fontSize: 10,
              fontWeight: 600,
              textTransform: 'uppercase',
              letterSpacing: '0.03em',
              padding: '3px 8px',
              borderRadius: 'var(--radius-pill)',
              background: 'var(--bg-tag)',
              color: 'var(--text-secondary)',
              marginRight: 6,
              display: 'flex',
              alignItems: 'center',
              gap: 4,
              border: '1px solid var(--border-subtle)',
              cursor: 'pointer',
            }}
            title="Click to select or change cryptocurrency network"
          >
            <span
              style={{
                width: 6,
                height: 6,
                borderRadius: '50%',
                background:
                  activeChain === 'bitcoin'
                    ? '#f7931a'
                    : activeChain === 'tron'
                    ? '#eb0029'
                    : activeChain === 'solana'
                    ? '#14f195'
                    : activeChain === 'ethereum'
                    ? '#0071e3'
                    : '#8e8e93',
              }}
            />
            <span>
              {activeChain ? (activeChain === 'bitcoin' ? 'BTC' : activeChain === 'tron' ? 'TRX' : activeChain === 'solana' ? 'SOL' : 'ETH') : 'Auto Detect'}
            </span>
            <ChevronDown size={10} />
          </button>

          {showCurrencyDropdown && (
            <div
              style={{
                position: 'absolute',
                top: 'calc(100% + 8px)',
                right: 0,
                width: 175,
                background: 'var(--bg-card)',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-subtle)',
                boxShadow: 'var(--shadow-lg)',
                padding: '6px',
                zIndex: 100,
                backdropFilter: 'var(--blur-standard)',
                WebkitBackdropFilter: 'var(--blur-standard)',
                animation: 'fadeIn 0.18s var(--ease-apple)',
              }}
            >
              <div style={{ fontSize: 9.5, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', padding: '4px 6px', letterSpacing: '0.04em' }}>
                Select Currency
              </div>

              {[
                { id: 'auto', name: 'Auto Detect', symbol: 'AUTO', color: '#8e8e93' },
                { id: 'ethereum', name: 'Ethereum', symbol: 'ETH', color: '#0071e3' },
                { id: 'bitcoin', name: 'Bitcoin', symbol: 'BTC', color: '#f7931a' },
                { id: 'tron', name: 'TRON', symbol: 'TRX', color: '#eb0029' },
              ].map((item) => {
                const isCurrent = (!selectedChain && item.id === 'auto') || selectedChain === item.id;
                return (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => {
                      setSelectedChain(item.id === 'auto' ? null : item.id);
                      if (item.id !== 'auto') setDetectedChain(item.id);
                      setShowCurrencyDropdown(false);
                    }}
                    style={{
                      width: '100%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '5px 8px',
                      borderRadius: 'var(--radius-xs)',
                      background: isCurrent ? 'var(--accent-soft)' : 'transparent',
                      border: 'none',
                      color: isCurrent ? 'var(--accent-primary)' : 'var(--text-primary)',
                      fontSize: 11,
                      fontWeight: isCurrent ? 600 : 500,
                      cursor: 'pointer',
                      textAlign: 'left',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <span style={{ width: 6, height: 6, borderRadius: '50%', background: item.color }} />
                      <span>{item.name}</span>
                    </div>
                    <span style={{ fontSize: 9.5, fontWeight: 700, color: 'var(--text-tertiary)' }}>{item.symbol}</span>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Submit Trace Button */}
        <button
          type="submit"
          disabled={loading || !address.trim()}
          className="apple-btn apple-btn-primary"
          style={{
            borderRadius: 'var(--radius-pill)',
            padding: '5px 14px',
            fontSize: 12,
            opacity: !address.trim() ? 0.5 : 1,
          }}
        >
          {loading ? (
            <>
              <Loader2 size={12} style={{ animation: 'spin 1s linear infinite' }} />
              <span>Tracing...</span>
            </>
          ) : (
            <span>Trace</span>
          )}
        </button>
      </form>

      {/* Settings Icon Button (Left of Profile Pill) */}
      <button
        type="button"
        onClick={onOpenSettings}
        className="apple-icon-btn"
        style={{ width: 30, height: 30, borderRadius: '50%', flexShrink: 0 }}
        title="Settings & Appearance"
      >
        <Settings size={14} />
      </button>

      {/* Profile Pill (Rightmost) */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          background: 'var(--bg-card)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-pill)',
          padding: '3px 10px 3px 5px',
          boxShadow: 'var(--shadow-sm)',
          flexShrink: 0,
        }}
      >
        <div
          style={{
            width: 22,
            height: 22,
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #0071e3 0%, #2997ff 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#ffffff',
            fontSize: 9.5,
            fontWeight: 700,
          }}
        >
          LEA
        </div>
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-primary)', lineHeight: 1.1 }}>
            LEA-I4C-4092
          </span>
          <span style={{ fontSize: 8.5, color: '#34c759', fontWeight: 600, letterSpacing: '0.02em' }}>
            ONLINE
          </span>
        </div>
      </div>

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};
