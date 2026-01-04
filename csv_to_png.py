"""
Load graphs from a csv using the format:
ID,graphml
paf0,"<graphml xmlns=""http://graphml.graphdrawing.org/xmlns"" xmlns:xsi=""http://www.w3.org/2001/XMLSchema-instance"" xsi:schemaLocation=""http://graphml.graphdrawing.org/xmlns http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd"">  <key id=""d0"" for=""node"" attr.name=""names"" attr.type=""string"" />  <graph edgedefault=""undirected"">    <node id=""Hari Seldon"">      <data key=""d0"">Hari Seldon</data>    </node>    <node id=""Cl&#233;on"">      <data key=""d0"">Cl&#233;on</data>    </node>    <node id=""Eto Demerzel"">      <data key=""d0"">Eto Demerzel</data>    </node>    <node id=""Sire"">      <data key=""d0"">Sire</data>    </node>    <node id=""Alban Wellis"">      <data key=""d0"">Alban Wellis</data>    </node>    <node id=""Empereur"">      <data key=""d0"">Empereur</data>    </node>    <node id=""Trantor"">      <data key=""d0"">Trantor</data>    </node>    <node id=""Hummin"">      <data key=""d0"">Hummin</data>    </node>  </graph></graphml>"
paf1,"<graphml xmlns=""http://graphml.graphdrawing.org/xmlns"" xmlns:xsi=""http://www.w3.org/2001/XMLSchema-instance"" xsi:schemaLocation=""http://graphml.graphdrawing.org/xmlns http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd"">  <key id=""d0"" for=""node"" attr.name=""names"" attr.type=""string"" />  <graph edgedefault=""undirected"">    <node id=""Cl&#233;on Ier"">      <data key=""d0"">Cl&#233;on Ier</data>    </node>    <node id=""Hari Seldon"">      <data key=""d0"">Hari Seldon</data>    </node>    <node id=""Alem"">      <data key=""d0"">Alem</data>    </node>    <node id=""Hummin"">      <data key=""d0"">Hummin</data>    </node>    <node id=""Trantorien"">      <data key=""d0"">Trantorien</data>    </node>    <node id=""H&#233;liconien"">      <data key=""d0"">H&#233;liconien</data>    </node>    <node id=""Anacr&#233;on"">      <data key=""d0"">Anacr&#233;on</data>    </node>    <node id=""Demerzel"">      <data key=""d0"">Demerzel</data>    </node>    <node id=""Trantor"">      <data key=""d0"">Trantor</data>    </node>  </graph></graphml>"
...

and save them as PNG files (the name will be the ID from the csv).
"""
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import os

def csv_to_png(csv_file):
    # Load the CSV file
    df = pd.read_csv(csv_file)

    for index, row in df.iterrows():
        graph_id = row['ID']
        graphml_data = row['graphml']

        # Load the graph from the GraphML string
        graph = nx.parse_graphml(graphml_data)

        # Draw the graph
        plt.figure(figsize=(8, 6))
        pos = nx.spring_layout(graph)
        nx.draw(graph, pos, with_labels=True, node_color='lightblue', edge_color='gray', node_size=500, font_size=10)
        
        # Save the graph as a PNG file
        plt.savefig(f"test/{graph_id}.png")
        plt.close()
        
        # also save the graphml for reference
        with open(f"test/{graph_id}.xml", "w") as f:
            f.write(graphml_data)

if __name__ == "__main__":
    os.makedirs("test", exist_ok=True)
    csv_to_png("EvanMASSOL_MartinGERIS.csv")