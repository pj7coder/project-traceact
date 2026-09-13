from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from backend.schemas.wallet import (
    BlockchainNetwork,
    TraceDirection,
    FundPath,
    TraceNode,
    TraceEdge,
)


class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class EntityType(str, Enum):
    CENTRALIZED_EXCHANGE = "centralized_exchange"
    VASP = "VASP"
    CUSTODIAL_WALLET = "custodial_wallet"
    BRIDGE = "bridge"
    MIXER = "mixer"
    CONTRACT = "contract"
    DEFI_PROTOCOL = "DeFi_protocol"
    UNKNOWN = "unknown"


class SystemLogicProfile(str, Enum):
    BALANCED = "balanced"
    STRICT = "strict"
    FRAUD_SYNDICATE = "fraud_syndicate"
    RELAXED = "relaxed"
    CUSTOM = "custom"


class SystemLogicConfig(BaseModel):
    profile: Optional[str] = Field(default="balanced", description="Forensic Profile: 'balanced' | 'strict' | 'fraud_syndicate' | 'relaxed' | 'custom'")
    sensitivityMultiplier: Optional[float] = Field(default=1.0, ge=0.2, le=3.0, description="Multiplier on calculated suspicion score")
    largeTransferThreshold: Optional[float] = Field(default=None, description="Custom large transfer threshold in native asset units (BTC/ETH/TRX/SOL)")
    burstVelocityThreshold: Optional[int] = Field(default=10, ge=3, le=100, description="Transaction burst velocity count threshold")
    rapidMovementRetentionRatio: Optional[float] = Field(default=0.5, ge=0.1, le=0.99, description="Minimum forwarding ratio to qualify as rapid movement")
    enableMixerBooster: Optional[bool] = Field(default=True, description="Elevate score to CRITICAL if mixer or CoinJoin detected")
    enableVaspDampener: Optional[bool] = Field(default=True, description="Dampen suspicion score when transactions involve compliant VASPs")
    disabledRuleIds: List[str] = Field(default_factory=list, description="List of rule IDs disabled by investigator")
    customRuleWeights: Dict[str, int] = Field(default_factory=dict, description="Custom rule weight overrides")


class AttributionRequest(BaseModel):
    chain: BlockchainNetwork = Field(default=BlockchainNetwork.ETHEREUM, description="Blockchain network")
    address: str = Field(..., description="Suspect root wallet address to investigate")
    maxDepth: int = Field(default=3, ge=1, le=5, description="Maximum BFS traversal depth")
    direction: TraceDirection = Field(default=TraceDirection.BOTH, description="Fund tracing direction")
    minimumTransferValue: Optional[str] = Field(default="0.0", description="Minimum transfer filter in ETH")
    startTimestamp: Optional[str] = Field(default=None, description="Start ISO timestamp")
    endTimestamp: Optional[str] = Field(default=None, description="End ISO timestamp")
    maxNodes: int = Field(default=50, ge=5, le=100, description="Node count safeguard threshold")
    systemLogic: Optional[SystemLogicConfig] = Field(default=None, description="Investigator-tuned forensic heuristics and system logic filter")


class EvaluateHeuristicsRequest(BaseModel):
    address: str = Field(..., description="Target wallet address")
    chain: BlockchainNetwork = Field(default=BlockchainNetwork.ETHEREUM, description="Blockchain network")
    systemLogic: Optional[SystemLogicConfig] = Field(default=None, description="Investigator-tuned system logic filter")
    multihopNodes: Optional[List[Dict[str, Any]]] = Field(default=None, description="Optional multi-hop graph nodes context")


class AttributionEvidenceItem(BaseModel):
    type: str = Field(..., description="'verified_address_match' | 'transaction_path' | 'source_verification' | 'counterparty_clustering'")
    title: str
    description: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VaspCandidate(BaseModel):
    entityName: str
    entityType: str
    address: str
    hopDistance: int
    confidence: ConfidenceLevel
    source: str
    sourceUrl: Optional[str] = ""
    totalObservedTransfer: str
    path: List[str]
    transactionHashes: List[str] = Field(default_factory=list)
    isDirectDepositEndpoint: bool = False
    endpointClassification: str = "Exchange-attributed address"
    verified: bool = True
    firstSeen: Optional[str] = None
    lastSeen: Optional[str] = None


class NearestVaspResult(BaseModel):
    name: str
    address: str
    type: str
    hopDistance: int
    confidence: ConfidenceLevel
    source: str
    sourceUrl: Optional[str] = ""
    path: List[str]
    totalTransferred: str
    isDirectDepositEndpoint: bool = False
    endpointClassification: str = "Exchange-attributed address"
    transactionHashes: List[str] = Field(default_factory=list)


class TraceSummary(BaseModel):
    nodes: int
    transactions: int
    maxDepth: int
    direction: str
    executionTimeSeconds: float


class AttributionGraph(BaseModel):
    nodes: List[TraceNode]
    edges: List[TraceEdge]


class AttributionResponse(BaseModel):
    rootWallet: str
    chain: str = "ethereum"
    traceSummary: TraceSummary
    nearestVasp: Optional[NearestVaspResult] = None
    vaspCandidates: List[VaspCandidate] = Field(default_factory=list)
    paths: List[FundPath] = Field(default_factory=list)
    graph: AttributionGraph
    evidence: List[AttributionEvidenceItem] = Field(default_factory=list)
    investigationSummary: str
    limitations: List[str] = Field(default_factory=list)
    riskAssessment: Optional[Dict[str, Any]] = None


# -------------------------------------------------------------
# Forensic Report & SAHYOG Portal Models
# -------------------------------------------------------------

class ReportGenerateRequest(BaseModel):
    caseId: Optional[str] = None
    targetAddress: str
    chain: BlockchainNetwork = BlockchainNetwork.ETHEREUM
    investigatorId: Optional[str] = "LEA-I4C-4092"
    investigatorName: Optional[str] = "Cyber Forensics Officer"
    maxDepth: int = 3


class ReportInfographics(BaseModel):
    riskScoreGauge: Dict[str, Any]
    hopDistribution: List[Dict[str, Any]]
    volumeFlow: List[Dict[str, Any]]
    categoryBreakdown: List[Dict[str, Any]]


class InvestigationReportResponse(BaseModel):
    reportId: str
    caseId: str
    targetAddress: str
    chain: str
    generatedAt: str
    llmModel: str
    executiveSummary: str
    sahyogNoticeDraft: str
    nearestVaspName: Optional[str] = None
    nearestVaspAddress: Optional[str] = None
    hopDistance: int = 0
    suspicionScore: int = 0
    riskLevel: str = "LOW"
    infographics: ReportInfographics
    evidenceChain: List[Dict[str, Any]] = Field(default_factory=list)
    sha256Checksum: str
    fullReportMarkdown: str
    sections: Optional[Dict[str, Any]] = Field(default=None, description="Structured 16-section forensic report object")


class InvestigationDossierResponse(BaseModel):
    caseId: str
    targetAddress: str
    chain: str
    status: str = "COMPLETED"
    generatedAt: str
    taintAccounting: Dict[str, Any]
    vaspActionabilityRankings: List[Dict[str, Any]]
    minimumInterventionSet: Dict[str, Any]
    attributionChallenges: List[Dict[str, Any]]
    unknownVaspCandidates: List[Dict[str, Any]]
    serviceClusters: List[Dict[str, Any]]
    evidenceGaps: List[Dict[str, Any]]
    blindSpots: List[str]
    nextActions: List[Dict[str, Any]]
    timeline: List[Dict[str, Any]]
    caseCoverage: Dict[str, Any]
    report: Optional[InvestigationReportResponse] = None
    attribution: Optional[AttributionResponse] = None


