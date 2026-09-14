import React, { useState, useCallback } from 'react';
import { Sidebar } from './components/Sidebar';
import { SearchBar } from './components/SearchBar';
import { WalletOverviewCard } from './components/WalletOverviewCard';
import { GraphView } from './components/GraphView';
import { TransactionList } from './components/TransactionList';
import { SuspicionPointsView } from './components/SuspicionPointsView';
import { InvestigationGuideView } from './components/InvestigationGuideView';
import { ForensicReportView } from './components/ForensicReportView';
import { SettingsModal } from './components/SettingsModal';
import {
  analyzeWallet,
  traceWalletFunds,
  evaluateHeuristics,
  runUnifiedInvestigation,
} from './api/client';
import { Shield, AlertCircle, CheckCircle2, Loader2, AlertTriangle } from 'lucide-react';

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

  // Active navigation tab (graph | suspicion | investigate | report)
  const [activeTab, setActiveTab] = useState('graph');
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  // Loaded Forensic Data
  const [analysisData, setAnalysisData] = useState(null);
  const [graphNodes, setGraphNodes] = useState([]);
  const [graphEdges, setGraphEdges] = useState([]);
  const [riskAssessment, setRiskAssessment] = useState(null);
  const [investigationDossier, setInvestigationDossier] = useState(null);

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

    try {
      // 1. Fetch wallet baseline overview
      const analyzeRes = await analyzeWallet(chain, address, searchHops);
      setAnalysisData(analyzeRes);

      let finalNodes = analyzeRes.graph?.nodes || [];
      let finalEdges = analyzeRes.graph?.edges || [];

      // Immediately render 1-hop counterparties so graph appears instantaneously
      if (finalNodes.length > 0) {
        setGraphNodes(finalNodes);
        setGraphEdges(finalEdges);
      }

      // Multi-hop BFS tracing across specified depth
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
            address: tn.address,
            fullAddress: tn.address,
            data: {
              ...tn,
              id: tn.address.toLowerCase(),
              address: tn.address,
              fullAddress: tn.address,
              label: `${tn.address.slice(0, 6)}...${tn.address.slice(-4)}`,
              nodeType: tn.type || (tn.address.toLowerCase() === address.toLowerCase() ? 'investigated' : 'wallet'),
              depth: tn.depth,
              asset: detectedAsset,
              balance: tn.balanceEth || tn.balance || '0',
              totalAmount: tn.totalReceivedFromParent || tn.totalSent || tn.totalAmount || '0',
              transactionCount: tn.transactionCount || 1,
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
        console.warn('Trace funds notice, using 1-hop:', traceErr);
      }

      // Suspicion Points evaluation
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

      // Investigation playbook & dossier
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

      setGraphNodes(finalNodes);
      setGraphEdges(finalEdges);
      showToast(`Traced ${searchHops} ${searchHops === 1 ? 'hop' : 'hops'} (${detectedAsset}).`);
    } catch (err) {
      console.error('Wallet analysis failed:', err);
      setError(err.message || 'Error communicating with backend forensics engine.');
    } finally {
      setLoading(false);
    }
  };

  // Node branch tracking / expansion (Expands 2 HOPS on pressing the node's search icon)
  const handleTrackNode = useCallback(
    async (nodeData, onDone) => {
      // Safely resolve the target address (ensure not truncated)
      const rawAddr = nodeData?.fullAddress || nodeData?.address || nodeData?.id || '';
      const targetAddr = rawAddr && !rawAddr.includes('...') ? rawAddr : '';
      if (!targetAddr) {
        console.error('Invalid or truncated address for branch expansion:', rawAddr);
        showToast('Invalid wallet address for branch expansion.');
        if (onDone) onDone();
        return;
      }

      const nodeChain = nodeData.chain || currentChain;
      const nodeAsset = getAssetForChain(nodeChain, targetAddr);

      try {
        // Execute 2-hop expansion from target node as reference
        let newDiscoveredNodes = [];
        let newDiscoveredEdges = [];

        try {
          const trace2Hop = await traceWalletFunds({
            chain: nodeChain,
            address: targetAddr,
            maxDepth: 2, // EXPAND EXACTLY 2 HOPS
            direction: 'both',
            minimumTransferValue: minAmount,
          });

          if (trace2Hop && trace2Hop.nodes && trace2Hop.nodes.length > 0) {
            const parentDepth = nodeData.depth || 1;

            trace2Hop.nodes.forEach((tn) => {
              const cleanAddr = tn.address.toLowerCase();
              if (cleanAddr !== targetAddr.toLowerCase()) {
                newDiscoveredNodes.push({
                  id: cleanAddr,
                  address: tn.address,
                  fullAddress: tn.address,
                  depth: parentDepth + (tn.depth || 1),
                  type: tn.type || 'wallet',
                  chain: nodeChain,
                  riskScore: tn.riskScore || 15,
                  riskLevel: tn.riskLevel || 'LOW',
                  balance: tn.balanceEth || tn.balance || '0',
                  totalAmount: tn.totalSent || tn.totalReceivedFromParent || tn.totalAmount || '0',
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
          console.warn('Trace 2-hop API notice, fetching direct counterparties:', traceErr);
          const subRes = await analyzeWallet(nodeChain, targetAddr);
          if (subRes && subRes.connectedWallets) {
            const parentDepth = nodeData.depth || 1;
            subRes.connectedWallets.slice(0, 6).forEach((cw) => {
              newDiscoveredNodes.push({
                id: cw.address.toLowerCase(),
                address: cw.address,
                fullAddress: cw.address,
                depth: parentDepth + 1,
                type: 'wallet',
                chain: nodeChain,
                riskScore: cw.riskScore || 15,
                riskLevel: cw.riskLevel || 'LOW',
                balance: cw.balance || '0',
                totalAmount: cw.totalAmount || '0',
                transactionCount: cw.transactionCount || 1,
                tags: cw.tags || [],
              });
              newDiscoveredEdges.push({
                source: targetAddr.toLowerCase(),
                target: cw.address.toLowerCase(),
                totalValue: cw.totalAmount || '0',
                asset: nodeAsset,
                transactionCount: cw.transactionCount || 1,
                hopDepth: parentDepth + 1,
              });
            });
          }
        }

        if (newDiscoveredNodes.length > 0) {
          const existingIds = new Set(graphNodes.map((n) => n.id.toLowerCase()));
          const parentKey = targetAddr.toLowerCase();

          // Mark parent as expanded target
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

          // Append new 2-hop nodes
          newDiscoveredNodes.forEach((tn) => {
            const id = (tn.address || tn.id).toLowerCase();
            if (!existingIds.has(id)) {
              existingIds.add(id);
              mergedNodes.push({
                id,
                type: 'customWalletNode',
                address: tn.address,
                fullAddress: tn.address,
                data: {
                  ...tn,
                  id,
                  address: tn.address,
                  fullAddress: tn.address,
                  label: `${tn.address.slice(0, 5)}...${tn.address.slice(-4)}`,
                  nodeType: tn.type || 'wallet',
                  depth: tn.depth,
                  asset: nodeAsset,
                },
              });
            }
          });

          // Append straight edges
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
        showToast(`Expansion notice: ${err.message || 'Counterparty limit reached'}`);
      } finally {
        if (onDone) onDone();
      }
    },
    [graphNodes, graphEdges, currentChain, minAmount]
  );

  const handleInvestigateAddress = (addr) => {
    handleSearch({ address: addr, chain: currentChain, hops, minAmount, direction });
  };

  const handleClearSearch = () => {
    setSearchedAddress('');
    setAnalysisData(null);
    setInvestigationDossier(null);
    setGraphNodes([]);
    setGraphEdges([]);
    setRiskAssessment(null);
    setError(null);
  };

  return (
    <div className="app-container">
      {/* Left Sidebar */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        hops={hops}
        graphData={{ nodes: graphNodes, edges: graphEdges }}
        riskAssessment={riskAssessment}
        wallet={analysisData?.wallet}
        investigationData={investigationDossier}
      />

      {/* Main Right Area */}
      <main className="app-main">
        {/* Top Header Bar */}
        <header className="top-header">
          <SearchBar
            onSearch={handleSearch}
            onClear={handleClearSearch}
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
        </header>

        {/* Main Content Area */}
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

          {/* Wallet Overview Strip */}
          {analysisData?.wallet && (
            <WalletOverviewCard wallet={analysisData.wallet} metadata={analysisData.metadata} />
          )}

          {/* Tab 1: Forensic Graph View */}
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
                      onInvestigateAddress={handleInvestigateAddress}
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
                  <Loader2 size={32} color="var(--accent-primary)" style={{ margin: '0 auto 12px', animation: 'spin 1s linear infinite' }} />
                  <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>
                    Tracing Blockchain Counterparties...
                  </h3>
                  <p style={{ fontSize: 11.5, color: 'var(--text-tertiary)', maxWidth: 380, margin: '0 auto' }}>
                    Querying ledger endpoints, discovering VASP touchpoints, and calculating suspicion points.
                  </p>
                </div>
              ) : (
                <div style={{ padding: '40px 20px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                  <Shield size={28} color="var(--accent-primary)" style={{ margin: '0 auto 8px' }} />
                  <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 3 }}>
                    Multi-Hop Forensic Graph
                  </h3>
                  <p style={{ fontSize: 11.5, maxWidth: 380, margin: '0 auto', lineHeight: 1.4 }}>
                    Enter a wallet address above to trace fund movements across hops, attribute VASP endpoints, and calculate suspicion points.
                  </p>
                </div>
              )}
            </>
          )}

          {/* Tab 2: Suspicion Points View */}
          {activeTab === 'suspicion' && (
            <SuspicionPointsView
              riskAssessment={riskAssessment}
              wallet={analysisData?.wallet}
            />
          )}

          {/* Tab 3: Investigation Playbook & Next Steps */}
          {activeTab === 'investigate' && (
            <InvestigationGuideView
              investigationData={investigationDossier}
              wallet={analysisData?.wallet}
            />
          )}

          {/* Tab 4: Forensic Dossier & Report */}
          {activeTab === 'report' && (
            <ForensicReportView
              reportData={investigationDossier}
              wallet={analysisData?.wallet}
              graphData={{ nodes: graphNodes, edges: graphEdges }}
              riskAssessment={riskAssessment}
              currentChain={currentChain}
              currentAsset={currentAsset}
            />
          )}
        </div>
      </main>

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
