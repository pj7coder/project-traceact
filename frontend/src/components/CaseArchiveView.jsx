import React, { useState, useEffect } from 'react';
import {
  Folder,
  FolderOpen,
  Search,
  Trash2,
  FileText,
  Clock,
  Shield,
  AlertTriangle,
  ArrowRight,
  ExternalLink,
  Tag,
  PlusCircle,
  Database,
  Building,
} from 'lucide-react';
import { getSavedInvestigations, deleteInvestigationCase } from '../api/client';

export const CaseArchiveView = ({ onOpenCase, onStartNewCase, showToast }) => {
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterChain, setFilterChain] = useState('all');

  const loadCases = async () => {
    setLoading(true);
    try {
      const saved = await getSavedInvestigations();
      setCases(saved || []);
    } catch (err) {
      console.error('Failed to load saved cases:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCases();
  }, []);

  const handleDelete = async (e, caseId) => {
    e.stopPropagation();
    if (!window.confirm(`Are you sure you want to permanently delete investigation case ${caseId}?`)) {
      return;
    }

    try {
      await deleteInvestigationCase(caseId);
      setCases((prev) => prev.filter((c) => c.caseId !== caseId));
      if (showToast) showToast(`Case ${caseId} deleted from database archive.`);
    } catch (err) {
      console.error('Failed to delete case:', err);
      if (showToast) showToast('Error deleting case from database.');
    }
  };

  const filteredCases = cases.filter((c) => {
    const q = searchQuery.toLowerCase().trim();
    const chainMatch = filterChain === 'all' || (c.chain || 'ethereum').toLowerCase() === filterChain.toLowerCase();
    if (!chainMatch) return false;

    if (!q) return true;
    const title = (c.title || '').toLowerCase();
    const caseId = (c.caseId || '').toLowerCase();
    const target = (c.targetAddress || c.wallet?.address || '').toLowerCase();
    const fir = (c.caseNumber || '').toLowerCase();
    const crime = (c.crimeType || '').toLowerCase();
    const tags = Array.isArray(c.tags) ? c.tags.join(' ').toLowerCase() : '';

    return title.includes(q) || caseId.includes(q) || target.includes(q) || fir.includes(q) || crime.includes(q) || tags.includes(q);
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Archive Header & Control Bar */}
      <div
        style={{
          background: 'var(--bg-card)',
          borderRadius: 'var(--radius-sm)',
          border: '1px solid var(--border-subtle)',
          padding: '16px 20px',
          boxShadow: 'var(--shadow-sm)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 14,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div
            style={{
              width: 36,
              height: 36,
              borderRadius: 'var(--radius-xs)',
              background: 'linear-gradient(135deg, #af52de 0%, #7b2cbf 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#ffffff',
            }}
          >
            <Database size={18} />
          </div>
          <div>
            <h3 style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>
              Case Archive & Saved Dockets
            </h3>
            <p style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
              {cases.length} {cases.length === 1 ? 'docket' : 'dockets'} saved in database archive · Cross-case correlation enabled
            </p>
          </div>
        </div>

        {/* Filter & Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          {/* Search box */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-xs)',
              padding: '5px 10px',
              width: 220,
            }}
          >
            <Search size={13} color="var(--text-tertiary)" />
            <input
              type="text"
              placeholder="Search docket, address, FIR..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                border: 'none',
                background: 'transparent',
                outline: 'none',
                fontSize: 11.5,
                color: 'var(--text-primary)',
                width: '100%',
              }}
            />
          </div>

          {/* Chain filter pills */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-pill)',
              padding: '2px',
              gap: 2,
            }}
          >
            {['all', 'ethereum', 'bitcoin', 'tron'].map((ch) => (
              <button
                key={ch}
                onClick={() => setFilterChain(ch)}
                style={{
                  border: 'none',
                  background: filterChain === ch ? 'var(--accent-primary)' : 'transparent',
                  color: filterChain === ch ? '#ffffff' : 'var(--text-secondary)',
                  padding: '3px 9px',
                  borderRadius: 'var(--radius-pill)',
                  fontSize: 10.5,
                  fontWeight: 500,
                  cursor: 'pointer',
                  textTransform: 'capitalize',
                  transition: 'all 0.15s var(--ease-apple)',
                }}
              >
                {ch}
              </button>
            ))}
          </div>

          <button
            className="apple-btn apple-btn-primary"
            onClick={onStartNewCase}
            style={{
              background: 'linear-gradient(135deg, #0071e3 0%, #2997ff 100%)',
              fontWeight: 600,
            }}
          >
            <PlusCircle size={14} />
            <span>Start New Investigation</span>
          </button>
        </div>
      </div>

      {/* Case Folders Grid */}
      {loading ? (
        <div style={{ padding: '60px 20px', textAlign: 'center', color: 'var(--text-secondary)' }}>
          <p style={{ fontSize: 12 }}>Loading saved case dockets from database...</p>
        </div>
      ) : filteredCases.length === 0 ? (
        <div
          style={{
            background: 'var(--bg-card)',
            borderRadius: 'var(--radius-sm)',
            border: '1px dashed var(--border-strong)',
            padding: '48px 24px',
            textAlign: 'center',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 12,
          }}
        >
          <Folder size={40} color="var(--text-tertiary)" strokeWidth={1.5} />
          <div>
            <h4 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>
              {cases.length === 0 ? 'No Saved Cases Yet' : 'No Matching Dockets Found'}
            </h4>
            <p style={{ fontSize: 11.5, color: 'var(--text-secondary)', maxWidth: 360, margin: '4px auto 0' }}>
              {cases.length === 0
                ? 'Run an investigation or click "Start New Investigation" to trace counterparties and save the case docket into the database.'
                : 'Try adjusting your search keywords or chain filter.'}
            </p>
          </div>
          <button className="apple-btn apple-btn-primary" onClick={onStartNewCase}>
            <PlusCircle size={14} />
            <span>Start New Investigation</span>
          </button>
        </div>
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
            gap: 16,
          }}
        >
          {filteredCases.map((c) => {
            const target = c.targetAddress || c.wallet?.address || '0x...';
            const chain = (c.chain || 'ethereum').toUpperCase();
            const dateFormatted = c.createdAt ? new Date(c.createdAt).toLocaleDateString() : 'Recent';
            const nodeCount = c.nodes?.length || c.graph?.nodes?.length || 0;
            const score = c.suspicionScore ?? c.riskAssessment?.suspicionScore ?? 75;
            const tags = Array.isArray(c.tags) ? c.tags : [];

            // Identify investigator correlation tags
            const crossTags = tags.filter((t) =>
              typeof t === 'string' &&
              (t.toLowerCase().includes('investigator') || t.toLowerCase().includes('previous') || t.toLowerCase().includes('appeared'))
            );

            return (
              <div
                key={c.caseId}
                className="case-folder-card"
                onClick={() => onOpenCase(c)}
                style={{
                  background: 'var(--bg-card)',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-subtle)',
                  boxShadow: 'var(--shadow-sm)',
                  padding: '16px 18px',
                  cursor: 'pointer',
                  position: 'relative',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 10,
                  transition: 'all 0.2s var(--ease-apple)',
                }}
              >
                {/* Folder Top Tab / Notch */}
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <FolderOpen size={16} color="#0071e3" />
                    <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-primary)', fontFamily: 'ui-monospace, monospace' }}>
                      {c.caseId}
                    </span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span
                      style={{
                        fontSize: 9.5,
                        fontWeight: 600,
                        padding: '2px 6px',
                        borderRadius: 'var(--radius-pill)',
                        background: 'rgba(0, 113, 227, 0.1)',
                        color: 'var(--accent-primary)',
                      }}
                    >
                      {chain}
                    </span>

                    <span
                      style={{
                        fontSize: 9.5,
                        fontWeight: 700,
                        padding: '2px 6px',
                        borderRadius: 'var(--radius-pill)',
                        background: score >= 75 ? 'rgba(175, 82, 222, 0.15)' : score >= 50 ? 'rgba(255, 69, 58, 0.15)' : 'rgba(52, 199, 89, 0.15)',
                        color: score >= 75 ? 'var(--risk-critical)' : score >= 50 ? 'var(--risk-high)' : 'var(--risk-clean)',
                      }}
                    >
                      {score}/100
                    </span>
                  </div>
                </div>

                {/* Case Title & Crime Reference */}
                <div>
                  <h4 style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', lineHeight: 1.3 }}>
                    {c.title || `Investigation ${c.caseId}`}
                  </h4>
                  {c.caseNumber && (
                    <div style={{ fontSize: 10.5, color: 'var(--text-tertiary)', marginTop: 2 }}>
                      Ref: <strong>{c.caseNumber}</strong> {c.crimeType ? `· ${c.crimeType}` : ''}
                    </div>
                  )}
                </div>

                {/* Target Address Display */}
                <div
                  style={{
                    background: 'var(--bg-surface)',
                    padding: '6px 10px',
                    borderRadius: 'var(--radius-xs)',
                    border: '1px solid var(--border-subtle)',
                    fontSize: 10.5,
                    fontFamily: 'ui-monospace, monospace',
                    color: 'var(--text-secondary)',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                >
                  🎯 {target}
                </div>

                {/* Cross-Investigation Tag Badges (Special Highlight) */}
                {crossTags.length > 0 && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    {crossTags.map((tag, idx) => (
                      <div
                        key={idx}
                        style={{
                          fontSize: 10,
                          fontWeight: 600,
                          padding: '3px 8px',
                          borderRadius: 'var(--radius-xs)',
                          background: 'rgba(175, 82, 222, 0.16)',
                          border: '1px solid rgba(175, 82, 222, 0.35)',
                          color: '#af52de',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: 4,
                        }}
                      >
                        <AlertTriangle size={11} color="#af52de" />
                        <span>{tag}</span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Footer Metrics & Actions */}
                <div
                  style={{
                    borderTop: '1px solid var(--border-subtle)',
                    paddingTop: 8,
                    marginTop: 'auto',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    fontSize: 10.5,
                    color: 'var(--text-tertiary)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                    <Clock size={11} />
                    <span>{dateFormatted}</span>
                    {nodeCount > 0 && <span>· {nodeCount} Nodes</span>}
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <button
                      onClick={(e) => handleDelete(e, c.caseId)}
                      className="apple-icon-btn"
                      style={{ width: 22, height: 22, color: 'var(--risk-high)' }}
                      title="Delete Case from Archive"
                    >
                      <Trash2 size={11} />
                    </button>
                    <span
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 2,
                        color: 'var(--accent-primary)',
                        fontWeight: 600,
                        fontSize: 11,
                      }}
                    >
                      Open Docket <ArrowRight size={11} />
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
