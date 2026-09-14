import React, { useState } from 'react';
import { X, Save, FolderCheck, Shield, FileText } from 'lucide-react';
import { saveInvestigationCase } from '../api/client';

export const SaveCaseModal = ({
  isOpen,
  onClose,
  targetAddress,
  currentChain,
  graphNodes,
  graphEdges,
  riskAssessment,
  wallet,
  investigationDossier,
  onSaved,
}) => {
  if (!isOpen) return null;

  const defaultCaseId = `CASE-2026-I4C-${(targetAddress || '71C8').slice(2, 6).toUpperCase()}-${Date.now().toString().slice(-4)}`;
  const [caseId, setCaseId] = useState(defaultCaseId);
  const [title, setTitle] = useState(
    targetAddress ? `Investigation on ${targetAddress.slice(0, 8)}... (${(currentChain || 'ethereum').toUpperCase()})` : 'New Case Docket'
  );
  const [caseNumber, setCaseNumber] = useState('FIR-2026/CYBER-409');
  const [crimeType, setCrimeType] = useState('Cryptocurrency Investment Fraud / Peeling');
  const [investigatorName, setInvestigatorName] = useState('Cyber Forensics Officer (LEA-4092)');
  const [notes, setNotes] = useState('');
  const [tagsInput, setTagsInput] = useState('High Priority, Inter-State Fraud, VASP Subpoena');
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);

    const tagsArray = tagsInput
      .split(',')
      .map((t) => t.trim())
      .filter(Boolean);

    // Merge existing wallet tags if any
    const mergedTags = Array.from(new Set([...tagsArray, ...(wallet?.tags || [])]));

    const payload = {
      caseId,
      title,
      caseNumber,
      crimeType,
      investigatorName,
      targetAddress,
      chain: currentChain || 'ethereum',
      notes,
      tags: mergedTags,
      suspicionScore: riskAssessment?.suspicionScore ?? wallet?.riskScore ?? 75,
      riskLevel: riskAssessment?.riskLevel || wallet?.riskLevel || 'CRITICAL',
      nodes: graphNodes.map((n) => n.data || n),
      edges: graphEdges,
      wallet,
      riskAssessment,
      investigationDossier,
      createdAt: new Date().toISOString(),
    };

    try {
      await saveInvestigationCase(payload);
      if (onSaved) onSaved(payload);
      onClose();
    } catch (err) {
      console.error('Error saving case docket:', err);
      alert(`Failed to save case docket: ${err.message || err}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 480 }}>
        {/* Modal Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div
              style={{
                width: 28,
                height: 28,
                borderRadius: 'var(--radius-xs)',
                background: 'linear-gradient(135deg, #0071e3 0%, #2997ff 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#ffffff',
              }}
            >
              <Save size={15} />
            </div>
            <h3 style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>
              Save Case Docket to Database
            </h3>
          </div>
          <button onClick={onClose} className="apple-icon-btn" style={{ width: 24, height: 24 }}>
            <X size={13} />
          </button>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {/* Target Address (Readonly) */}
          <div>
            <label style={{ fontSize: 10.5, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>
              Target Suspect Address
            </label>
            <div
              style={{
                background: 'var(--bg-surface)',
                padding: '6px 10px',
                borderRadius: 'var(--radius-xs)',
                border: '1px solid var(--border-subtle)',
                fontFamily: 'ui-monospace, monospace',
                fontSize: 11,
                marginTop: 3,
                wordBreak: 'break-all',
              }}
            >
              {targetAddress || 'N/A'} ({currentChain})
            </div>
          </div>

          {/* Case Title */}
          <div>
            <label style={{ fontSize: 10.5, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>
              Docket Title
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
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

          {/* Grid: FIR Ref & Crime Type */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            <div>
              <label style={{ fontSize: 10.5, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>
                FIR / Crime Ref #
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
                <option value="Cryptocurrency Investment Fraud / Peeling">Investment Fraud / Peeling</option>
                <option value="Ransomware Extortion Payment">Ransomware Extortion</option>
                <option value="Pig Butchering / High-Yield Scam">Pig Butchering Scam</option>
                <option value="Phishing / Drainer Contract">Phishing Drainer</option>
                <option value="AML Evasion & Mixing">AML Evasion & Mixing</option>
              </select>
            </div>
          </div>

          {/* Investigator Notes */}
          <div>
            <label style={{ fontSize: 10.5, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>
              Investigator Field Notes
            </label>
            <textarea
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="e.g., Target address transferred 5.2 ETH directly into CoinDCX router; Section 91 notice ready."
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
                resize: 'none',
              }}
            />
          </div>

          {/* Tags */}
          <div>
            <label style={{ fontSize: 10.5, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>
              Tags (Comma-Separated)
            </label>
            <input
              type="text"
              value={tagsInput}
              onChange={(e) => setTagsInput(e.target.value)}
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

          {/* Footer Actions */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 8 }}>
            <button type="button" className="apple-btn apple-btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button
              type="submit"
              className="apple-btn apple-btn-primary"
              disabled={saving}
              style={{
                background: 'linear-gradient(135deg, #0071e3 0%, #2997ff 100%)',
                fontWeight: 600,
              }}
            >
              <Save size={13} />
              <span>{saving ? 'Saving...' : 'Save Case to Database'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
