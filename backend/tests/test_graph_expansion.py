import pytest
from backend.schemas.wallet import (
    TraceNode,
    TraceEdge,
    NodeExpansionRequest,
    BlockchainNetwork,
)
from backend.services.graph_expansion_service import graph_expansion_service


@pytest.mark.anyio
async def test_node_branch_expansion_preserves_nodes():
    """Branch expansion adds new counterparty nodes while keeping original nodes intact."""
    root_node = TraceNode(address="0x1111111111111111111111111111111111111111", depth=0, type="suspect")
    inter_node = TraceNode(address="0x2222222222222222222222222222222222222222", depth=1, type="wallet")
    existing_edge = TraceEdge(
        source=root_node.address,
        target=inter_node.address,
        totalValue="1.0",
        transactionCount=1,
        hopDepth=1
    )

    req = NodeExpansionRequest(
        chain=BlockchainNetwork.ETHEREUM,
        targetAddress=inter_node.address,
        currentNodes=[root_node, inter_node],
        currentEdges=[existing_edge],
        maxNewNodes=5,
    )

    res = await graph_expansion_service.expand_branch(req)

    # Verifies old nodes are preserved
    addresses_in_graph = [n.address.lower() for n in res.nodes]
    assert root_node.address.lower() in addresses_in_graph
    assert inter_node.address.lower() in addresses_in_graph
    assert len(res.nodes) >= 2
