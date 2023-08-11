import typer
import networkx as nx
import json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import sys


def process_network(json_fname):
    avg_degrees = []
    with open(json_fname) as f:
        json_graphs, G = json.load(f), nx.empty_graph()
        for k in json_graphs.keys():
            js_graph = json_graphs[k]
            for src in js_graph.keys():
                for dst  in js_graph[src]:
                    G.add_edge(src, dst)
            avg_degrees.append(2 * len(G.edges)/len(G.nodes))
    return avg_degrees


def plot_network(avg_degrees, fanout):
        fig, axes = plt.subplots(1, 1, layout='constrained')
        fig.set_figwidth(12)
        fig.set_figheight(10)

        format="pdf"
        if fanout == -1:
            tag = 'discv5'
            ofname = f'avg-degree-discv5.{format}'
        else:
            tag = f'fanout={fanout}'
            ofname = f'avg-degree-{fanout}fanout.{format}'
        axes.plot(avg_degrees, marker='o', linestyle='dashed',)
        #axes.set_xticks(range(1, len(avg_degrees)))
        axes.set_title(f'Convergence of Average Degree - {tag}')
        axes.set_xlabel("Time (secs)")
        axes.set_ylabel("Average degree")
        plt.savefig(f'{ofname}', format=format, bbox_inches="tight")
        plt.show()


def main(ctx: typer.Context,
         network_data_file: Path = typer.Option("observed_network.json",
             exists=True, file_okay=True, dir_okay=False, readable=True,
             help="Set network file"),
         fanout : int = typer.Option(6,
             help="Set the network fanout")):
    plot_network(process_network(network_data_file), fanout)


if __name__ == "__main__":
    typer.run(main)
