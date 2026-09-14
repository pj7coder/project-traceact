import React from 'react';
import { X, Sun, Moon, Shield, Server, User, Sliders, CheckCircle2 } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';

export const SettingsModal = ({ isOpen, onClose, defaultHops, setDefaultHops, dustFilter, setDustFilter }) => {
  const { theme, toggleTheme, setTheme } = useTheme();

  if (!isOpen) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" style={{ maxWidth: 540 }} onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div
              style={{
                width: 32,
                height: 32,
                borderRadius: 'var(--radius-sm)',
                background: 'linear-gradient(135deg, #0071e3 0%, #2997ff 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#ffffff',
              }}
            >
              <Sliders size={17} />
            </div>
            <div>
              <h3 style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)' }}>
                Workstation Settings
              </h3>
              <p style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
                Interface appearance, investigator credentials & engine calibration
              </p>
            </div>
          </div>

          <button className="apple-icon-btn" onClick={onClose}>
            <X size={16} />
          </button>
        </div>

        {/* Section 1: Appearance (Light & Dark Theme) */}
        <div style={{ marginBottom: 20 }}>
          <div style={{ fontSize: 11, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: 8 }}>
            Appearance Theme
          </div>

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              background: 'var(--bg-tag)',
              padding: 4,
              borderRadius: 'var(--radius-pill)',
              border: '1px solid var(--border-subtle)',
            }}
          >
            <button
              type="button"
              onClick={() => setTheme('light')}
              style={{
                flex: 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 8,
                padding: '8px 0',
                borderRadius: 'var(--radius-pill)',
                background: theme === 'light' ? 'var(--bg-surface-elevated)' : 'transparent',
                color: theme === 'light' ? 'var(--text-primary)' : 'var(--text-tertiary)',
                boxShadow: theme === 'light' ? 'var(--shadow-sm)' : 'none',
                border: 'none',
                cursor: 'pointer',
                fontSize: 13,
                fontWeight: 500,
                transition: 'all 0.2s var(--ease-apple)',
              }}
            >
              <Sun size={15} />
              Light Theme
            </button>
            <button
              type="button"
              onClick={() => setTheme('dark')}
              style={{
                flex: 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 8,
                padding: '8px 0',
                borderRadius: 'var(--radius-pill)',
                background: theme === 'dark' ? 'var(--bg-surface-elevated)' : 'transparent',
                color: theme === 'dark' ? 'var(--text-primary)' : 'var(--text-tertiary)',
                boxShadow: theme === 'dark' ? 'var(--shadow-sm)' : 'none',
                border: 'none',
                cursor: 'pointer',
                fontSize: 13,
                fontWeight: 500,
                transition: 'all 0.2s var(--ease-apple)',
              }}
            >
              <Moon size={15} />
              Dark Theme
            </button>
          </div>
        </div>

        {/* Section 2: Investigator Identity */}
        <div style={{ marginBottom: 20 }}>
          <div style={{ fontSize: 11, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: 8 }}>
            Investigator Identity & Jurisdiction
          </div>

          <div
            style={{
              background: 'var(--bg-tag)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-subtle)',
              padding: '12px 14px',
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: 10,
              fontSize: 12,
            }}
          >
            <div>
              <span style={{ color: 'var(--text-tertiary)', fontSize: 10 }}>INVESTIGATOR ID:</span>
              <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>LEA-I4C-4092</div>
            </div>
            <div>
              <span style={{ color: 'var(--text-tertiary)', fontSize: 10 }}>DESIGNATION:</span>
              <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Cyber Forensics Officer</div>
            </div>
            <div>
              <span style={{ color: 'var(--text-tertiary)', fontSize: 10 }}>AGENCY:</span>
              <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>I4C / SAHYOG Ecosystem</div>
            </div>
            <div>
              <span style={{ color: 'var(--text-tertiary)', fontSize: 10 }}>STATUTORY POWERS:</span>
              <div style={{ fontWeight: 600, color: 'var(--accent-primary)' }}>Sec 91 CrPC Authorized</div>
            </div>
          </div>
        </div>

        {/* Section 3: Engine Calibration */}
        <div style={{ marginBottom: 20 }}>
          <div style={{ fontSize: 11, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: 8 }}>
            Default Traversal & Filter Parameters
          </div>

          <div
            style={{
              background: 'var(--bg-tag)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-subtle)',
              padding: '14px',
              display: 'flex',
              flexDirection: 'column',
              gap: 12,
            }}
          >
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 6 }}>
                <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>Default Hop Depth</span>
                <span style={{ fontWeight: 600, color: 'var(--accent-primary)' }}>{defaultHops} Hops</span>
              </div>
              <div style={{ display: 'flex', gap: 6 }}>
                {[1, 2, 3, 4, 5].map((h) => (
                  <button
                    key={h}
                    type="button"
                    onClick={() => setDefaultHops(h)}
                    style={{
                      flex: 1,
                      padding: '6px 0',
                      borderRadius: 'var(--radius-xs)',
                      background: defaultHops === h ? 'var(--accent-primary)' : 'var(--bg-card)',
                      color: defaultHops === h ? '#ffffff' : 'var(--text-primary)',
                      border: '1px solid var(--border-subtle)',
                      fontWeight: 600,
                      cursor: 'pointer',
                      fontSize: 12,
                    }}
                  >
                    {h}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 6 }}>
                <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>Dust Filter Threshold</span>
                <span style={{ fontWeight: 600, color: 'var(--accent-primary)' }}>{dustFilter} ETH/BTC</span>
              </div>
              <input
                type="text"
                value={dustFilter}
                onChange={(e) => setDustFilter(e.target.value)}
                placeholder="0.0"
                style={{
                  width: '100%',
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-xs)',
                  padding: '7px 10px',
                  fontSize: 12,
                  color: 'var(--text-primary)',
                  outline: 'none',
                }}
              />
            </div>
          </div>
        </div>

        {/* Section 4: Backend Service Status */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '10px 14px',
            borderRadius: 'var(--radius-sm)',
            background: 'var(--bg-card)',
            border: '1px solid var(--border-subtle)',
            fontSize: 11,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Server size={14} color="#34c759" />
            <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>FastAPI Backend: 8001</span>
          </div>
          <span className="apple-badge badge-clean">Active</span>
        </div>
      </div>
    </div>
  );
};
