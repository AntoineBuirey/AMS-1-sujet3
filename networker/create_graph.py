import networkx as nx
import os
import matplotlib.pyplot as plt
from gamuLogger import Logger

Logger.set_module("create_graph")

from .standardizer import lowercase

def create_graph(persons : list[list[str]], links : list[tuple[str, str, int]]) -> nx.Graph:
    """
    Create a graph from a list of persons.
    Return the graph in graphml format.
    persons: list of [name, alias1, alias2, ...]
    links: list of (person1, person2, weight)
    each person in links must be in persons
    """
    G = nx.Graph()
    for person in persons:
        aliases = ";".join(person)
        id = person[0].replace(" ", "_")
        G.add_node(id, names=aliases)
        
    for person1, person2, weight in links:
        # find the canonical names
        canon1 = next((p[0].replace(" ", "_") for p in persons if person1 in p), None)
        canon2 = next((p[0].replace(" ", "_") for p in persons if person2 in p), None)
        if canon1 is None:
            raise ValueError(f"Person {person1} not found in persons list")
        if canon2 is None:
            raise ValueError(f"Person {person2} not found in persons list")
        if G.has_edge(canon1, canon2):
            raise ValueError(f"Edge between {canon1} and {canon2} already exists")
        else:
            G.add_edge(canon1, canon2, weight=weight)

    return G


def save_img_graph(graph: nx.Graph, output_path: str, show_vertices_labels: bool = False):
    plt.figure(figsize=(50, 40))
    pos = nx.spring_layout(graph, k=0.5, iterations=50)
    weights = nx.get_edge_attributes(graph, 'weight')
    
    # Get edge weights as a list for thickness
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
    """
    Convert a networkx graph to graphml format.
    Return the graphml as a string.
    """
    sep = "\n" if pretty else ""
    graphml = sep.join(nx.generate_graphml(graph, prettyprint=pretty))
    return graphml
    

if __name__ == "__main__":
    import json
    ############################## Data loading
    with open("output/chapter_1.aliases.json", "r", encoding="utf-8") as f:
        persons = json.load(f)
    with open("output/chapter_1_links_aggregated.csv", "r", encoding="utf-8") as f:
        lines = f.readlines()[1:]  # skip header
    links = []
    for line in lines:
        parts = line.strip().split(",")
        person1 = parts[0]
        person2 = parts[1]
        weight = int(parts[2])
        links.append((person1, person2, weight))
        
    # lowercase all names
    persons = lowercase(persons)
    links = lowercase(links)
    
    ############################### Graph creation
    
    graphml = create_graph(persons, links)
    
    ############################### Save graph image
    
    os.makedirs("./output/graphs/", exist_ok=True)
    save_img_graph(graphml, "./output/graphs/person_graph.png")