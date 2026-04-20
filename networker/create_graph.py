import networkx as nx
import os
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from gamuLogger import Logger

Logger.set_module("create_graph")

from .standardizer import lowercase, capitalize_all_words

# Couleurs pour le réseau signé
COLOR_POSITIVE = "#2196F3"   # bleu  → relation positive
COLOR_NEGATIVE = "#F44336"   # rouge → relation négative
COLOR_NEUTRAL  = "#9E9E9E"   # gris  → relation neutre


def _build_names_attr(person: list[str]) -> str:
    """Construit l'attribut 'names' du nœud, dédupliqué et trié."""
    seen: set[str] = set()
    ordered: list[str] = []
    for raw in person:
        n = capitalize_all_words(raw)
        if n and n not in seen:
            seen.add(n)
            ordered.append(n)
    ordered.sort(key=lambda n: len(n.split()), reverse=True)
    return ";".join(ordered)


def create_graph(
    persons: list[list[str]],
    links: list[tuple],
) -> nx.Graph:
    """
    Crée un graphe NetworkX.

    links peut être :
      (a, b, weight)            → réseau non signé
      (a, b, weight, polarity)  → réseau signé

    Attributs des arêtes :
      weight   : nombre de co-occurrences
      polarity : +1, -1 ou 0 (présent uniquement si fourni)
      color    : couleur selon la polarité (pour la visualisation)
    """
    G = nx.Graph()

    for person in persons:
        node_id    = person[0]
        names_attr = _build_names_attr(person)
        G.add_node(node_id, names=names_attr)
        Logger.debug(f"Node '{node_id}' names='{names_attr}'")

    for link in links:
        if len(link) == 4:
            person1, person2, weight, polarity = link
        elif len(link) == 3:
            person1, person2, weight = link
            polarity = None
        else:
            raise ValueError(f"Lien invalide : {link}")

        canon1 = next((p[0] for p in persons if person1 in p), None)
        canon2 = next((p[0] for p in persons if person2 in p), None)

        if canon1 is None:
            raise ValueError(f"Personnage '{person1}' introuvable dans persons")
        if canon2 is None:
            raise ValueError(f"Personnage '{person2}' introuvable dans persons")
        if canon1 == canon2:
            continue

        if G.has_edge(canon1, canon2):
            G[canon1][canon2]['weight'] += weight
            # Mise à jour de la polarité : on garde la plus fréquente
            if polarity is not None:
                old_pol = G[canon1][canon2].get('polarity', 0)
                # Simple vote : on somme les polarités
                new_pol_sum = G[canon1][canon2].get('_pol_sum', old_pol) + polarity
                G[canon1][canon2]['_pol_sum'] = new_pol_sum
                G[canon1][canon2]['polarity'] = (
                    1 if new_pol_sum > 0 else (-1 if new_pol_sum < 0 else 0)
                )
        else:
            attrs = {'weight': weight}
            if polarity is not None:
                attrs['polarity']  = polarity
                attrs['_pol_sum']  = polarity
                attrs['color']     = (
                    COLOR_POSITIVE if polarity > 0
                    else COLOR_NEGATIVE if polarity < 0
                    else COLOR_NEUTRAL
                )
            G.add_edge(canon1, canon2, **attrs)

    # Nettoyer l'attribut interne _pol_sum
    for u, v in G.edges():
        G[u][v].pop('_pol_sum', None)

    return G


def save_img_graph(
    graph: nx.Graph,
    output_path: str,
    show_vertices_labels: bool = False,
    signed: bool = True,
):
    """
    Sauvegarde le graphe en image.
    Si signed=True, colorie les arêtes selon leur polarité.
    """
    plt.figure(figsize=(50, 40))
    pos     = nx.spring_layout(graph, k=0.5, iterations=50)
    weights = nx.get_edge_attributes(graph, 'weight')

    if signed and nx.get_edge_attributes(graph, 'polarity'):
        # Séparer les arêtes par polarité
        pos_edges     = [(u, v) for u, v, d in graph.edges(data=True) if d.get('polarity', 0) > 0]
        neg_edges     = [(u, v) for u, v, d in graph.edges(data=True) if d.get('polarity', 0) < 0]
        neutral_edges = [(u, v) for u, v, d in graph.edges(data=True) if d.get('polarity', 0) == 0]

        def widths(edges):
            return [weights.get(e, weights.get((e[1], e[0]), 1)) for e in edges]

        nx.draw_networkx_nodes(graph, pos, node_color='lightblue', node_size=5000)
        nx.draw_networkx_labels(graph, pos, font_size=20)
        nx.draw_networkx_edges(graph, pos, edgelist=pos_edges,
                               edge_color=COLOR_POSITIVE, width=widths(pos_edges), alpha=0.8)
        nx.draw_networkx_edges(graph, pos, edgelist=neg_edges,
                               edge_color=COLOR_NEGATIVE, width=widths(neg_edges), alpha=0.8)
        nx.draw_networkx_edges(graph, pos, edgelist=neutral_edges,
                               edge_color=COLOR_NEUTRAL, width=widths(neutral_edges), alpha=0.5)

        # Légende
        legend = [
            mpatches.Patch(color=COLOR_POSITIVE, label='Relation positive'),
            mpatches.Patch(color=COLOR_NEGATIVE, label='Relation négative'),
            mpatches.Patch(color=COLOR_NEUTRAL,  label='Relation neutre'),
        ]
        plt.legend(handles=legend, loc='upper left', fontsize=20)
    else:
        edge_widths = [weights.get(e, 1) for e in graph.edges()]
        nx.draw(graph, pos, with_labels=True, node_color='lightblue',
                edge_color='gray', node_size=5000, font_size=20, width=edge_widths)

    if show_vertices_labels:
        nx.draw_networkx_edge_labels(graph, pos, edge_labels=weights, font_size=15)

    plt.title("Réseau de personnages (réseau signé)" if signed else "Réseau de personnages")
    plt.savefig(output_path)
    plt.close()
    Logger.info(f"Graphe sauvegardé : {output_path}")


def to_graphml(graph: nx.Graph, pretty: bool = True) -> str:
    sep = "\n" if pretty else ""
    return sep.join(nx.generate_graphml(graph, prettyprint=pretty))