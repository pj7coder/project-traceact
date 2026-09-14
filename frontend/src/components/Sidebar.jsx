import React, { useEffect, useState } from 'react';
import { Shield, GitFork, ShieldAlert, Compass, FileText } from 'lucide-react';
import { checkHealth } from '../api/client';

export const Sidebar = ({
  activeTab,
  setActiveTab,
  hops = 2,
  graphData,
  riskAssessment,
  wallet,
  investigationData,
}) => {
  const [backendStatus, setBackendStatus] = useState({ online: false, loading: true });

  useEffect(() => {
    let isMounted = true;
    const verifyBackend = async () => {
      try {
        const res = await checkHealth();
        if (isMounted) {
          setBackendStatus({
            online: res.status === 'healthy',
            loading: false,
          });
        }
      } catch (e) {
        if (isMounted) {
          setBackendStatus({ online: false, loading: false });
        }
      }
    };

    verifyBackend();
    const timer = setInterval(verifyBackend, 12000);
    return () => {
      isMounted = false;
      clearInterval(timer);
    };
  }, []);

  const hasTarget = Boolean(wallet?.address);
  const nodeCount = graphData?.nodes?.length || 0;
  const edgeCount = graphData?.edges?.length || 0;
  const suspicionScore = hasTarget ? (riskAssessment?.suspicionScore ?? wallet?.riskScore ?? 0) : 0;
  const suspicionLevel = hasTarget ? ((riskAssessment?.riskLevel || riskAssessment?.riskClassification || wallet?.riskLevel || 'LOW').toUpperCase()) : 'LOW';
  const ruleCount = hasTarget ? (riskAssessment?.triggeredRules?.length || 0) : 0;
  const actionsCount = hasTarget ? (investigationData?.nextActions?.length || 2) : 0;
  const caseId = hasTarget ? (investigationData?.caseId || `CASE-${wallet.address.slice(2, 6).toUpperCase()}`) : 'Awaiting Target';

  const navItems = [
    {
      id: 'graph',
      title: 'Forensic Graph',
      icon: <GitFork size={16} />,
      metricPrimary: hasTarget ? `${nodeCount} Nodes · ${edgeCount} Edges` : '0 Nodes · 0 Edges',
      metricSecondary: `${hops} ${hops === 1 ? 'Hop' : 'Hops'} Traversal`,
    },
    {
      id: 'suspicion',
      title: 'Suspicion Points',
      icon: <ShieldAlert size={16} />,
      metricPrimary: hasTarget ? `${suspicionScore} / 100 Points` : '0 / 100 Points',
      metricSecondary: hasTarget ? `${ruleCount} Rules (${suspicionLevel})` : '0 Rules (Standby)',
      badgeColor: suspicionScore >= 75 ? '#af52de' : suspicionScore >= 50 ? '#ff453a' : suspicionScore >= 20 ? '#ff9f0a' : '#34c759',
    },
    {
      id: 'investigate',
      title: 'Investigation Playbook',
      icon: <Compass size={16} />,
      metricPrimary: hasTarget ? `${actionsCount} Steps Planned` : '0 Steps Planned',
      metricSecondary: hasTarget ? 'Section 91 Ready' : 'Standby',
    },
    {
      id: 'report',
      title: 'Forensic Dossier & Report',
      icon: <FileText size={16} />,
      metricPrimary: caseId,
      metricSecondary: hasTarget ? 'Sec 65B BSA Admissible' : 'Standby',
    },
  ];

  return (
    <aside className="app-sidebar">
      <div>
        {/* Top Branding */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: 'var(--radius-xs)',
              background: 'linear-gradient(135deg, #0071e3 0%, #2997ff 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#ffffff',
              boxShadow: '0 2px 8px rgba(0, 113, 227, 0.25)',
            }}
          >
            <Shield size={17} strokeWidth={2.2} />
          </div>
          <div>
            <h1 style={{ fontSize: 14, fontWeight: 700, letterSpacing: '-0.02em', color: 'var(--text-primary)' }}>
              TraceACT
            </h1>
            <p style={{ fontSize: 10, color: 'var(--text-secondary)', fontWeight: 500 }}>
              Forensic Intelligence
            </p>
          </div>
        </div>

        {/* 4 Core Forensic Navigation Sections */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => setActiveTab(item.id)}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'flex-start',
                  width: '100%',
                  padding: '9px 10px',
                  borderRadius: 'var(--radius-xs)',
                  background: isActive ? 'var(--bg-card)' : 'transparent',
                  border: isActive ? '1px solid var(--border-strong)' : '1px solid transparent',
                  boxShadow: isActive ? 'var(--shadow-sm)' : 'none',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'all 0.15s var(--ease-apple)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, width: '100%', marginBottom: 3 }}>
                  <span style={{ color: isActive ? 'var(--accent-primary)' : 'var(--text-secondary)' }}>
                    {item.icon}
                  </span>
                  <span style={{ fontSize: 11.5, fontWeight: 600, color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)', flex: 1 }}>
                    {item.title}
                  </span>
                  {item.badgeColor && (
                    <span
                      style={{
                        width: 6,
                        height: 6,
                        borderRadius: '50%',
                        background: item.badgeColor,
                        boxShadow: `0 0 5px ${item.badgeColor}`,
                      }}
                    />
                  )}
                </div>

                {/* Relevant Live Metrics */}
                <div style={{ paddingLeft: 24, width: '100%' }}>
                  <div style={{ fontSize: 10.5, fontWeight: 600, color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)' }}>
                    {item.metricPrimary}
                  </div>
                  <div style={{ fontSize: 9.5, color: 'var(--text-tertiary)' }}>
                    {item.metricSecondary}
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </aside>
  );
};
