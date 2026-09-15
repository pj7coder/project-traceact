from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class BlockchainNetwork(str, Enum):
    ETHEREUM = "ethereum"
    BITCOIN = "bitcoin"
    TRON = "tron"
    SOLANA = "solana"
    BNB = "bnb"
    POLYGON = "polygon"


class TransactionDirection(str, Enum):
    INCOMING = "incoming"
    OUTGOING = "outgoing"
    SELF = "self"


class ConnectedWalletDirection(str, Enum):
    INCOMING = "incoming"
    OUTGOING = "outgoing"
    BIDIRECTIONAL = "bidirectional"


class TraceDirection(str, Enum):
    OUTGOING = "outgoing"
    INCOMING = "incoming"
    BOTH = "both"


class RiskLevel(str, Enum):
    CLEAN = "CLEAN"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# -------------------------------------------------------------
# Common Normalized Schemas
# -------------------------------------------------------------

class AnalyzeWalletRequest(BaseModel):
    chain: BlockchainNetwork = Field(default=BlockchainNetwork.ETHEREUM, description="Blockchain network to query")
    address: str = Field(..., description="Target blockchain wallet address")


class WalletOverview(BaseModel):
    address: str
    chain: str = "ethereum"
    balance: str
    balanceWei: str = "0"
    balanceRaw: Optional[str] = "0"
    asset: str = "ETH"
    transactionCount: int = 0
    incomingCount: int = 0
    outgoingCount: int = 0
    uniqueConnectedWallets: int = 0
    firstSeen: Optional[str] = None
    lastSeen: Optional[str] = None
    riskScore: Optional[int] = 0
    riskLevel: Optional[str] = "LOW"
    riskAssessment: Optional[Dict[str, Any]] = None
    triggeredRules: List[Dict[str, Any]] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    globalSearchCount: Optional[int] = 1
    appearanceCountInGraphs: Optional[int] = 0


class NormalizedTransaction(BaseModel):
    txHash: str
    chain: str = "ethereum"
    fromAddress: str
    toAddress: Optional[str] = None
    value: str
    valueWei: str = "0"
    valueRaw: Optional[str] = "0"
    asset: str = "ETH"
    timestamp: str
    blockNumber: int = 0
    status: str = "confirmed"
    direction: TransactionDirection
    gasUsed: Optional[str] = "0"
    fee: Optional[str] = "0"
    feeWei: Optional[str] = "0"
    feeRaw: Optional[str] = "0"
    txType: Optional[str] = "native_transfer"


class ConnectedWallet(BaseModel):
    address: str
    direction: ConnectedWalletDirection
    transactionCount: int
    totalAmount: str
    totalAmountWei: str = "0"
    totalAmountRaw: Optional[str] = "0"
    asset: str = "ETH"
    incomingTxCount: int = 0
    outgoingTxCount: int = 0
    totalSentToInvestigated: str = "0"
    totalReceivedFromInvestigated: str = "0"
    firstInteractionTimestamp: Optional[str] = None
    lastInteractionTimestamp: Optional[str] = None
    riskScore: Optional[int] = 0
    riskLevel: Optional[str] = "LOW"
    nodeColor: Optional[str] = None
    tags: List[str] = Field(default_factory=list)



class GraphNodeData(BaseModel):
    label: str
    fullAddress: str
    nodeType: str  # "investigated" | "connected" | "known_entity"
    role: Optional[str] = None  # "investigated" | "incoming" | "outgoing" | "bidirectional"
    txCount: Optional[int] = 0
    totalVolume: Optional[str] = "0"
    balance: Optional[str] = None
    asset: Optional[str] = "ETH"
    depth: Optional[int] = 0
    entityName: Optional[str] = None
    entityType: Optional[str] = None
    riskScore: Optional[int] = 0
    riskLevel: Optional[str] = "LOW"
    nodeColor: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    globalSearchCount: Optional[int] = 1
    appearanceCountInGraphs: Optional[int] = 0
    isMonitored: Optional[bool] = False


class GraphNode(BaseModel):
    id: str
    type: str = "customWalletNode"
    data: GraphNodeData
    position: Dict[str, float] = Field(default_factory=lambda: {"x": 0.0, "y": 0.0})


class GraphEdgeData(BaseModel):
    transactionCount: int
    totalTransferred: str
    asset: str = "ETH"
    hopDepth: Optional[int] = 1


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    label: Optional[str] = None
    data: Optional[GraphEdgeData] = None
    animated: bool = False


class GraphData(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]


class WalletAnalysisResponse(BaseModel):
    wallet: WalletOverview
    transactions: List[NormalizedTransaction]
    connectedWallets: List[ConnectedWallet]
    graph: GraphData
    riskAssessment: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# -------------------------------------------------------------
# Multi-Hop Blockchain Tracing Schemas
# -------------------------------------------------------------

class TraceFundsRequest(BaseModel):
    chain: BlockchainNetwork = Field(default=BlockchainNetwork.ETHEREUM, description="Blockchain network")
    address: str = Field(..., description="Suspect root wallet address to trace")
    maxDepth: int = Field(default=3, ge=1, le=5, description="Maximum BFS traversal depth (hops)")
    direction: TraceDirection = Field(default=TraceDirection.BOTH, description="Tracing direction: outgoing, incoming, or both")
    minimumTransferValue: Optional[str] = Field(default="0.0", description="Minimum transfer threshold (filters dust)")
    startTimestamp: Optional[str] = Field(default=None, description="ISO timestamp start filter")
    endTimestamp: Optional[str] = Field(default=None, description="ISO timestamp end filter")
    maxNodes: int = Field(default=50, ge=5, le=200, description="Prototype traversal safeguard: maximum total nodes analyzed")
    maxTransactionsPerWallet: int = Field(default=50, ge=5, le=100, description="Maximum transactions fetched per wallet hop")


class TraceNode(BaseModel):
    address: str
    depth: int = Field(..., description="Hop depth relative to suspect root wallet (0 = root)")
    type: str = Field(..., description="'suspect' | 'wallet' | 'known_entity'")
    chain: Optional[str] = "ethereum"
    entityName: Optional[str] = None
    entityType: Optional[str] = None
    attributionSource: Optional[str] = None
    confidence: Optional[str] = None
    totalReceivedFromParent: Optional[str] = "0"
    totalSent: Optional[str] = "0"
    transactionCount: Optional[int] = 0
    balanceEth: Optional[str] = None
    firstSeen: Optional[str] = None
    lastSeen: Optional[str] = None
    # Risk & Tagging enhancements
    riskScore: Optional[int] = 0
    riskLevel: Optional[str] = "LOW"
    nodeColor: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    globalSearchCount: Optional[int] = 1
    appearanceCountInGraphs: Optional[int] = 0
    isMonitored: Optional[bool] = False


class TraceEdge(BaseModel):
    source: str
    target: str
    totalValue: str
    totalValueWei: Optional[str] = "0"
    totalValueRaw: Optional[str] = "0"
    asset: Optional[str] = "ETH"
    transactionCount: int
    hopDepth: int
    firstSeen: Optional[str] = None
    lastSeen: Optional[str] = None
    transactionHashes: List[str] = Field(default_factory=list)


class FundPathStep(BaseModel):
    fromAddress: str
    toAddress: str
    amount: str
    amountWei: Optional[str] = "0"
    amountRaw: Optional[str] = "0"
    asset: Optional[str] = "ETH"
    transactionCount: int = 1
    hopDepth: int
    txHash: Optional[str] = None



class FundPath(BaseModel):
    path: List[str] = Field(..., description="Sequential list of wallet addresses in the path")
    hopCount: int
    totalVolume: str
    asset: Optional[str] = "ETH"
    steps: List[FundPathStep] = Field(default_factory=list)
    terminatesAtEntity: Optional[str] = None
    entityName: Optional[str] = None


class NearestEntityResult(BaseModel):
    name: str
    address: str
    entityType: str
    attributionSource: Optional[str] = None
    confidence: Optional[str] = None
    hopDistance: int
    path: List[str]
    totalTransferred: Optional[str] = "0"
    asset: Optional[str] = "ETH"


class TraceFundsResponse(BaseModel):
    rootWallet: str
    chain: str = "ethereum"
    maxDepth: int
    direction: str
    nodesAnalyzed: int
    transactionsAnalyzed: int
    nodes: List[TraceNode]
    edges: List[TraceEdge]
    paths: List[FundPath]
    nearestEntity: Optional[NearestEntityResult] = None
    traceIncomplete: bool = False
    reason: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# -------------------------------------------------------------
# Multi-Chain Auto-Detection & Normalization Schemas
# -------------------------------------------------------------

class ChainDetectionRequest(BaseModel):
    address: str = Field(..., description="Wallet address to analyze for chain determination")


class ChainDetectionResponse(BaseModel):
    address: str
    detectedChain: BlockchainNetwork
    confidence: str = "HIGH"
    formatName: str
    symbol: str
    suggestedAlternativeChains: List[BlockchainNetwork] = Field(default_factory=list)
    validationStatus: bool = True
    message: Optional[str] = None


# -------------------------------------------------------------
# Incremental Graph Branch Expansion Schemas
# -------------------------------------------------------------

class NodeExpansionRequest(BaseModel):
    chain: BlockchainNetwork = Field(default=BlockchainNetwork.ETHEREUM)
    targetAddress: str = Field(..., description="Node to expand branch from")
    caseId: Optional[str] = Field(default=None, description="Current investigation case ID")
    currentNodes: List[TraceNode] = Field(default_factory=list, description="Currently rendered graph nodes")
    currentEdges: List[TraceEdge] = Field(default_factory=list, description="Currently rendered graph edges")
    maxNewNodes: int = Field(default=10, ge=1, le=30, description="Max peers to attach to branch")


class NodeExpansionResponse(BaseModel):
    expandedAddress: str
    newNodesAdded: int
    newEdgesAdded: int
    nodes: List[TraceNode]
    edges: List[TraceEdge]
    message: str


# -------------------------------------------------------------
# Live Tracking & Alert Schemas
# -------------------------------------------------------------

class LiveTrackingToggleRequest(BaseModel):
    address: str
    chain: BlockchainNetwork = Field(default=BlockchainNetwork.ETHEREUM)
    email: Optional[str] = None
    enabled: bool = True


class MonitoredWalletItem(BaseModel):
    address: str
    chain: str
    investigatorId: str
    investigatorEmail: Optional[str] = None
    isActive: bool = True
    intervalMinutes: int = 60
    lastCheckedAt: Optional[str] = None
    nextCheckAt: Optional[str] = None
    lastKnownTxCount: int = 0
    lastKnownBalance: str = "0"
    alertsCount: int = 0
    alerts: List[Dict[str, Any]] = Field(default_factory=list)


class NotificationItem(BaseModel):
    id: str
    timestamp: str
    type: str  # "new_tx" | "vasp_hop" | "risk_spike" | "balance_change"
    title: str
    description: str
    address: str
    chain: str
    read: bool = False
    txHash: Optional[str] = None


# -------------------------------------------------------------
# Runtime System Settings Schemas
# -------------------------------------------------------------

class SystemSettingsModel(BaseModel):
    etherscanApiKey: Optional[str] = ""
    blockscoutBaseUrl: Optional[str] = "https://eth.blockscout.com/api/v2"
    blockstreamApiUrl: Optional[str] = "https://blockstream.info/api"
    trongridApiKey: Optional[str] = ""
    tronscanApiKey: Optional[str] = ""
    solanaRpcUrl: Optional[str] = "https://api.mainnet-beta.solana.com"
    mongodbUri: Optional[str] = "mongodb://localhost:27017/sih_forensics"
    ollamaHost: Optional[str] = "http://127.0.0.1:11434"
    ollamaModel: Optional[str] = "llama3.2:3b"
    emailNotificationsEnabled: bool = False
    smtpHost: Optional[str] = ""
    smtpPort: int = 587
    smtpUser: Optional[str] = ""
    smtpPassword: Optional[str] = ""
    alertEmailRecipient: Optional[str] = ""
    investigatorId: Optional[str] = "LEA-I4C-4092"
    investigatorName: Optional[str] = "Cyber Forensics Officer"
