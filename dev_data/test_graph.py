import networkx as nx
import pandas as pd
import os
import matplotlib.pyplot as plt

# (chapitres, code du livre)
books = [
    (list(range(0, 19)), "paf"),
    (list(range(0, 18)), "lca"),
]

df_dict = {"ID": [], "graphml": []}
for chapters, book_code in books:
    for chapter in chapters:
        G = nx.Graph()
        # Crée implicitement deux noeuds ("Hari" et "Dors"),
        # et ajoute un lien entre eux.
        G.add_edge("Hari", "Dors")
        # On ajoute les attributs "names"
        G.nodes["Hari"]["names"] = "Hari Seldon;Hari"
        G.nodes["Dors"]["names"] = "Dors;docteur Dors"
        df_dict["ID"].append("{}{}".format(book_code, chapter))
        graphml = "".join(nx.generate_graphml(G))
        df_dict["graphml"].append(graphml)
        
        # save to image
        plt.figure(figsize=(8, 6))
        pos = nx.spring_layout(G)
        nx.draw(G, pos, with_labels=True, node_color='lightblue', edge_color='gray', node_size=2000, font_size=15)
        plt.title("{}{}".format(book_code, chapter))
        os.makedirs("./output/graphs/", exist_ok=True)
        plt.savefig("./output/graphs/{}_{}.png".format(book_code, chapter))

df = pd.DataFrame(df_dict)
df.set_index("ID", inplace=True)
df.to_csv("./my_submission.csv")