import React, { useState } from 'react';
import { FileText, Copy, Check, Printer, Shield, Download, CheckCircle2 } from 'lucide-react';

export const ForensicReportView = ({ reportData, wallet }) => {
  const [copied, setCopied] = useState(false);

  const target = wallet?.address || reportData?.targetAddress || 'N/A';
  const caseId = reportData?.caseId || `CASE-2026-I4C-${target.slice(2, 6)}`;
  const date = reportData?.generatedAt ? new Date(reportData.generatedAt).toLocaleString() : new Date().toLocaleString();

  const noticeText = reportData?.report?.section91NoticeText ||
    reportData?.section91NoticeText ||
    `FORM OF NOTICE UNDER SECTION 91 CODE OF CRIMINAL PROCEDURE, 1973
To: Nodal Grievance & Law Enforcement Officer (VASP / Custodial Exchange)
Case Reference: ${caseId}
Subject: Statutory Requisition for Immediate Preservation & Account Debit Freeze

WHEREAS credible cryptocurrency transaction records indicate illicit cyber fraud proceeds originated from or transited through the address:
Address: ${target}

YOU ARE HEREBY REQUIRED under Section 91 CrPC to immediately:
1. Freeze and restrict all debit facilities on all internal accounts mapped to the aforementioned deposit routers.
2. Furnish comprehensive KYC dossiers, Aadhaar/PAN records, registered phone numbers, and associated bank accounts.
3. Provide complete historical deposit/withdrawal logs with internal transaction IDs.

Officer In-Charge: Cyber Forensics & Financial Intelligence Cell
Authorized Under I4C / SAHYOG Framework`;

  const handleCopyNotice = () => {
    navigator.clipboard.writeText(noticeText);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Action Header */}
      <div
        style={{
          background: 'var(--bg-card)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-subtle)',
          padding: '18px 24px',
          boxShadow: 'var(--shadow-sm)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 12,
        }}
      >
        <div>
          <h3 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>
            Official LEA Forensic Investigation Dossier
          </h3>
          <p style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
            Case ID: {caseId} · Generated: {date}
          </p>
        </div>

        <div style={{ display: 'flex', gap: 10 }}>
          <button className="apple-btn apple-btn-secondary" onClick={handleCopyNotice}>
            {copied ? <Check size={14} color="#34c759" /> : <Copy size={14} />}
            <span>{copied ? 'Notice Copied' : 'Copy Sec 91 Notice'}</span>
          </button>
          <button className="apple-btn apple-btn-primary" onClick={handlePrint}>
            <Printer size={14} />
            <span>Print / Save Dossier</span>
          </button>
        </div>
      </div>

      {/* Case Header Details */}
      <div
        style={{
          background: 'var(--bg-card)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-subtle)',
          padding: '20px 24px',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: 14,
          fontSize: 12,
        }}
      >
        <div>
          <span style={{ color: 'var(--text-tertiary)', fontSize: 10, textTransform: 'uppercase' }}>TARGET ADDRESS</span>
          <div style={{ fontFamily: 'ui-monospace, monospace', fontWeight: 600, wordBreak: 'break-all', marginTop: 2 }}>
            {target}
          </div>
        </div>
        <div>
          <span style={{ color: 'var(--text-tertiary)', fontSize: 10, textTransform: 'uppercase' }}>BLOCKCHAIN NETWORK</span>
          <div style={{ fontWeight: 600, textTransform: 'capitalize', marginTop: 2 }}>
            {wallet?.chain || 'Ethereum'}
          </div>
        </div>
        <div>
          <span style={{ color: 'var(--text-tertiary)', fontSize: 10, textTransform: 'uppercase' }}>INVESTIGATING OFFICER</span>
          <div style={{ fontWeight: 600, marginTop: 2 }}>
            Cyber Forensics Officer (LEA-I4C-4092)
          </div>
        </div>
        <div>
          <span style={{ color: 'var(--text-tertiary)', fontSize: 10, textTransform: 'uppercase' }}>LEGAL ADMISSIBILITY</span>
          <div style={{ fontWeight: 600, color: 'var(--risk-clean)', marginTop: 2 }}>
            Sec 65B BSA Compliant
          </div>
        </div>
      </div>

      {/* Statutory Section 91 CrPC Notice */}
      <div
        style={{
          background: 'var(--bg-card)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-subtle)',
          padding: '20px 24px',
          boxShadow: 'var(--shadow-sm)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
          <h4 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>
            Statutory Notice under Section 91 CrPC (Ready for Issuance)
          </h4>
          <button className="apple-btn apple-btn-ghost" onClick={handleCopyNotice} style={{ padding: '4px 10px', fontSize: 12 }}>
            {copied ? <Check size={13} color="#34c759" /> : <Copy size={13} />}
            <span>Copy Text</span>
          </button>
        </div>

        <pre
          style={{
            background: 'var(--bg-surface)',
            padding: '16px',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--border-subtle)',
            fontFamily: 'ui-monospace, monospace',
            fontSize: 12,
            lineHeight: 1.55,
            color: 'var(--text-primary)',
            whiteSpace: 'pre-wrap',
            overflowX: 'auto',
          }}
        >
          {noticeText}
        </pre>
      </div>
    </div>
  );
};
