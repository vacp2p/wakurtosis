import typer
import networkx as nx
import json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import sys


def read_network(json_fname, ith=0):
    with open(json_fname) as f:
        json_graphs, G = json.load(f), nx.empty_graph()
        try:
            js_graph = json_graphs[sorted(list(json_graphs))[ith]]
        except IndexError:
            print(f'read_network: not enough keys {ith}')
            sys.exit()
        for src in js_graph.keys():
            for dst  in js_graph[src]:
                G.add_edge(src, dst)
    return G


def plot_network(G, fanout):
        fig, axes = plt.subplots(1, 2, layout='constrained')
        fig.set_figwidth(12)
        fig.set_figheight(10)
        n, e, s = len(G.nodes), len(G.edges), 0

        for i in G.nodes:
            s += G.degree[i]
        avg = 2 * e/n

        if fanout == -1:
            tag = 'discv5'
            ofname = 'observed-network-discv5.png'
        else:
            tag = f'fanout={fanout}'
            ofname = f'observed-network-{fanout}fanout.png'

        axes[0].set_title(f'The Generated Network: num-nodes = {n}, avg degree = {avg:.2f}')
        nx.draw(G, ax=axes[0], pos=nx.kamada_kawai_layout(G), with_labels=True)
        degree_sequence = sorted((d for n, d in G.degree()), reverse=True)
        deg, cnt = *np.unique(degree_sequence, return_counts=True),
        normalised_cnt =  cnt/np.array(n)
        axes[1].bar(deg, normalised_cnt, align='center',
            width=0.9975, edgecolor='k', facecolor='green', alpha=0.5)
        axes[1].set_xticks(range(max(degree_sequence)+1))
        axes[1].set_title(f'Normalised Degree Histogram: {tag}')
        axes[1].set_xlabel("Degree")
        axes[1].set_ylabel("Fraction of Nodes")
        plt.savefig(f'{ofname}', format="png", bbox_inches="tight")
        plt.show()


def main(ctx: typer.Context,
         network_data_file: Path = typer.Option("observed_network.json",
             exists=True, file_okay=True, dir_okay=False, readable=True,
             help="Set network file"),
         fanout : int = typer.Option(6,
             help="Set the network fanout"),
         ith : int = typer.Option(0,
             help="Set the network fanout")):
    G = read_network(network_data_file, ith)
    plot_network(G, fanout)


if __name__ == "__main__":
    typer.run(main)
