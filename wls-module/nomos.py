import json
import matplotlib.pyplot as plt
import networkx as nx
from PIL import Image

# Histogram of time delta in millis of tx being sent
# and received by all nodes.
def hist_delta(name, iterations):
    results = []
    for iteration in iterations:
        iteration_results = [result["delta"] for result in iteration["results"]]
        results.extend(iteration_results)

    plt.hist(results, bins=20)
    plt.xlabel("delta in (ms)")
    plt.ylabel("Frequency")
    plt.title("TX dissemination over network")
    plt.savefig(name)
    plt.close()

def network_graph(name, topology):
    G = nx.DiGraph()
    for node_name, node_data in topology.items():
        G.add_node(node_name)
    for node_name, node_data in topology.items():
        for connection in node_data["static_nodes"]:
            G.add_edge(node_name, connection)

    nx.draw(G, with_labels=True)
    plt.savefig(name)
    plt.close()

def concat_images(name, images):
    images = [Image.open(image) for image in images]

    # Get the width and height of the first image
    widths, heights = zip(*(i.size for i in images))

    # Calculate the total width and height of the collage
    total_width = sum(widths)
    max_height = max(heights)

    # Create a new image with the calculated size
    collage = Image.new('RGB', (total_width, max_height))

    # Paste the images into the collage
    x_offset = 0
    for image in images:
        collage.paste(image, (x_offset, 0))
        x_offset += image.size[0]

    # Save the collage
    collage.save(name)


