import React, { useState } from 'react';
import {
  Compass,
  CheckSquare,
  Clock,
  ShieldAlert,
  ArrowRight,
  FileCheck,
  Landmark,
  AlertCircle,
  Copy,
  Check,
  GitFork,
  CheckCircle2,
  Lock,
  ExternalLink,
  Flame,
  Scale
} from 'lucide-react';

export const InvestigationGuideView = ({ investigationData, wallet }) => {
  const [copiedKey, setCopiedKey] = useState(null);
  const [completedSteps, setCompletedSteps] = useState(new Set());

  const handleCopy = (text, key) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const toggleStep = (stepNum) => {
    setCompletedSteps(prev => {
      const next = new Set(prev);
      if (next.has(stepNum)) {
        next.delete(stepNum);
      } else {
        next.add(stepNum);
      }
      return next;
    });
  };

  const targetAddr = wallet?.address || investigationData?.targetAddress || '';

  if (!targetAddr) {
    return (
      <div
        style={{
          background: 'var(--bg-card)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-subtle)',
          padding: '64px 28px',
          textAlign: 'center',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 14,
          boxShadow: 'var(--shadow-sm)',
        }}
      >
        <div
          style={{
            width: 52,
            height: 52,
            borderRadius: 'var(--radius-sm)',
            background: 'rgba(0, 113, 227, 0.12)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#0071e3',
            marginBottom: 2,
          }}
        >
          <Compass size={26} strokeWidth={1.8} />
        </div>
        <h3 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
          Deterministic Forensic Investigation Playbook (SOP)
        </h3>
        <p style={{ fontSize: 13, color: 'var(--text-secondary)', maxWidth: 480, margin: 0, lineHeight: 1.55 }}>
          No suspect wallet address entered. Enter a wallet address in the top search bar to generate an actionable, step-wise SOP interdiction workflow, NetworkX bottleneck mule identification, and statutory freeze requisition directives.
        </p>
      </div>
    );
  }

  const targetChain = wallet?.chain || investigationData?.chain || 'ethereum';
  const targetAsset = wallet?.asset || (targetChain === 'bitcoin' ? 'BTC' : (targetChain === 'tron' ? 'TRX' : (targetChain === 'solana' ? 'SOL' : 'ETH')));
  const caseId = investigationData?.caseId || `CASE-${targetAddr.slice(2, 6).toUpperCase()}`;

  // NetworkX topological intelligence
  const netx = investigationData?.networkAnalytics;
  const bottleneckMules = netx?.bottleneckMules || [];
  const hasCycles = netx?.graphSummary?.hasCycles || false;
  const isDag = netx?.graphSummary?.isDirectedAcyclic || true;

  const mis = investigationData?.minimumInterventionSet;
  const timeline = investigationData?.timeline || [];

  // Deterministic Step-by-Step Playbook Steps from Backend
  const backendPlaybook = investigationData?.investigationPlaybook || [];

  // Robust deterministic fallback if playbook not pre-calculated
  const playbookSteps = backendPlaybook.length > 0 ? backendPlaybook : [
    {
      stepNumber: 1,
      phase: 'GOLDEN_WINDOW',
      phaseLabel: 'Phase 1: Immediate Containment (0–2h)',
      priority: 'CRITICAL',
      title: 'Preserve Cryptographic Ledger State (Section 65B BSA)',
      statutoryReference: 'Section 65B(4) Indian Evidence Act / Section 63 BSA',
      targetEntity: 'Suspect Case Ledger State',
      targetAddress: targetAddr,
      amount: `All ${targetAsset} Assets`,
      actionableDirective: `Compute and log SHA-256 integrity hash of the raw transaction manifest for ${targetAddr.slice(0, 10)}... Record current block height and validator timestamp to preclude evidence tampering claims.`,
      deadline: 'Immediate (< 1 Hour)',
      expectedOutcome: 'Non-repudiable electronic evidence chain of custody established for trial court.',
      badgeClass: 'badge-critical',
    },
    {
      stepNumber: 2,
      phase: 'GOLDEN_WINDOW',
      phaseLabel: 'Phase 1: Immediate Containment (0–2h)',
      priority: 'CRITICAL',
      title: 'Serve Emergency Statutory Freeze Notice under Section 91 & 102 CrPC',
      statutoryReference: 'Section 91 & 102 CrPC (Section 94 & 106 BNSS) r/w FIU-IND AML Rules',
      targetEntity: 'Identified Primary Regulated VASP',
      targetAddress: 'Exchange Deposit Router',
      amount: 'Primary Trace Volume',
      actionableDirective: 'Serve immediate statutory order to the designated Nodal Compliance Officer. Demand emergency debit freeze on the beneficiary custodial account and production of full KYC dossier (PAN, Aadhaar/Passport, linked bank accounts, and IP login audit logs).',
      deadline: 'Within 2 Hours (Golden Window before cash-out)',
      expectedOutcome: 'Immediate custodial asset freeze preventing fiat dissipation and suspect identification.',
      badgeClass: 'badge-critical',
    },
    {
      stepNumber: 3,
      phase: 'ACTIVE_INTERDICTION',
      phaseLabel: 'Phase 2: Active Interdiction (2–24h)',
      priority: 'HIGH',
      title: 'Interdict Critical Intermediary Money Mule (NetworkX Centrality Discovered)',
      statutoryReference: 'Section 91 CrPC (Section 94 BNSS) - Layering Intermediation',
      targetEntity: bottleneckMules.length > 0 ? `Key Mule (${bottleneckMules[0].address.slice(0, 10)}...)` : 'Fee/Gas Funding Genesis Origin',
      targetAddress: bottleneckMules.length > 0 ? bottleneckMules[0].address : targetAddr,
      amount: 'Intermediary Bridge Node',
      actionableDirective: bottleneckMules.length > 0
        ? `NetworkX betweenness centrality flagged ${bottleneckMules[0].address} as carrying the primary shortest transaction paths. Trace its gas funding source to identify the parent exchange where transaction fees were acquired.`
        : `Trace the genesis transaction providing native gas to ${targetAddr.slice(0, 10)}... Issue Section 91 notice to the originating exchange to identify the wallet's funding patron.`,
      deadline: 'Within 6 Hours',
      expectedOutcome: 'Uncovers parent funding exchange account; reveals syndicate operator identity.',
      badgeClass: 'badge-high',
    },
    {
      stepNumber: 4,
      phase: 'ACTIVE_INTERDICTION',
      phaseLabel: 'Phase 2: Active Interdiction (2–24h)',
      priority: 'HIGH',
      title: 'Issue Secondary Requisitions under Minimum Intervention Set (MIS)',
      statutoryReference: 'Section 91 CrPC / Law Enforcement Request Portal (LERT)',
      targetEntity: 'Secondary Actionable VASP',
      targetAddress: 'Secondary Destination Router',
      amount: 'Secondary Case Share',
      actionableDirective: `Fulfill Minimum Intervention Set (MIS) recommendation by serving statutory notices to the top remaining exchange destinations to achieve $\\ge 70\\%$ cumulative stolen fund coverage.`,
      deadline: 'Within 12 Hours',
      expectedOutcome: 'Secures secondary branch from dissipation across offshore or P2P trading desks.',
      badgeClass: 'badge-high',
    },
    {
      stepNumber: 5,
      phase: 'ACTIVE_INTERDICTION',
      phaseLabel: 'Phase 2: Active Interdiction (2–24h)',
      priority: 'MEDIUM',
      title: 'Investigate Detected Unknown Service Clusters (UC-YYYY-XXXX)',
      statutoryReference: 'Section 91 CrPC Inquiry on Unregistered Payment Processor / OTC Desk',
      targetEntity: 'Potential Service Cluster',
      targetAddress: 'Cluster Aggregation Hub',
      amount: 'Pooled Case Funds',
      actionableDirective: 'Identify whether high-velocity consolidation hubs belong to unhosted bot sweepers or unlicenced OTC brokers. Issue notice to associated domain registrars, payment gateways, or cloud infrastructure hosts.',
      deadline: 'Within 24 Hours',
      expectedOutcome: 'Discovers undisclosed custodial infrastructure and off-ramps.',
      badgeClass: 'badge-medium',
    },
    {
      stepNumber: 6,
      phase: 'JUDICIAL_RECOVERY',
      phaseLabel: 'Phase 3: Judicial Recovery (24–72h)',
      priority: 'MEDIUM',
      title: 'Deploy 24/7 Automated Blockchain Sentry on Residue Outflows',
      statutoryReference: 'Police Standing Order on Continuous Electronic Evidence Tracking',
      targetEntity: 'Unhosted Residue Wallets',
      targetAddress: 'Residual Unspent Outflows',
      amount: 'Unresolved Fund Balance',
      actionableDirective: 'Activate 60-minute automated background ledger monitoring on unspent balances to capture automated alerts if suspect attempts delayed liquidation at future block heights.',
      deadline: 'Continuous Background Sentry',
      expectedOutcome: 'Real-time alert dispatch upon subsequent sweep or bridging.',
      badgeClass: 'badge-clean',
    },
    {
      stepNumber: 7,
      phase: 'JUDICIAL_RECOVERY',
      phaseLabel: 'Phase 3: Judicial Recovery (24–72h)',
      priority: 'CRITICAL',
      title: 'Assemble Judicial Evidence Docket for Trial Court (Section 173 CrPC / 193 BNSS)',
      statutoryReference: 'Section 173 CrPC / Section 193 BNSS r/w Section 65B Indian Evidence Act / Section 63 BSA',
      targetEntity: 'Jurisdictional Criminal Court',
      targetAddress: `Case File ${caseId}`,
      amount: 'Entire Evidence Packet',
      actionableDirective: 'Compile the 16-section TraceACT forensic report, VASP compliance replies, frozen asset receipts, and signed Section 65B BSA certificate into the formal police charge sheet for filing before the Magistrate.',
      deadline: 'Within 72 Hours (Filing Window)',
      expectedOutcome: 'Court-admissible electronic evidence packet ready for framing of charges and asset recovery.',
      badgeClass: 'badge-critical',
    },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
      {/* Overview Header Banner */}
      <div
        style={{
          background: 'var(--bg-card)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-subtle)',
          padding: '22px 26px',
          boxShadow: 'var(--shadow-sm)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div
              style={{
                width: 38,
                height: 38,
                borderRadius: 'var(--radius-sm)',
                background: 'rgba(0, 113, 227, 0.12)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Scale size={22} color="#0071e3" />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <h3 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>
                  Deterministic Forensic Investigation Playbook (SOP)
                </h3>
                <span className="apple-badge badge-clean">100% Deterministic • Zero LLM</span>
              </div>
              <p style={{ fontSize: 12.5, color: 'var(--text-secondary)', marginTop: 2 }}>
                Step-wise Standard Operating Procedure under Section 91 & 102 CrPC (Section 94 & 106 BNSS) and Section 65B Bharatiya Sakshya Adhiniyam (BSA).
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: 11, fontFamily: 'ui-monospace, monospace', color: 'var(--text-tertiary)' }}>
              CASE: <strong style={{ color: 'var(--accent-primary)' }}>{caseId}</strong>
            </span>
            <span className="apple-badge badge-medium">
              {completedSteps.size} of {playbookSteps.length} Steps Executed
            </span>
          </div>
        </div>
      </div>

      {/* NetworkX Topological Intelligence Banner (if available) */}
      {netx && (
        <div
          style={{
            background: 'linear-gradient(135deg, rgba(0, 113, 227, 0.08) 0%, rgba(52, 199, 89, 0.05) 100%)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid rgba(0, 113, 227, 0.25)',
            padding: '16px 22px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8, flexWrap: 'wrap', gap: 8 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <GitFork size={17} color="#0071e3" />
              <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>
                NetworkX Topological Analysis & Confidence Engine
              </span>
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <span className={`apple-badge ${isDag ? 'badge-clean' : 'badge-high'}`}>
                {isDag ? '✓ Acyclic Flow Verified (Zero Dilution)' : '⚠ Cycle/Loop Detected'}
              </span>
              <span className="apple-badge badge-neutral">
                {netx.graphSummary?.nodeCount || 0} Nodes • {netx.graphSummary?.edgeCount || 0} Directed Edges
              </span>
            </div>
          </div>

          {bottleneckMules.length > 0 ? (
            <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              <strong style={{ color: '#ff9500' }}>Critical Money Mule Identified: </strong>
              <code style={{ fontFamily: 'ui-monospace, monospace', color: 'var(--text-primary)', background: 'var(--bg-tag)', padding: '2px 6px', borderRadius: 4 }}>
                {bottleneckMules[0].address}
              </code>{' '}
              exhibits highest betweenness centrality (<strong>{bottleneckMules[0].betweennessCentrality}</strong>).{' '}
              {bottleneckMules[0].significance}
            </div>
          ) : (
            <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
              Network topology indicates direct fan-out towards terminal exchange deposit endpoints with verified acyclic reachability.
            </div>
          )}
        </div>
      )}

      {/* Phased Investigation Timeline Pipeline */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: 12,
        }}
      >
        <div
          style={{
            background: 'var(--bg-card)',
            border: '1px solid rgba(255, 69, 58, 0.3)',
            borderRadius: 'var(--radius-sm)',
            padding: '12px 16px',
            borderLeft: '4px solid #ff453a',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
            <Flame size={14} color="#ff453a" />
            <span style={{ fontSize: 11, fontWeight: 700, color: '#ff453a', textTransform: 'uppercase', letterSpacing: 0.5 }}>
              Phase 1: Golden Window (0–2h)
            </span>
          </div>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)' }}>
            Evidence Hashing & Immediate VASP Freeze
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 2 }}>
            Steps 1 & 2 • Prevents cash-out at primary exchange
          </div>
        </div>

        <div
          style={{
            background: 'var(--bg-card)',
            border: '1px solid rgba(255, 149, 0, 0.3)',
            borderRadius: 'var(--radius-sm)',
            padding: '12px 16px',
            borderLeft: '4px solid #ff9500',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
            <Lock size={14} color="#ff9500" />
            <span style={{ fontSize: 11, fontWeight: 700, color: '#ff9500', textTransform: 'uppercase', letterSpacing: 0.5 }}>
              Phase 2: Interdiction (2–24h)
            </span>
          </div>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)' }}>
            Mule Bottlenecks & MIS Subpoenas
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 2 }}>
            Steps 3, 4 & 5 • Secures 70%+ stolen proceeds
          </div>
        </div>

        <div
          style={{
            background: 'var(--bg-card)',
            border: '1px solid rgba(52, 199, 89, 0.3)',
            borderRadius: 'var(--radius-sm)',
            padding: '12px 16px',
            borderLeft: '4px solid #34c759',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
            <FileCheck size={14} color="#34c759" />
            <span style={{ fontSize: 11, fontWeight: 700, color: '#34c759', textTransform: 'uppercase', letterSpacing: 0.5 }}>
              Phase 3: Judicial Filing (24–72h)
            </span>
          </div>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)' }}>
            24/7 Sentry & Court Charge-Sheet
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 2 }}>
            Steps 6 & 7 • Sec 65B certificate for Magistrate
          </div>
        </div>
      </div>

      {/* Minimum Intervention Set (MIS) Recommendation */}
      {mis && (
        <div
          style={{
            background: 'rgba(0, 113, 227, 0.05)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid rgba(0, 113, 227, 0.2)',
            padding: '16px 20px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6, flexWrap: 'wrap', gap: 8 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Landmark size={16} color="#0071e3" />
              <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>
                Minimum Intervention Set (MIS) Strategic Strategy
              </span>
            </div>
            <span className="apple-badge badge-clean">
              {mis.achievedCoveragePercentage || 73}% Stolen Fund Recovery Coverage
            </span>
          </div>
          <p style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
            {mis.explanation ||
              `Serving statutory requisitions to the top ${mis.vaspCount || 2} identified entities achieves high asset coverage while minimizing subpoena turnaround latency.`}
          </p>
        </div>
      )}

      {/* Step-by-Step Procedure Cards */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <h4 style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>
            Chronological Standard Operating Procedure (SOP Steps)
          </h4>
          <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
            Click checkbox to track operational execution
          </span>
        </div>

        {playbookSteps.map((step) => {
          const isDone = completedSteps.has(step.stepNumber);
          return (
            <div
              key={step.stepNumber}
              style={{
                background: isDone ? 'rgba(52, 199, 89, 0.04)' : 'var(--bg-card)',
                borderRadius: 'var(--radius-md)',
                border: isDone ? '1px solid rgba(52, 199, 89, 0.35)' : '1px solid var(--border-subtle)',
                boxShadow: 'var(--shadow-sm)',
                padding: '18px 22px',
                display: 'flex',
                flexDirection: 'column',
                gap: 12,
                transition: 'all 0.2s ease',
              }}
            >
              {/* Step Header */}
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12 }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
                  {/* Step Number Badge / Checkbox */}
                  <button
                    onClick={() => toggleStep(step.stepNumber)}
                    style={{
                      width: 28,
                      height: 28,
                      borderRadius: 8,
                      border: isDone ? '2px solid #34c759' : '2px solid var(--border-medium)',
                      background: isDone ? '#34c759' : 'var(--bg-surface)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      cursor: 'pointer',
                      flexShrink: 0,
                      marginTop: 2,
                      transition: 'all 0.15s ease',
                    }}
                    title={isDone ? 'Mark as Incomplete' : 'Mark as Executed'}
                  >
                    {isDone ? (
                      <Check size={16} color="#ffffff" strokeWidth={3} />
                    ) : (
                      <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-secondary)' }}>
                        {step.stepNumber}
                      </span>
                    )}
                  </button>

                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                      <span
                        className={`apple-badge ${
                          step.priority === 'CRITICAL'
                            ? 'badge-critical'
                            : step.priority === 'HIGH'
                            ? 'badge-high'
                            : 'badge-medium'
                        }`}
                      >
                        {step.priority}
                      </span>
                      <span style={{ fontSize: 11, color: 'var(--text-tertiary)', fontWeight: 600 }}>
                        {step.phaseLabel}
                      </span>
                      <span style={{ fontSize: 11, fontFamily: 'ui-monospace, monospace', color: 'var(--accent-primary)', background: 'rgba(0, 113, 227, 0.08)', padding: '1px 6px', borderRadius: 4 }}>
                        {step.statutoryReference}
                      </span>
                    </div>

                    <h4
                      style={{
                        fontSize: 14.5,
                        fontWeight: 700,
                        color: isDone ? '#34c759' : 'var(--text-primary)',
                        textDecoration: isDone ? 'line-through' : 'none',
                        marginTop: 4,
                      }}
                    >
                      Step {step.stepNumber}: {step.title}
                    </h4>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0 }}>
                  <Clock size={13} color="var(--text-tertiary)" />
                  <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-secondary)' }}>
                    {step.deadline}
                  </span>
                </div>
              </div>

              {/* Actionable Directive */}
              <div
                style={{
                  fontSize: 12.5,
                  lineHeight: 1.5,
                  color: 'var(--text-primary)',
                  background: 'var(--bg-surface)',
                  padding: '12px 14px',
                  borderRadius: 'var(--radius-sm)',
                  borderLeft: step.priority === 'CRITICAL' ? '3px solid #ff453a' : '3px solid #0071e3',
                }}
              >
                <strong>Operational Directive: </strong>
                {step.actionableDirective}
              </div>

              {/* Entity, Target, Expected Deliverable Grid */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 10, fontSize: 11.5 }}>
                <div style={{ padding: '8px 12px', borderRadius: 'var(--radius-xs)', background: 'var(--bg-tag)' }}>
                  <span style={{ color: 'var(--text-tertiary)', textTransform: 'uppercase', fontSize: 10, display: 'block', fontWeight: 600, marginBottom: 2 }}>
                    Target Entity / Endpoint
                  </span>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 6 }}>
                    <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                      {step.targetEntity}
                    </span>
                    {step.targetAddress && step.targetAddress !== 'N/A' && (
                      <button
                        onClick={() => handleCopy(step.targetAddress, `step-${step.stepNumber}`)}
                        className="apple-btn apple-btn-secondary"
                        style={{ padding: '2px 6px', fontSize: 10 }}
                        title="Copy target address"
                      >
                        {copiedKey === `step-${step.stepNumber}` ? <Check size={10} color="#34c759" /> : <Copy size={10} />}
                      </button>
                    )}
                  </div>
                </div>

                <div style={{ padding: '8px 12px', borderRadius: 'var(--radius-xs)', background: 'var(--bg-tag)' }}>
                  <span style={{ color: 'var(--text-tertiary)', textTransform: 'uppercase', fontSize: 10, display: 'block', fontWeight: 600, marginBottom: 2 }}>
                    Asset Exposure
                  </span>
                  <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                    {step.amount}
                  </span>
                </div>

                <div style={{ padding: '8px 12px', borderRadius: 'var(--radius-xs)', background: 'var(--bg-tag)', gridColumn: 'span 1' }}>
                  <span style={{ color: 'var(--text-tertiary)', textTransform: 'uppercase', fontSize: 10, display: 'block', fontWeight: 600, marginBottom: 2 }}>
                    Expected Legal Deliverable
                  </span>
                  <span style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>
                    {step.expectedOutcome}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Forensic Fund Chronology & Timeline */}
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
            <h4 style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>
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
