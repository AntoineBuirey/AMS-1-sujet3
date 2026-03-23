import networkx as nx
import os
import matplotlib.pyplot as plt
from gamuLogger import Logger

Logger.set_module("create_graph")

from .standardizer import lowercase, capitalize_all_words


def _build_names_attr(person: list[str]) -> str:
    """
    Construit l'attribut 'names' d'un nœud à partir du groupe d'alias.

    Règles calées sur la métrique Kaggle :
    - Précision pénalise les noms en trop : on déduplique après normalisation
      de casse pour éviter "Hari Seldon" et "hari seldon" comptant comme
      deux noms différents.
    - Rappel est binaire : inclure toutes les formes uniques détectées dans
      le texte maximise la probabilité d'intersection avec le ground truth.
    - Les noms sont triés par longueur décroissante (nom composé en premier)
      pour faciliter l'alignement Jaccard utilisé pour les arêtes.

    Format de sortie : "Hari Seldon;Seldon;Hari" (séparateur ';' imposé par le sujet)
    """
    seen: set[str] = set()
    ordered: list[str] = []
    for raw_name in person:
        normalized = capitalize_all_words(raw_name)
        if normalized and normalized not in seen:
            seen.add(normalized)
            ordered.append(normalized)
    # Trier par longueur décroissante : le nom le plus complet en premier.
    ordered.sort(key=lambda n: len(n.split()), reverse=True)
    return ";".join(ordered)


def create_graph(persons: list[list[str]], links: list[tuple[str, str, int]]) -> nx.Graph:
    """
    Crée un graphe NetworkX à partir des groupes d'alias et des liens.

    persons : liste de groupes [nom_canonique, alias1, alias2, ...]
              person[0] est l'ID du nœud (doit être déterministe).
    links   : liste de (personne1, personne2, poids)
              chaque nom doit être présent dans persons.
    """
    G = nx.Graph()

    for person in persons:
        node_id = person[0]
        names_attr = _build_names_attr(person)
        G.add_node(node_id, names=names_attr)
        Logger.debug(f"Node '{node_id}' names='{names_attr}'")

    for person1, person2, weight in links:
        Logger.debug(f"Finding canonical names for '{person1}' and '{person2}'")
        canon1 = next((p[0] for p in persons if person1 in p), None)
        canon2 = next((p[0] for p in persons if person2 in p), None)
        if canon1 is None:
            Logger.debug(f"Persons list: {persons}")
            raise ValueError(f"Person '{person1}' not found in persons list")
        if canon2 is None:
            Logger.debug(f"Persons list: {persons}")
            raise ValueError(f"Person '{person2}' not found in persons list")
        if canon1 == canon2:
            continue  # self-loop : ignoré
        if G.has_edge(canon1, canon2):
            G[canon1][canon2]['weight'] += weight
        elif canon1 == canon2:
            # skip self-loops
            Logger.debug(f"Skipping self-loop for {canon1}")
        else:
            G.add_edge(canon1, canon2, weight=weight)

    return G


def save_img_graph(graph: nx.Graph, output_path: str, show_vertices_labels: bool = False):
    plt.figure(figsize=(50, 40))
    pos = nx.spring_layout(graph, k=0.5, iterations=50)
    weights = nx.get_edge_attributes(graph, 'weight')
    edge_widths = [weights[edge] for edge in graph.edges()]
    nx.draw(graph, pos, with_labels=True, node_color='lightblue', edge_color='gray',
            node_size=5000, font_size=20, width=edge_widths)
    if show_vertices_labels:
        nx.draw_networkx_edge_labels(graph, pos, edge_labels=weights, font_size=15)
    plt.title("Character Graph")
    plt.savefig(output_path)
    plt.close()
    Logger.info(f"Graph image saved to {output_path}")


def to_graphml(graph: nx.Graph, pretty: bool = True) -> str:
    sep = "\n" if pretty else ""
    return sep.join(nx.generate_graphml(graph, prettyprint=pretty))


if __name__ == "__main__":
    import json
    with open("output/chapter_1.aliases.json", "r", encoding="utf-8") as f:
        persons = json.load(f)
    with open("output/chapter_1_links_aggregated.csv", "r", encoding="utf-8") as f:
        lines = f.readlines()[1:]
    links = []
    for line in lines:
        parts = line.strip().split(",")
        links.append((parts[0], parts[1], int(parts[2])))
    persons = lowercase(persons)
    links = lowercase(links)
    graphml = create_graph(persons, links)
    os.makedirs("./output/graphs/", exist_ok=True)
    save_img_graph(graphml, "./output/graphs/person_graph.png")