This repo contains scripts to generate network models (in JSON) and waku configuration files (in TOMLs) for wakukurtosis runs. 


## generate_network.py
generate_network.py generates one network and per-node configuration files. The tool is configurable with specified number of nodes, topics, network types, node types and number of subnets. Use with Python3. Comment out the `#draw(fname, H)` line to visualise the generated graph.

> usage: $./generate_network --help

## batch_gen.sh
batch_gen.sh can generate given number of Waku networks and outputs them to a directory. Please make sure that the output directory does NOT exist; both relative and absolute paths work. The Wakunode parameters are generated at random; edit the MIN and MAX for finer control. The script requires bc & /dev/urandom.<br>

> usage: $./batch_gen.sh <output-dir> <#number of networks needed> </br>
