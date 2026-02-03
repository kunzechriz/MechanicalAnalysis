from typing import List, Dict

def check_connectivity(active_nodes: List, fixed_nodes: List, adj_list: Dict[int, List[int]]) -> bool:
    """
    Prüft mittels Graphen-Algorithmus, ob die Struktur
    noch zusammenhängend ist.
    
    Wir starten bei einem Lagerknoten und müssen von dort aus ALLE anderen
    aktiven Knoten erreichen können. Wenn das gelingt, ist die Struktur intakt.
    """
    if not active_nodes or not fixed_nodes:
        return False

    start_node_id = fixed_nodes[0].id
    visited = {start_node_id}
    queue = [start_node_id]

    idx = 0
    while idx < len(queue):
        curr = queue[idx]
        idx += 1
        for neighbor in adj_list.get(curr, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

    return len(visited) == len(active_nodes)

