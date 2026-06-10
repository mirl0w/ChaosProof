"""
NetworkX service dependency graph.
Replace build_service_graph() with real service discovery.
"""
import json
import networkx as nx


def build_service_graph() -> nx.DiGraph:
    """
    Swap this out for real discovery:
      - kubectl get pods --output json  (parse labels/annotations)
      - Consul catalog API
      - Istio ServiceEntry / DestinationRule resources
    """
    G = nx.DiGraph()
    edges = [
        ("api-gateway",       "order-service"),
        ("api-gateway",       "user-service"),
        ("order-service",     "inventory-service"),
        ("order-service",     "payment-service"),
        ("payment-service",   "fraud-service"),
        ("inventory-service", "warehouse-service"),
        ("warehouse-service", "shipping-service"),
    ]
    G.add_edges_from(edges)
    for node in G.nodes:
        G.nodes[node]["critical"] = G.in_degree(node) == 1
    return G


def get_graph_json() -> str:
    return json.dumps(nx.node_link_data(build_service_graph()))


def get_blast_radius(target: str) -> list[str]:
    G = build_service_graph()
    return list(nx.descendants(G, target)) if target in G else []


def is_safe_to_inject(target: str, max_blast: int = 5) -> tuple[bool, list[str]]:
    radius = get_blast_radius(target)
    return len(radius) <= max_blast, radius
