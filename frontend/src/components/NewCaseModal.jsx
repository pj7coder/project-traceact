import React, { useState } from 'react';
import { X, PlusCircle, Shield, GitFork, Compass } from 'lucide-react';

export const NewCaseModal = ({ isOpen, onClose, onLaunch }) => {
  if (!isOpen) return null;

  const [address, setAddress] = useState('');
  const [chain, setChain] = useState('ethereum');
  const [caseNumber, setCaseNumber] = useState(`FIR-2026/CYBER-${Math.floor(100 + Math.random() * 900)}`);
  const [crimeType, setCrimeType] = useState('Cryptocurrency Investment Fraud / Peeling');
  const [hops, setHops] = useState(2);
  const [direction, setDirection] = useState('both');
  const [minAmount, setMinAmount] = useState('0.0');

  const handleAddressChange = (e) => {
    const val = e.target.value.trim();
    setAddress(val);

    // Smart chain auto-detection
    if (val.startsWith('0x') && val.length >= 10) {
      setChain('ethereum');
    } else if (val.startsWith('T') && val.length >= 10) {
      setChain('tron');
    } else if (val.startsWith('1') || val.startsWith('3') || val.toLowerCase().startsWith('bc1')) {
      setChain('bitcoin');
    } else if (val.length >= 32 && val.length <= 44 && !val.startsWith('0x')) {
      setChain('solana');
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!address.trim()) return;

    onLaunch({
      address: address.trim(),
      chain,
      caseNumber,
      crimeType,
      hops: Number(hops),
      direction,
      minAmount,
    });
    onClose();
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 480 }}>
        {/* Modal Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div
              style={{
                width: 30,
                height: 30,
                borderRadius: 'var(--radius-xs)',
                background: 'linear-gradient(135deg, #0071e3 0%, #2997ff 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#ffffff',
              }}
            >
              <PlusCircle size={17} />
            </div>
            <div>
              <h3 style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>
                Start New Investigation Docket
              </h3>
              <p style={{ fontSize: 10.5, color: 'var(--text-secondary)' }}>
                Initialize suspect wallet tracing, graph building, and case dossier
              </p>
            </div>
          </div>
          <button onClick={onClose} className="apple-icon-btn" style={{ width: 24, height: 24 }}>
            <X size={13} />
          </button>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {/* Suspect Wallet Address */}
          <div>
            <label style={{ fontSize: 10.5, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>
              Target Suspect Address *
            </label>
            <input
              type="text"
              required
              placeholder="0x... or 1... / bc1... or T..."
              value={address}
              onChange={handleAddressChange}
              style={{
                width: '100%',
                padding: '8px 10px',
                borderRadius: 'var(--radius-xs)',
                border: '1px solid var(--border-subtle)',
                background: 'var(--bg-surface)',
                color: 'var(--text-primary)',
                fontFamily: 'ui-monospace, monospace',
                fontSize: 12,
                marginTop: 3,
                outline: 'none',
              }}
            />
          </div>

          {/* Grid: Blockchain Network & Crime Type */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            <div>
              <label style={{ fontSize: 10.5, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>
                Blockchain Network
              </label>
              <select
                value={chain}
                onChange={(e) => setChain(e.target.value)}
                style={{
                  width: '100%',
                  padding: '7px 10px',
                  borderRadius: 'var(--radius-xs)',
                  border: '1px solid var(--border-subtle)',
                  background: 'var(--bg-surface)',
                  color: 'var(--text-primary)',
                  fontSize: 11.5,
                  marginTop: 3,
                  outline: 'none',
                }}
              >
                <option value="ethereum">Ethereum (ETH)</option>
                <option value="bitcoin">Bitcoin (BTC)</option>
                <option value="tron">TRON (TRX)</option>
                <option value="solana">Solana (SOL)</option>
              </select>
            </div>

            <div>
              <label style={{ fontSize: 10.5, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>
                Crime Classification
              </label>
              <select
                value={crimeType}
                onChange={(e) => setCrimeType(e.target.value)}
                style={{
                  width: '100%',
                  padding: '7px 10px',
                  borderRadius: 'var(--radius-xs)',
                  border: '1px solid var(--border-subtle)',
                  background: 'var(--bg-surface)',
                  color: 'var(--text-primary)',
                  fontSize: 11.5,
                  marginTop: 3,
                  outline: 'none',
                }}
              >
                <option value="Cryptocurrency Investment Fraud / Peeling">Investment Fraud</option>
                <option value="Ransomware Extortion Payment">Ransomware</option>
                <option value="Pig Butchering / High-Yield Scam">Pig Butchering</option>
                <option value="Phishing / Drainer Contract">Phishing Drainer</option>
                <option value="AML Evasion & Mixing">AML Evasion</option>
              </select>
            </div>
          </div>

          {/* FIR Ref & Traversal Depth */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            <div>
              <label style={{ fontSize: 10.5, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>
                FIR / Requisition Reference #
              </label>
              <input
                type="text"
                value={caseNumber}
                onChange={(e) => setCaseNumber(e.target.value)}
                style={{
                  width: '100%',
                  padding: '7px 10px',
                  borderRadius: 'var(--radius-xs)',
                  border: '1px solid var(--border-subtle)',
                  background: 'var(--bg-surface)',
                  color: 'var(--text-primary)',
                  fontSize: 12,
                  marginTop: 3,
                  outline: 'none',
                }}
              />
            </div>

            <div>
              <label style={{ fontSize: 10.5, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>
                Tracing Depth (Hops)
              </label>
              <select
                value={hops}
                onChange={(e) => setHops(Number(e.target.value))}
                style={{
                  width: '100%',
                  padding: '7px 10px',
                  borderRadius: 'var(--radius-xs)',
                  border: '1px solid var(--border-subtle)',
                  background: 'var(--bg-surface)',
                  color: 'var(--text-primary)',
                  fontSize: 11.5,
                  marginTop: 3,
                  outline: 'none',
                }}
              >
                <option value={1}>1 Hop (Direct Counterparties)</option>
                <option value={2}>2 Hops (Standard Intermediaries)</option>
                <option value={3}>3 Hops (Layering Chains)</option>
                <option value={4}>4 Hops (Deep Cluster Analysis)</option>
                <option value={5}>5 Hops (Maximum Forensic Depth)</option>
              </select>
            </div>
          </div>

          {/* Sample quick picks */}
          <div>
            <span style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>Sample Target Addresses:</span>
            <div style={{ display: 'flex', gap: 6, marginTop: 4, flexWrap: 'wrap' }}>
              <button
                type="button"
                className="apple-btn apple-btn-secondary"
                style={{ padding: '3px 8px', fontSize: 10 }}
                onClick={() => {
                  setAddress('0x71c836489b990038848971201991802901238910');
                  setChain('ethereum');
                }}
              >
                0x71c8... (CoinDCX Demo)
              </button>
              <button
                type="button"
                className="apple-btn apple-btn-secondary"
                style={{ padding: '3px 8px', fontSize: 10 }}
                onClick={() => {
                  setAddress('0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045');
                  setChain('ethereum');
                }}
              >
                Vitalik ETH
              </button>
              <button
                type="button"
                className="apple-btn apple-btn-secondary"
                style={{ padding: '3px 8px', fontSize: 10 }}
                onClick={() => {
                  setAddress('TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t');
                  setChain('tron');
                }}
              >
                Tron USDT
              </button>
            </div>
          </div>

          {/* Footer Actions */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 10 }}>
            <button type="button" className="apple-btn apple-btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button
              type="submit"
              className="apple-btn apple-btn-primary"
              style={{
                background: 'linear-gradient(135deg, #0071e3 0%, #2997ff 100%)',
                fontWeight: 600,
              }}
            >
              <PlusCircle size={14} />
              <span>Launch & Trace Case</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
