import networkx as nx
import pandas as pd


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
        with open("./test.xml", "w") as f:
            f.write(graphml)
        exit(0)

df = pd.DataFrame(df_dict)
df.set_index("ID", inplace=True)
df.to_csv("./my_submission.csv")
