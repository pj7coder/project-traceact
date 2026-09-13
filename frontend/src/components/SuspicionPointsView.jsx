import React, { useState } from 'react';
import {
  ShieldAlert,
  AlertTriangle,
  Flame,
  CheckCircle2,
  ShieldCheck,
  HelpCircle,
  Layers,
  Award,
  ChevronDown,
  ChevronUp,
  Activity,
  Check,
  X,
} from 'lucide-react';

const PRIORITY_CATALOG = [
  {
    tier: 'Tier 1: Severe Threat Nexus (Critical Severity)',
    tierColor: '#ff453a',
    rules: [
      {
        id: 'P1_SANCTIONED_ADDRESSES',
        priority: 1,
        title: 'Connection to Sanctioned Addresses',
        weight: 100,
        severity: 'CRITICAL',
        description: 'Direct transaction detected with OFAC/UN sanctioned entity or blacklisted address.',
      },
      {
        id: 'P2_RANSOMWARE_INTERACTION',
        priority: 2,
        title: 'Interaction with Known Ransomware',
        weight: 95,
        severity: 'CRITICAL',
        description: 'Direct financial nexus to ransomware extortion infrastructure or payment portals.',
      },
      {
        id: 'P3_RECEIVING_STOLEN_FUNDS_HACKS',
        priority: 3,
        title: 'Receiving Stolen Funds & Connection to Known Hacks',
        weight: 92,
        severity: 'CRITICAL',
        description: 'Inflow or direct interaction with exploit addresses, bridge hacks, or stolen funds pools.',
      },
      {
        id: 'P4_SCAMS_MALICIOUS_CONTRACTS',
        priority: 4,
        title: 'Connection to Scams & Malicious Contract Interaction',
        weight: 88,
        severity: 'CRITICAL',
        description: 'Direct interaction with phishing drainers, fraudulent token contracts, or ponzi schemes.',
      },
    ],
  },
  {
    tier: 'Tier 2: Obfuscation & Syndicate Tactics (High Severity)',
    tierColor: '#ff9f0a',
    rules: [
      {
        id: 'P5_ILLICIT_SERVICES_MIXERS',
        priority: 5,
        title: 'Connection to Illicit Services & Anonymizing Mixers',
        weight: 82,
        severity: 'HIGH',
        description: 'Asset routing through Tornado Cash, darknet markets, or CoinJoin mixing pools.',
      },
      {
        id: 'P6_RAPID_MOVEMENT_OF_FUNDS',
        priority: 6,
        title: 'Rapid Movement of Funds (Peeling Chains & Pass-Through)',
        weight: 76,
        severity: 'HIGH',
        description: 'Pass-through behavior where large funds are immediately routed out without custodial retention.',
      },
      {
        id: 'P7_MULTIPLE_WALLETS_AS_ONE_CLUSTER',
        priority: 7,
        title: 'Multiple Wallets as One Cluster (Syndicate Looping)',
        weight: 70,
        severity: 'HIGH',
        description: 'Bi-directional fund looping and co-spending between target and peer wallets.',
      },
      {
        id: 'P8_SUSPICIOUS_TRANSACTION_PATTERN',
        priority: 8,
        title: 'Suspicious Transaction Pattern (High Velocity Burst)',
        weight: 65,
        severity: 'HIGH',
        description: 'High burst velocity of automated transfers in a compressed temporal window.',
      },
    ],
  },
  {
    tier: 'Tier 3: Financial Exposure & Profile Anomalies (Medium Severity)',
    tierColor: '#ffd60a',
    rules: [
      {
        id: 'P9_RECEIVING_SENDING_LARGE_AMOUNTS',
        priority: 9,
        title: 'Receiving / Sending Large Amounts (High-Value Exposure)',
        weight: 52,
        severity: 'MEDIUM',
        description: 'High-value transactions exceeding single-transfer or cumulative volume thresholds.',
      },
      {
        id: 'P10_MAKING_LARGE_NUMBER_OF_TRANSACTIONS',
        priority: 10,
        title: 'Making Large Number of Transactions (High Frequency)',
        weight: 45,
        severity: 'MEDIUM',
        description: 'Elevated transaction frequency (> 100 lifetime or > 50 trace operations).',
      },
      {
        id: 'P11_INDIRECT_EXPOSURE_SUSPICIOUS_WALLETS',
        priority: 11,
        title: 'Indirect Exposure to Suspicious Wallets (2+ Hops)',
        weight: 38,
        severity: 'MEDIUM',
        description: 'Downstream multi-hop counterparty ties to flagged mixers or illicit endpoints.',
      },
      {
        id: 'P12_CREATING_A_NEW_WALLET',
        priority: 12,
        title: 'Creating a New Wallet with Sudden Volume Surge',
        weight: 34,
        severity: 'MEDIUM',
        description: 'Freshly generated wallet (< 5 lifetime txs) immediately handling large asset volume.',
      },
      {
        id: 'P13_NO_VASP_ACCOUNT',
        priority: 13,
        title: 'No VASP Account (Pure Unhosted Hopping)',
        weight: 26,
        severity: 'MEDIUM',
        description: 'Exclusively unhosted self-custody hopping with zero registered VASP touchpoints.',
      },
    ],
  },
  {
    tier: 'Tier 4: Baseline Indicators & Retail Utility Dampener',
    tierColor: '#34c759',
    rules: [
      {
        id: 'P14_HOLDING_A_LOT_OF_ETH',
        priority: 14,
        title: 'Holding a Lot of ETH (High Custodial Balance)',
        weight: 15,
        severity: 'INFORMATIONAL',
        description: 'Substantial liquid custody holding on-chain (> 15 ETH or equivalent).',
      },
      {
        id: 'P15_SENDING_ETH_DIRECTLY_TO_PERSON',
        priority: 15,
        title: 'Sending ETH Directly to Another Person (Direct P2P)',
        weight: 10,
        severity: 'INFORMATIONAL',
        description: 'Direct unhosted peer-to-peer asset transfers outside smart contracts or custodial rails.',
      },
      {
        id: 'P16_DAY_TO_DAY_PURPOSES',
        priority: 16,
        title: 'Using Ethereum for Day-to-Day Purposes (Routine Retail Baseline)',
        weight: -20,
        severity: 'CLEAN_BASELINE',
        description: 'Normal personal/commercial utility with regulated exchanges without illicit nexus (Dampener).',
      },
    ],
  },
];

export const SuspicionPointsView = ({ riskAssessment, wallet }) => {
  const [showMatrix, setShowMatrix] = useState(true);

  if (!riskAssessment && !wallet) {
    return (
      <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-secondary)' }}>
        Enter a wallet address above to run the Suspicion Engine.
      </div>
    );
  }

  const score = riskAssessment?.suspicionScore ?? wallet?.riskScore ?? 0;
  const preciseScore = riskAssessment?.preciseScore ?? riskAssessment?.heuristicsBreakdown?.preciseScore ?? score;
  const level = (riskAssessment?.riskClassification || wallet?.riskLevel || 'LOW').toUpperCase();
  const triggeredRules = riskAssessment?.triggeredRules || [];
  const breakdown = riskAssessment?.heuristicsBreakdown || {};

  // Build a lookup map of triggered rules for quick status check in the matrix
  const triggeredRuleMap = new Map();
  triggeredRules.forEach((r) => {
    if (r.ruleId) triggeredRuleMap.set(r.ruleId, r);
  });

  const getScoreColor = (s) => {
    if (s >= 75) return '#af52de';
    if (s >= 50) return '#ff453a';
    if (s >= 20) return '#ff9f0a';
    return '#34c759';
  };

  const getSeverityBadge = (sev) => {
    switch ((sev || '').toUpperCase()) {
      case 'CRITICAL': return 'badge-critical';
      case 'HIGH': return 'badge-high';
      case 'MEDIUM': return 'badge-medium';
      case 'CLEAN_BASELINE': return 'badge-low';
      default: return 'badge-low';
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Top Suspicion Points Gauge & Summary */}
      <div
        style={{
          background: 'var(--bg-card)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-subtle)',
          padding: '20px 24px',
          boxShadow: 'var(--shadow-sm)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 16,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
          {/* Radial Circular Metric */}
          <div
            style={{
              width: 76,
              height: 76,
              borderRadius: '50%',
              border: `4px solid ${getScoreColor(score)}`,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              background: 'var(--bg-tag)',
              boxShadow: `0 0 16px ${getScoreColor(score)}33`,
            }}
          >
            <span style={{ fontSize: 24, fontWeight: 800, color: getScoreColor(score), letterSpacing: '-0.03em', lineHeight: 1 }}>
              {score}
            </span>
            <span style={{ fontSize: 9, color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600, marginTop: 2 }}>
              {preciseScore && preciseScore !== score ? `${Number(preciseScore).toFixed(1)} pts` : 'Points'}
            </span>
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
              <span style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)' }}>
                Forensic Suspicion Engine Assessment
              </span>
              <span className={`apple-badge ${getSeverityBadge(level)}`}>
                {level} Risk Tier
              </span>
            </div>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', maxWidth: 540 }}>
              {riskAssessment?.recommendation ||
                'Calculated via TraceACT Prioritized Law Enforcement Engine with behavioral indicators, transfer velocity, and entity linkages.'}
            </p>
          </div>
        </div>

        {/* Quick Heuristics Chips */}
        <div style={{ display: 'flex', gap: 12, fontSize: 12, flexWrap: 'wrap' }}>
          <div style={{ padding: '8px 14px', borderRadius: 'var(--radius-sm)', background: 'var(--bg-tag)' }}>
            <div style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>PRECISE INDEX</div>
            <div style={{ fontSize: 15, fontWeight: 700, color: getScoreColor(score) }}>
              {Number(preciseScore).toFixed(1)} <span style={{ fontSize: 10, fontWeight: 500, color: 'var(--text-tertiary)' }}>/ 100</span>
            </div>
          </div>
          <div style={{ padding: '8px 14px', borderRadius: 'var(--radius-sm)', background: 'var(--bg-tag)' }}>
            <div style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>ACTIVE SIGNALS</div>
            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>
              {triggeredRules.length} Triggered
            </div>
          </div>
          <div style={{ padding: '8px 14px', borderRadius: 'var(--radius-sm)', background: 'var(--bg-tag)' }}>
            <div style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>MIXER BOOSTER</div>
            <div style={{ fontSize: 15, fontWeight: 700, color: breakdown.mixerBooster ? '#ff453a' : 'var(--text-primary)' }}>
              {breakdown.mixerBooster ? 'ACTIVE' : 'CLEAN'}
            </div>
          </div>
        </div>
      </div>

      {/* Triggered Forensic Rules & Points Breakdown */}
      <div
        style={{
          background: 'var(--bg-card)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-subtle)',
          boxShadow: 'var(--shadow-sm)',
          padding: '20px 24px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
          <h4 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>
            Triggered Forensic Evidence & Points ({triggeredRules.length})
          </h4>
          <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>
            Arranged by Forensic Threat Priority
          </span>
        </div>

        {triggeredRules.length === 0 ? (
          <div style={{ padding: 24, textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 13 }}>
            No high-suspicion heuristic rules triggered for this address. Address exhibits clean baseline behavior.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {triggeredRules.map((rule, idx) => {
              const isDampener = (rule.weight || 0) < 0;
              return (
                <div
                  key={rule.ruleId || idx}
                  style={{
                    background: 'var(--bg-surface)',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border-subtle)',
                    padding: '14px 18px',
                    display: 'flex',
                    alignItems: 'flex-start',
                    justifyContent: 'space-between',
                    gap: 16,
                  }}
                >
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 5, flexWrap: 'wrap' }}>
                      {rule.priority && (
                        <span
                          style={{
                            fontSize: 10,
                            fontWeight: 700,
                            padding: '2px 8px',
                            borderRadius: 'var(--radius-pill)',
                            background: 'rgba(0, 113, 227, 0.12)',
                            color: 'var(--accent-primary)',
                            border: '1px solid rgba(0, 113, 227, 0.25)',
                          }}
                        >
                          Priority {rule.priority}
                        </span>
                      )}
                      <span className={`apple-badge ${getSeverityBadge(rule.severity)}`}>
                        {rule.severity}
                      </span>
                      <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>
                        {rule.title}
                      </span>
                      <span style={{ fontSize: 11, fontFamily: 'ui-monospace, monospace', color: 'var(--text-tertiary)' }}>
                        [{rule.ruleId}]
                      </span>
                    </div>

                    <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 8 }}>
                      {rule.description}
                    </p>

                    {/* Concrete Evidence Points */}
                    {rule.evidence && rule.evidence.length > 0 && (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                        {rule.evidence.map((ev, eIdx) => (
                          <div key={eIdx} style={{ fontSize: 11, color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: 6 }}>
                            <span style={{ width: 4, height: 4, borderRadius: '50%', background: isDampener ? '#34c759' : 'var(--accent-primary)' }} />
                            {ev}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Points Weight Badge */}
                  <div
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'flex-end',
                      flexShrink: 0,
                    }}
                  >
                    <span
                      style={{
                        fontSize: 16,
                        fontWeight: 700,
                        color: isDampener ? '#34c759' : getScoreColor(rule.weight || 20),
                      }}
                    >
                      {rule.weight > 0 ? `+${rule.weight}` : `${rule.weight}`}
                    </span>
                    <span style={{ fontSize: 9.5, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>
                      {isDampener ? 'Risk Dampener' : 'Points'}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Forensic Priority Hierarchy Matrix (Interactive Registry of all 18 Indicators) */}
      <div
        style={{
          background: 'var(--bg-card)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-subtle)',
          boxShadow: 'var(--shadow-sm)',
          overflow: 'hidden',
        }}
      >
        <button
          type="button"
          onClick={() => setShowMatrix((prev) => !prev)}
          style={{
            width: '100%',
            padding: '16px 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'transparent',
            border: 'none',
            cursor: 'pointer',
            textAlign: 'left',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <Layers size={16} color="var(--accent-primary)" />
            <div>
              <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>
                Forensic Suspicion Engine Priority Hierarchy Matrix
              </div>
              <div style={{ fontSize: 11.5, color: 'var(--text-secondary)' }}>
                Complete 16-level priority catalog organized by law enforcement threat tiers
              </div>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--text-secondary)', fontSize: 12 }}>
            <span>{showMatrix ? 'Collapse' : 'Expand Matrix'}</span>
            {showMatrix ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </div>
        </button>

        {showMatrix && (
          <div style={{ padding: '0 24px 24px 24px', display: 'flex', flexDirection: 'column', gap: 20 }}>
            {PRIORITY_CATALOG.map((tierGroup, tIdx) => (
              <div key={tIdx} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, fontWeight: 700, color: tierGroup.tierColor }}>
                  <span style={{ width: 8, height: 8, borderRadius: '50%', background: tierGroup.tierColor }} />
                  {tierGroup.tier}
                </div>

                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
                    gap: 10,
                  }}
                >
                  {tierGroup.rules.map((rule) => {
                    const isTriggered = triggeredRuleMap.has(rule.id);
                    const activeRule = triggeredRuleMap.get(rule.id);
                    const isDampener = rule.weight < 0;

                    return (
                      <div
                        key={rule.id}
                        style={{
                          background: isTriggered ? 'var(--bg-surface)' : 'var(--bg-card)',
                          borderRadius: 'var(--radius-sm)',
                          border: `1px solid ${isTriggered ? 'rgba(0, 113, 227, 0.4)' : 'var(--border-subtle)'}`,
                          padding: '12px 14px',
                          display: 'flex',
                          flexDirection: 'column',
                          justifyContent: 'space-between',
                          gap: 6,
                          position: 'relative',
                          transition: 'all 0.15s ease',
                          boxShadow: isTriggered ? '0 0 10px rgba(0, 113, 227, 0.12)' : 'none',
                        }}
                      >
                        <div>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
                            <span
                              style={{
                                fontSize: 10,
                                fontWeight: 700,
                                padding: '1px 6px',
                                borderRadius: 4,
                                background: 'var(--bg-tag)',
                                color: 'var(--text-secondary)',
                              }}
                            >
                              P{rule.priority}
                            </span>

                            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                              {isTriggered ? (
                                <span
                                  style={{
                                    fontSize: 10,
                                    fontWeight: 700,
                                    padding: '2px 7px',
                                    borderRadius: 10,
                                    background: isDampener ? 'rgba(52, 199, 89, 0.15)' : 'rgba(255, 69, 58, 0.15)',
                                    color: isDampener ? '#34c759' : '#ff453a',
                                    display: 'inline-flex',
                                    alignItems: 'center',
                                    gap: 3,
                                  }}
                                >
                                  <Flame size={10} />
                                  TRIGGERED ({isDampener ? rule.weight : `+${activeRule?.weight ?? rule.weight}`})
                                </span>
                              ) : (
                                <span
                                  style={{
                                    fontSize: 10,
                                    fontWeight: 500,
                                    padding: '2px 7px',
                                    borderRadius: 10,
                                    background: 'var(--bg-tag)',
                                    color: 'var(--text-tertiary)',
                                    display: 'inline-flex',
                                    alignItems: 'center',
                                    gap: 3,
                                  }}
                                >
                                  <Check size={10} />
                                  CLEAN
                                </span>
                              )}
                            </div>
                          </div>

                          <div style={{ fontSize: 12.5, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 2 }}>
                            {rule.title}
                          </div>
                          <div style={{ fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                            {rule.description}
                          </div>
                        </div>

                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: 10.5, color: 'var(--text-tertiary)', marginTop: 4 }}>
                          <span>Severity: <strong style={{ color: 'var(--text-secondary)' }}>{rule.severity}</strong></span>
                          <span>Base Weight: <strong style={{ color: isDampener ? '#34c759' : 'var(--text-primary)' }}>{rule.weight > 0 ? `+${rule.weight}` : rule.weight}</strong></span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
