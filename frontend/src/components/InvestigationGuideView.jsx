import React from 'react';
import { Compass, CheckSquare, Clock, ShieldAlert, ArrowRight, FileCheck, Landmark, AlertCircle } from 'lucide-react';

export const InvestigationGuideView = ({ investigationData, wallet }) => {
  const nextActions = investigationData?.nextActions || [
    {
      actionId: 'ACT-001',
      priority: 'CRITICAL',
      actionType: 'ISSUE_LAWFUL_REQUEST',
      title: 'Serve Section 91 CrPC Notice to Identified Primary VASP',
      reason: 'Direct fund flow observed into regulated custodial infrastructure.',
      relatedEntity: 'Exchange Deposit Router',
      expectedInvestigativeValue: 'Account debit freeze & KYC identity records (PAN/Aadhaar/bank account).',
      evidenceRequired: 'On-chain transaction hash manifest and address deposit proof.',
    },
    {
      actionId: 'ACT-002',
      priority: 'HIGH',
      actionType: 'PRESERVE_EVIDENCE',
      title: 'Preserve Cryptographic Ledger Snapshot (Section 65B BSA)',
      reason: 'Court admissibility requires verifiable SHA-256 evidence snapshot.',
      relatedEntity: wallet?.address || 'Target Address',
      expectedInvestigativeValue: 'Establishes legal chain of custody for court proceedings.',
      evidenceRequired: 'Raw block height manifest and block explorer certification.',
    },
  ];

  const mis = investigationData?.minimumInterventionSet;
  const timeline = investigationData?.timeline || [];
  const challenges = investigationData?.attributionChallenges || [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Overview Header */}
      <div
        style={{
          background: 'var(--bg-card)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-subtle)',
          padding: '20px 24px',
          boxShadow: 'var(--shadow-sm)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
          <Compass size={20} color="#0071e3" />
          <h3 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>
            Investigation Action Playbook & Statutory Next Steps
          </h3>
        </div>
        <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
          Prioritized sequence of statutory requisitions, evidence preservation actions, and notice issuance under Section 91 of the Code of Criminal Procedure (CrPC).
        </p>
      </div>

      {/* Minimum Intervention Set (MIS) if available */}
      {mis && (
        <div
          style={{
            background: 'rgba(0, 113, 227, 0.06)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid rgba(0, 113, 227, 0.2)',
            padding: '16px 20px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
            <Landmark size={16} color="#0071e3" />
            <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>
              Minimum Intervention Set (MIS) Recommendation
            </span>
            <span className="apple-badge badge-clean">
              {mis.achievedCoveragePercentage || 73}% Stolen Fund Coverage
            </span>
          </div>
          <p style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
            {mis.explanation ||
              `Serving statutory requisitions to the top ${mis.vaspCount || 2} identified entities covers the majority of tracked proceeds.`}
          </p>
        </div>
      )}

      {/* Prioritized Action Steps */}
      <div
        style={{
          background: 'var(--bg-card)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-subtle)',
          boxShadow: 'var(--shadow-sm)',
          padding: '20px 24px',
        }}
      >
        <h4 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 14 }}>
          Recommended Next Actions & Interventions
        </h4>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {nextActions.map((action, idx) => (
            <div
              key={action.actionId || idx}
              style={{
                background: 'var(--bg-surface)',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-subtle)',
                padding: '14px 18px',
                display: 'flex',
                flexDirection: 'column',
                gap: 8,
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span
                    className={`apple-badge ${
                      action.priority === 'CRITICAL' ? 'badge-critical' : action.priority === 'HIGH' ? 'badge-high' : 'badge-medium'
                    }`}
                  >
                    {action.priority}
                  </span>
                  <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>
                    {action.title}
                  </span>
                </div>
                <span style={{ fontSize: 11, fontFamily: 'ui-monospace, monospace', color: 'var(--text-tertiary)' }}>
                  {action.actionId}
                </span>
              </div>

              <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                <strong>Reason:</strong> {action.reason}
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, fontSize: 11, marginTop: 4 }}>
                <div style={{ padding: '6px 10px', borderRadius: 'var(--radius-xs)', background: 'var(--bg-tag)' }}>
                  <span style={{ color: 'var(--text-tertiary)' }}>TARGET ENTITY: </span>
                  <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{action.relatedEntity}</span>
                </div>
                <div style={{ padding: '6px 10px', borderRadius: 'var(--radius-xs)', background: 'var(--bg-tag)' }}>
                  <span style={{ color: 'var(--text-tertiary)' }}>EXPECTED VALUE: </span>
                  <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{action.expectedInvestigativeValue}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Forensic Timeline */}
      {timeline.length > 0 && (
        <div
          style={{
            background: 'var(--bg-card)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-subtle)',
            boxShadow: 'var(--shadow-sm)',
            padding: '20px 24px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
            <Clock size={16} color="var(--text-secondary)" />
            <h4 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>
              Forensic Fund Chronology
            </h4>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {timeline.map((item, idx) => (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: 12,
                  padding: '8px 0',
                  borderBottom: idx < timeline.length - 1 ? '1px solid var(--border-subtle)' : 'none',
                }}
              >
                <span style={{ fontSize: 11, fontFamily: 'ui-monospace, monospace', color: 'var(--accent-primary)', minWidth: 65 }}>
                  {item.time || `Step ${item.step}`}
                </span>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>
                    {item.event}
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>
                    {item.description}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
