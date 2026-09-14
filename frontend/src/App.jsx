import React, { useState, useCallback, useEffect } from 'react';
import { SearchBar } from './components/SearchBar';
import { WalletOverviewCard } from './components/WalletOverviewCard';
import { GraphView } from './components/GraphView';
import { TransactionList } from './components/TransactionList';
import { SuspicionPointsView } from './components/SuspicionPointsView';
import { InvestigationGuideView } from './components/InvestigationGuideView';
import { ForensicReportView } from './components/ForensicReportView';
import { CaseArchiveView } from './components/CaseArchiveView';
import { SaveCaseModal } from './components/SaveCaseModal';
import { NewCaseModal } from './components/NewCaseModal';
import { SettingsModal } from './components/SettingsModal';
import {
  analyzeWallet,
  traceWalletFunds,
  evaluateHeuristics,
  runUnifiedInvestigation,
  getDemoInvestigation,
  getSavedInvestigations,
  saveInvestigationCase,
  checkHealth,
} from './api/client';
import {
  Shield,
  AlertCircle,
  CheckCircle2,
  Loader2,
  AlertTriangle,
  Folder,
  FolderOpen,
  FolderPlus,
  FileText,
  BookOpen,
  Save,
  Printer,
  Compass,
  GitFork,
  Activity,
  Layers,
  Database,
} from 'lucide-react';

class GraphErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  componentDidCatch(error, errorInfo) {
    console.error('GraphView ErrorBoundary caught error:', error, errorInfo);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            padding: 36,
            background: 'var(--bg-card)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid rgba(255, 69, 58, 0.3)',
            textAlign: 'center',
            color: 'var(--text-secondary)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 12,
          }}
        >
          <AlertTriangle size={32} color="#ff453a" />
          <h4 style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)' }}>
            Forensic Graph Display Notice
          </h4>
          <p style={{ fontSize: 12, maxWidth: 440, color: 'var(--text-secondary)' }}>
            {this.state.error?.message || 'A render issue occurred while computing graph coordinates.'}
          </p>
          <button
            className="apple-btn apple-btn-primary"
            onClick={() => this.setState({ hasError: false, error: null })}
          >
            Reload Graph View
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

export function App() {
  const [searchedAddress, setSearchedAddress] = useState('');
  const [currentChain, setCurrentChain] = useState('ethereum');
  const [currentAsset, setCurrentAsset] = useState('ETH');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [toastMessage, setToastMessage] = useState(null);

  // Traversal & filter parameters
  const [hops, setHops] = useState(2);
  const [minAmount, setMinAmount] = useState('0.0');
  const [direction, setDirection] = useState('both');

  // Primary navigation: 'graph' | 'suspicion' | 'investigate' | 'archive' | 'report' | 'guide'
  const [activeTab, setActiveTab] = useState('graph');
  const [activeDocketSubTab, setActiveDocketSubTab] = useState('graph');

  // Modals
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isSaveCaseOpen, setIsSaveCaseOpen] = useState(false);
  const [isNewCaseOpen, setIsNewCaseOpen] = useState(false);

  // Saved investigations count & active case metadata
  const [savedCasesCount, setSavedCasesCount] = useState(0);
  const [activeCaseDetails, setActiveCaseDetails] = useState({
    caseId: 'CASE-2026-I4C-INITIAL',
    caseNumber: 'FIR-2026/CYBER-409',
    crimeType: 'Cryptocurrency Investment Fraud / Peeling',
    investigatorName: 'Cyber Forensics Officer (LEA-4092)',
    notes: '',
  });

  // Loaded Forensic Data
  const [analysisData, setAnalysisData] = useState(null);
  const [graphNodes, setGraphNodes] = useState([]);
  const [graphEdges, setGraphEdges] = useState([]);
  const [riskAssessment, setRiskAssessment] = useState(null);
  const [investigationDossier, setInvestigationDossier] = useState(null);

  // Backend Health Status
  const [backendHealthy, setBackendHealthy] = useState(false);

  useEffect(() => {
    let isMounted = true;
    const checkStatus = async () => {
      try {
        const res = await checkHealth();
        if (isMounted) setBackendHealthy(res.status === 'healthy');
      } catch {
        if (isMounted) setBackendHealthy(false);
      }
    };
    checkStatus();
    const timer = setInterval(checkStatus, 15000);
    return () => {
      isMounted = false;
      clearInterval(timer);
    };
  }, []);

  // Refresh saved cases count
  const refreshSavedCasesCount = useCallback(async () => {
    try {
      const saved = await getSavedInvestigations();
      setSavedCasesCount(saved ? saved.length : 0);
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    refreshSavedCasesCount();
  }, [refreshSavedCasesCount]);

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3500);
  };

  const getAssetForChain = (chain, addr = '') => {
    const c = (chain || '').toLowerCase();
    if (c === 'bitcoin' || addr.startsWith('1') || addr.startsWith('3') || addr.startsWith('bc1')) return 'BTC';
    if (c === 'tron' || addr.startsWith('T')) return 'TRX';
    if (c === 'solana') return 'SOL';
    return 'ETH';
  };

  // Primary trace / analyze function
  const handleSearch = async ({
    address,
    chain = 'ethereum',
    hops: searchHops = hops,
    minAmount: searchMin = minAmount,
    direction: searchDir = direction,
  }) => {
    if (!address) return;
    setLoading(true);
    setError(null);
    setSearchedAddress(address);
    setCurrentChain(chain);

    const detectedAsset = getAssetForChain(chain, address);
    setCurrentAsset(detectedAsset);

    const newCaseId = `CASE-2026-I4C-${address.slice(2, 6).toUpperCase()}-${Date.now().toString().slice(-4)}`;
    setActiveCaseDetails((prev) => ({
      ...prev,
      caseId: newCaseId,
      targetAddress: address,
      chain,
    }));

    try {
      // 1. Fetch wallet baseline overview
      const analyzeRes = await analyzeWallet(chain, address, searchHops);
      setAnalysisData(analyzeRes);

      let finalNodes = analyzeRes.graph?.nodes || [];
      let finalEdges = analyzeRes.graph?.edges || [];

      if (finalNodes.length > 0) {
        setGraphNodes(finalNodes);
        setGraphEdges(finalEdges);
      }

      // Demo fallback handler
      if (address.toLowerCase() === '0x71c836489b990038848971201991802901238910' && finalNodes.length <= 1) {
        try {
          const demoDossier = await getDemoInvestigation();
          setInvestigationDossier(demoDossier);
          finalNodes = demoDossier.attribution?.graph?.nodes || [];
          finalEdges = demoDossier.attribution?.graph?.edges || [];
          setRiskAssessment({
            suspicionScore: 92,
            riskLevel: 'CRITICAL',
            riskClassification: 'CRITICAL',
            triggeredRules: [
              {
                ruleId: 'P1_KNOWN_VASP_DESTINATION',
                priority: 1,
                title: 'High-Value Deposit into Verified VASP (CoinDCX)',
                severity: 'ACTIONABLE',
                weight: 52,
                description: '5.2000 ETH transited into CoinDCX deposit router.',
                evidence: ['Direct 1-hop deposit to CoinDCX omnibus wallet', 'Reg No: FIU-IND/2023/VASP/0012'],
              },
              {
                ruleId: 'P6_RAPID_PEELING',
                priority: 2,
                title: 'Peeling Chain and Outbound Fragmentation',
                severity: 'HIGH',
                weight: 25,
                description: 'Funds fragmented across 3 separate branches within 20 minutes.',
                evidence: ['Binance feeder branch (2.1000 ETH)', 'Cluster UC-42 feeder branch (1.4000 ETH)'],
              },
            ],
            recommendation: 'IMMEDIATE ACTION: Serve Section 91 CrPC notice to CoinDCX Nodal Officer to freeze 5.2000 ETH.',
          });
        } catch (demoErr) {
          console.warn('Demo fallback notice:', demoErr);
        }
      } else {
        // Multi-hop tracing
        try {
          const traceRes = await traceWalletFunds({
            chain,
            address,
            maxDepth: searchHops,
            direction: searchDir,
            minimumTransferValue: searchMin,
          });

          if (traceRes && traceRes.nodes && traceRes.nodes.length > 0) {
            finalNodes = traceRes.nodes.map((tn) => ({
              id: tn.address.toLowerCase(),
              type: 'customWalletNode',
              data: {
                ...tn,
                fullAddress: tn.address,
                label: `${tn.address.slice(0, 6)}...${tn.address.slice(-4)}`,
                nodeType: tn.type || (tn.address.toLowerCase() === address.toLowerCase() ? 'investigated' : 'wallet'),
                depth: tn.depth,
                asset: detectedAsset,
              },
            }));

            finalEdges = (traceRes.edges || []).map((te, idx) => ({
              id: `e-${te.source}-${te.target}-${idx}`,
              source: te.source.toLowerCase(),
              target: te.target.toLowerCase(),
              totalValue: te.totalValue,
              label: `${parseFloat(te.totalValue || '0').toFixed(3)} ${detectedAsset}`,
              data: {
                transactionCount: te.transactionCount,
                totalTransferred: te.totalValue,
                asset: detectedAsset,
                hopDepth: te.hopDepth,
              },
              animated: false,
            }));
          }
        } catch (traceErr) {
          console.warn('Trace funds notice:', traceErr);
        }

        // Evaluate Heuristics
        try {
          const heuristicRes = await evaluateHeuristics({
            chain,
            address,
            multihopNodes: finalNodes.map((n) => n.data || n),
          });
          if (heuristicRes && heuristicRes.riskAssessment) {
            setRiskAssessment(heuristicRes.riskAssessment);
          }
        } catch (heurErr) {
          setRiskAssessment({
            suspicionScore: analyzeRes.wallet?.riskScore || 15,
            riskLevel: analyzeRes.wallet?.riskLevel || 'LOW',
            riskClassification: analyzeRes.wallet?.riskLevel || 'LOW',
            triggeredRules: [],
          });
        }

        // Unified Investigation Dossier
        try {
          const dossierRes = await runUnifiedInvestigation({
            chain,
            address,
            maxDepth: searchHops,
            minimumTransferValue: searchMin,
            direction: searchDir,
          });
          setInvestigationDossier(dossierRes);
        } catch (dossierErr) {
          console.warn('Dossier notice:', dossierErr);
        }
      }

      setGraphNodes(finalNodes);
      setGraphEdges(finalEdges);
      setActiveTab('graph');
      setActiveDocketSubTab('graph');
      showToast(`Docket ${newCaseId} traced across ${searchHops} hops.`);

      // Auto-record and save active investigation into database
      try {
        await saveInvestigationCase({
          caseId: newCaseId,
          title: `Investigation on ${address.slice(0, 8)}... (${detectedAsset})`,
          caseNumber: 'FIR-2026/CYBER-409',
          crimeType: 'Cryptocurrency Fund Tracing',
          targetAddress: address,
          chain,
          suspicionScore: 85,
          riskLevel: 'HIGH',
          nodes: finalNodes.map((n) => n.data || n),
          edges: finalEdges,
          wallet: analyzeRes?.wallet,
        });
        refreshSavedCasesCount();
      } catch (autoSaveErr) {
        console.warn('Auto-save notice:', autoSaveErr);
      }
    } catch (err) {
      console.error('Wallet analysis failed:', err);
      setError(err.message || 'Error communicating with backend forensics engine.');
    } finally {
      setLoading(false);
    }
  };

  // Node branch tracking / expansion (Expands 2 HOPS on pressing node search icon)
  const handleTrackNode = useCallback(
    async (nodeData, onDone) => {
      const targetAddr = nodeData.fullAddress || nodeData.address || nodeData.label;
      if (!targetAddr) {
        if (onDone) onDone();
        return;
      }

      const nodeChain = nodeData.chain || currentChain;
      const nodeAsset = getAssetForChain(nodeChain, targetAddr);

      try {
        let newDiscoveredNodes = [];
        let newDiscoveredEdges = [];

        try {
          const trace2Hop = await traceWalletFunds({
            chain: nodeChain,
            address: targetAddr,
            maxDepth: 2,
            direction: 'both',
            minimumTransferValue: minAmount,
          });

          if (trace2Hop && trace2Hop.nodes && trace2Hop.nodes.length > 0) {
            const parentDepth = nodeData.depth || 1;

            trace2Hop.nodes.forEach((tn) => {
              const cleanAddr = tn.address.toLowerCase();
              if (cleanAddr !== targetAddr.toLowerCase()) {
                newDiscoveredNodes.push({
                  address: tn.address,
                  depth: parentDepth + (tn.depth || 1),
                  type: tn.type || 'wallet',
                  chain: nodeChain,
                  riskScore: tn.riskScore || 15,
                  riskLevel: tn.riskLevel || 'LOW',
                  totalAmount: tn.totalSent || tn.totalReceivedFromParent || '0',
                  transactionCount: tn.transactionCount || 1,
                  tags: tn.tags || [],
                });
              }
            });

            trace2Hop.edges.forEach((te) => {
              newDiscoveredEdges.push({
                source: te.source.toLowerCase(),
                target: te.target.toLowerCase(),
                totalValue: te.totalValue,
                asset: nodeAsset,
                transactionCount: te.transactionCount,
                hopDepth: (nodeData.depth || 1) + (te.hopDepth || 1),
              });
            });
          }
        } catch (traceErr) {
          console.warn('Trace 2-hop notice:', traceErr);
        }

        if (newDiscoveredNodes.length > 0) {
          const existingIds = new Set(graphNodes.map((n) => n.id.toLowerCase()));
          const parentKey = targetAddr.toLowerCase();

          const mergedNodes = graphNodes.map((n) => {
            if (n.id.toLowerCase() === parentKey) {
              return {
                ...n,
                data: {
                  ...n.data,
                  isExpanded: true,
                  tags: Array.from(new Set([...(n.data?.tags || []), 'Expanded Ref'])),
                },
              };
            }
            return n;
          });

          newDiscoveredNodes.forEach((tn) => {
            const id = tn.address.toLowerCase();
            if (!existingIds.has(id)) {
              existingIds.add(id);
              mergedNodes.push({
                id,
                type: 'customWalletNode',
                data: {
                  ...tn,
                  fullAddress: tn.address,
                  label: `${tn.address.slice(0, 5)}...${tn.address.slice(-4)}`,
                  nodeType: tn.type || 'wallet',
                  depth: tn.depth,
                  asset: nodeAsset,
                },
              });
            }
          });

          const existingEdgeKeys = new Set(graphEdges.map((e) => `${e.source}->${e.target}`));
          const mergedEdges = [...graphEdges];

          newDiscoveredEdges.forEach((te, idx) => {
            const edgeKey = `${te.source.toLowerCase()}->${te.target.toLowerCase()}`;
            if (!existingEdgeKeys.has(edgeKey)) {
              existingEdgeKeys.add(edgeKey);
              mergedEdges.push({
                id: `e-${te.source}-${te.target}-${idx}`,
                source: te.source.toLowerCase(),
                target: te.target.toLowerCase(),
                totalValue: te.totalValue,
                type: 'straight',
                data: {
                  transactionCount: te.transactionCount || 1,
                  totalTransferred: te.totalValue || '0',
                  asset: nodeAsset,
                  hopDepth: te.hopDepth,
                },
                animated: false,
              });
            }
          });

          setGraphNodes(mergedNodes);
          setGraphEdges(mergedEdges);
          showToast(`Expanded 2 hops from ${targetAddr.slice(0, 6)}... (+${newDiscoveredNodes.length} nodes).`);
        } else {
          showToast(`No additional 2-hop counterparties found.`);
        }
      } catch (err) {
        console.error('2-hop branch expansion failed:', err);
      } finally {
        if (onDone) onDone();
      }
    },
    [graphNodes, graphEdges, currentChain, minAmount]
  );

  // Open saved case from archive docket
  const handleOpenSavedCase = (savedCase) => {
    const target = savedCase.targetAddress || savedCase.wallet?.address;
    if (target) {
      setSearchedAddress(target);
    }
    const chain = savedCase.chain || 'ethereum';
    setCurrentChain(chain);
    setCurrentAsset(getAssetForChain(chain, target));

    setActiveCaseDetails({
      caseId: savedCase.caseId,
      caseNumber: savedCase.caseNumber || 'FIR-2026/CYBER-409',
      crimeType: savedCase.crimeType || 'Cryptocurrency Fund Tracing',
      investigatorName: savedCase.investigatorName || 'Cyber Forensics Officer (LEA-4092)',
      notes: savedCase.notes || '',
      targetAddress: target,
      chain,
    });

    if (savedCase.wallet) {
      setAnalysisData({
        wallet: savedCase.wallet,
        metadata: { chain, totalPeersDiscovered: (savedCase.nodes || []).length },
      });
    }

    if (savedCase.nodes && savedCase.nodes.length > 0) {
      const formattedNodes = savedCase.nodes.map((n) => {
        const d = n.data || n;
        const addr = d.address || d.fullAddress || n.id || '';
        return {
          id: (n.id || addr).toLowerCase(),
          type: 'customWalletNode',
          data: {
            ...d,
            fullAddress: addr,
            label: d.label || `${addr.slice(0, 6)}...${addr.slice(-4)}`,
            nodeType: d.nodeType || d.type || 'wallet',
            asset: getAssetForChain(chain, addr),
          },
        };
      });
      setGraphNodes(formattedNodes);
    }

    if (savedCase.edges && savedCase.edges.length > 0) {
      setGraphEdges(savedCase.edges);
    }

    if (savedCase.riskAssessment) {
      setRiskAssessment(savedCase.riskAssessment);
    }

    if (savedCase.investigationDossier) {
      setInvestigationDossier(savedCase.investigationDossier);
    }

    setActiveTab('graph');
    setActiveDocketSubTab('graph');
    showToast(`Case ${savedCase.caseId} opened from database docket.`);
  };

  // Launch new case from modal
  const handleLaunchNewCase = ({ address, chain, caseNumber, crimeType, hops: newHops, direction: newDir, minAmount: newMin }) => {
    setHops(newHops);
    setDirection(newDir);
    setMinAmount(newMin);
    setActiveCaseDetails({
      caseId: `CASE-2026-I4C-${address.slice(2, 6).toUpperCase()}-${Date.now().toString().slice(-4)}`,
      caseNumber,
      crimeType,
      investigatorName: 'Cyber Forensics Officer (LEA-4092)',
      notes: '',
      targetAddress: address,
      chain,
    });
    handleSearch({ address, chain, hops: newHops, minAmount: newMin, direction: newDir });
  };

  const isActiveDocket = ['graph', 'suspicion', 'investigate'].includes(activeTab);
  const suspicionScore = riskAssessment?.suspicionScore ?? analysisData?.wallet?.riskScore ?? 0;
  const suspicionLevel = (riskAssessment?.riskLevel || analysisData?.wallet?.riskLevel || 'LOW').toUpperCase();
  const ruleCount = riskAssessment?.triggeredRules?.length || 0;

  // Cross-case tags on the current active wallet
  const activeTags = analysisData?.wallet?.tags || [];
  const crossInvestigatorTag = activeTags.find(
    (t) => typeof t === 'string' && (t.toLowerCase().includes('investigator') || t.toLowerCase().includes('previous'))
  );

  return (
    <div className="app-container">
      {/* Top Application Header Bar */}
      <header className="top-header">
        {/* Left Branding */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
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
              boxShadow: '0 2px 8px rgba(0, 113, 227, 0.3)',
            }}
          >
            <Shield size={17} strokeWidth={2.4} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <h1 style={{ fontSize: 13.5, fontWeight: 700, letterSpacing: '-0.02em', color: 'var(--text-primary)' }}>
                TraceACT
              </h1>
              <span
                style={{
                  fontSize: 9,
                  fontWeight: 700,
                  padding: '1px 5px',
                  borderRadius: 'var(--radius-pill)',
                  background: 'rgba(0, 113, 227, 0.12)',
                  color: 'var(--accent-primary)',
                  letterSpacing: '0.04em',
                }}
              >
                LEA FORENSICS
              </span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 9.5, color: 'var(--text-tertiary)' }}>
              <span
                style={{
                  width: 5,
                  height: 5,
                  borderRadius: '50%',
                  background: backendHealthy ? '#34c759' : '#ff9f0a',
                }}
              />
              <span>{backendHealthy ? 'Database Engine Connected' : 'Local Forensics Engine'}</span>
            </div>
          </div>
        </div>

        {/* Center / Right Search Bar */}
        <div style={{ flex: 1, maxWidth: 680, margin: '0 16px' }}>
          <SearchBar
            onSearch={handleSearch}
            loading={loading}
            initialAddress={searchedAddress}
            hops={hops}
            setHops={setHops}
            minAmount={minAmount}
            setMinAmount={setMinAmount}
            direction={direction}
            setDirection={setDirection}
            onOpenSettings={() => setIsSettingsOpen(true)}
          />
        </div>
      </header>

      {/* Top Folder-Docket Navigation Bar (Folder-like Tabs Structure) */}
      <nav className="folder-docket-bar">
        <div className="folder-tabs-group">
          {/* Tab 1: Active Investigation Case */}
          <button
            className={`folder-tab ${isActiveDocket ? 'active' : ''}`}
            onClick={() => {
              setActiveTab(activeDocketSubTab || 'graph');
            }}
          >
            <FolderOpen size={14} />
            <span>Active Case Docket</span>
            {graphNodes.length > 0 && (
              <span className="folder-tab-badge">
                {graphNodes.length} Nodes
              </span>
            )}
          </button>

          {/* Tab 2: Case Archive & Saved Investigations */}
          <button
            className={`folder-tab ${activeTab === 'archive' ? 'active' : ''}`}
            onClick={() => setActiveTab('archive')}
          >
            <Database size={14} />
            <span>Case Archive & Saved Dockets</span>
            {savedCasesCount > 0 && (
              <span className="folder-tab-badge">
                {savedCasesCount}
              </span>
            )}
          </button>

          {/* Tab 3: Official Forensic Dossier & Report */}
          <button
            className={`folder-tab ${activeTab === 'report' ? 'active' : ''}`}
            onClick={() => setActiveTab('report')}
          >
            <FileText size={14} />
            <span>Forensic Dossier & CrPC 91</span>
          </button>

          {/* Tab 4: Standard Operating Procedures (SOP) */}
          <button
            className={`folder-tab ${activeTab === 'guide' ? 'active' : ''}`}
            onClick={() => setActiveTab('guide')}
          >
            <BookOpen size={14} />
            <span>SOP Guidelines</span>
          </button>

          {/* Action Tab: Start New Investigation */}
          <button
            className="folder-tab folder-action-tab"
            onClick={() => setIsNewCaseOpen(true)}
          >
            <FolderPlus size={14} />
            <span>+ Start New Investigation</span>
          </button>
        </div>
      </nav>

      {/* Active Case Docket Sub-Bar (When an investigation is in active mode) */}
      {isActiveDocket && (
        <div className="active-docket-bar">
          {/* Left: Case ID & Cross-Investigation Alert */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <Folder size={14} color="#0071e3" />
              <strong style={{ color: 'var(--text-primary)', fontFamily: 'ui-monospace, monospace', fontSize: 11.5 }}>
                {activeCaseDetails.caseId}
              </strong>
              <span
                style={{
                  fontSize: 9.5,
                  padding: '1px 6px',
                  borderRadius: 'var(--radius-pill)',
                  background: 'rgba(0, 113, 227, 0.1)',
                  color: 'var(--accent-primary)',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                }}
              >
                {currentChain} ({currentAsset})
              </span>
            </div>

            {/* Cross-Investigator Match Badge */}
            {crossInvestigatorTag && (
              <div
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 4,
                  fontSize: 10,
                  fontWeight: 600,
                  background: 'rgba(175, 82, 222, 0.15)',
                  border: '1px solid rgba(175, 82, 222, 0.35)',
                  color: '#af52de',
                  padding: '2px 8px',
                  borderRadius: 'var(--radius-pill)',
                }}
              >
                <AlertTriangle size={11} color="#af52de" />
                <span>{crossInvestigatorTag}</span>
              </div>
            )}
          </div>

          {/* Center: Docket View Mode Switcher Pills */}
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
            <button
              onClick={() => {
                setActiveTab('graph');
                setActiveDocketSubTab('graph');
              }}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 5,
                padding: '3px 10px',
                borderRadius: 'var(--radius-pill)',
                border: 'none',
                background: activeTab === 'graph' ? 'var(--accent-primary)' : 'transparent',
                color: activeTab === 'graph' ? '#ffffff' : 'var(--text-secondary)',
                fontSize: 11,
                fontWeight: 500,
                cursor: 'pointer',
                transition: 'all 0.15s var(--ease-apple)',
              }}
            >
              <GitFork size={12} />
              <span>Forensic Graph</span>
            </button>

            <button
              onClick={() => {
                setActiveTab('suspicion');
                setActiveDocketSubTab('suspicion');
              }}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 5,
                padding: '3px 10px',
                borderRadius: 'var(--radius-pill)',
                border: 'none',
                background: activeTab === 'suspicion' ? 'var(--accent-primary)' : 'transparent',
                color: activeTab === 'suspicion' ? '#ffffff' : 'var(--text-secondary)',
                fontSize: 11,
                fontWeight: 500,
                cursor: 'pointer',
                transition: 'all 0.15s var(--ease-apple)',
              }}
            >
              <Shield size={12} />
              <span>Suspicion Points ({suspicionScore}/100)</span>
            </button>

            <button
              onClick={() => {
                setActiveTab('investigate');
                setActiveDocketSubTab('investigate');
              }}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 5,
                padding: '3px 10px',
                borderRadius: 'var(--radius-pill)',
                border: 'none',
                background: activeTab === 'investigate' ? 'var(--accent-primary)' : 'transparent',
                color: activeTab === 'investigate' ? '#ffffff' : 'var(--text-secondary)',
                fontSize: 11,
                fontWeight: 500,
                cursor: 'pointer',
                transition: 'all 0.15s var(--ease-apple)',
              }}
            >
              <Compass size={12} />
              <span>Investigation Playbook</span>
            </button>
          </div>

          {/* Right: Actions */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <button
              className="apple-btn apple-btn-secondary"
              onClick={() => setIsSaveCaseOpen(true)}
              style={{ padding: '4px 10px', fontSize: 11 }}
            >
              <Save size={12} />
              <span>Save Case</span>
            </button>

            <button
              className="apple-btn apple-btn-primary"
              onClick={() => setActiveTab('report')}
              style={{ padding: '4px 10px', fontSize: 11 }}
            >
              <Printer size={12} />
              <span>Generate PDF Dossier</span>
            </button>
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <main className="app-main">
        <div className="main-content">
          {/* Notification Toast */}
          {toastMessage && (
            <div
              style={{
                background: 'var(--accent-primary)',
                color: '#ffffff',
                padding: '6px 14px',
                borderRadius: 'var(--radius-pill)',
                fontSize: 11,
                fontWeight: 500,
                display: 'inline-flex',
                alignItems: 'center',
                gap: 6,
                alignSelf: 'center',
                boxShadow: '0 3px 12px rgba(0, 113, 227, 0.25)',
                animation: 'fadeIn 0.18s var(--ease-apple)',
              }}
            >
              <CheckCircle2 size={12} />
              <span>{toastMessage}</span>
            </div>
          )}

          {/* Error Banner */}
          {error && (
            <div
              style={{
                background: 'rgba(255, 69, 58, 0.1)',
                border: '1px solid rgba(255, 69, 58, 0.25)',
                color: 'var(--risk-high)',
                borderRadius: 'var(--radius-xs)',
                padding: '8px 12px',
                fontSize: 11.5,
                display: 'flex',
                alignItems: 'center',
                gap: 8,
              }}
            >
              <AlertCircle size={15} />
              <span>{error}</span>
            </div>
          )}

          {/* Wallet Overview Card (Shown in Active Docket) */}
          {isActiveDocket && analysisData?.wallet && (
            <WalletOverviewCard wallet={analysisData.wallet} metadata={analysisData.metadata} />
          )}

          {/* Tab: Forensic Graph View */}
          {activeTab === 'graph' && (
            <>
              {graphNodes.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  <GraphErrorBoundary>
                    <GraphView
                      initialNodes={graphNodes}
                      initialEdges={graphEdges}
                      rootAddress={analysisData?.wallet?.address}
                      targetAsset={currentAsset}
                      onTrackNode={handleTrackNode}
                      onInvestigateAddress={(addr) =>
                        handleSearch({ address: addr, chain: currentChain, hops, minAmount, direction })
                      }
                    />
                  </GraphErrorBoundary>

                  {analysisData?.transactions && analysisData.transactions.length > 0 && (
                    <TransactionList
                      transactions={analysisData.transactions}
                      targetAddress={analysisData.wallet?.address}
                    />
                  )}
                </div>
              ) : loading ? (
                <div style={{ padding: '60px 20px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                  <Loader2
                    size={32}
                    color="var(--accent-primary)"
                    style={{ margin: '0 auto 12px', animation: 'spin 1s linear infinite' }}
                  />
                  <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>
                    Tracing Blockchain Counterparties...
                  </h3>
                  <p style={{ fontSize: 11.5, color: 'var(--text-tertiary)', maxWidth: 380, margin: '0 auto' }}>
                    Querying ledger endpoints, discovering VASP touchpoints, and calculating suspicion points.
                  </p>
                </div>
              ) : (
                <div style={{ padding: '50px 20px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                  <Shield size={32} color="var(--accent-primary)" style={{ margin: '0 auto 10px' }} />
                  <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>
                    Multi-Hop Forensic Graph
                  </h3>
                  <p style={{ fontSize: 11.5, maxWidth: 420, margin: '0 auto 16px', lineHeight: 1.45 }}>
                    Enter a suspect wallet address above or click <strong>+ Start New Investigation</strong> to trace fund movements, attribute VASP endpoints, and generate a court-admissible report.
                  </p>
                  <button className="apple-btn apple-btn-primary" onClick={() => setIsNewCaseOpen(true)}>
                    <FolderPlus size={13} />
                    <span>+ Start New Investigation Docket</span>
                  </button>
                </div>
              )}
            </>
          )}

          {/* Tab: Suspicion Points View */}
          {activeTab === 'suspicion' && (
            <SuspicionPointsView
              riskAssessment={riskAssessment}
              wallet={analysisData?.wallet}
            />
          )}

          {/* Tab: Investigation Playbook & Next Steps */}
          {activeTab === 'investigate' && (
            <InvestigationGuideView
              investigationData={investigationDossier}
              wallet={analysisData?.wallet}
            />
          )}

          {/* Tab: Case Archive & Saved Dockets */}
          {activeTab === 'archive' && (
            <CaseArchiveView
              onOpenCase={handleOpenSavedCase}
              onStartNewCase={() => setIsNewCaseOpen(true)}
              showToast={showToast}
            />
          )}

          {/* Tab: Forensic Dossier & Report */}
          {activeTab === 'report' && (
            <ForensicReportView
              reportData={investigationDossier}
              wallet={analysisData?.wallet}
              graphData={{ nodes: graphNodes, edges: graphEdges }}
              riskAssessment={riskAssessment}
              currentChain={currentChain}
              currentAsset={currentAsset}
              caseDetails={activeCaseDetails}
            />
          )}

          {/* Tab: SOP Guidelines */}
          {activeTab === 'guide' && (
            <InvestigationGuideView
              investigationData={investigationDossier}
              wallet={analysisData?.wallet}
            />
          )}
        </div>
      </main>

      {/* Save Case Modal */}
      <SaveCaseModal
        isOpen={isSaveCaseOpen}
        onClose={() => setIsSaveCaseOpen(false)}
        targetAddress={searchedAddress}
        currentChain={currentChain}
        graphNodes={graphNodes}
        graphEdges={graphEdges}
        riskAssessment={riskAssessment}
        wallet={analysisData?.wallet}
        investigationDossier={investigationDossier}
        onSaved={(savedCase) => {
          setActiveCaseDetails(savedCase);
          refreshSavedCasesCount();
          showToast(`Case ${savedCase.caseId} saved to database archive.`);
        }}
      />

      {/* Start New Investigation Modal */}
      <NewCaseModal
        isOpen={isNewCaseOpen}
        onClose={() => setIsNewCaseOpen(false)}
        onLaunch={handleLaunchNewCase}
      />

      {/* Settings Modal */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        defaultHops={hops}
        setDefaultHops={setHops}
        dustFilter={minAmount}
        setDustFilter={setMinAmount}
      />
    </div>
  );
}
