Module to generate network models (in JSON) and node configuration files (in TOMLs) for wakurtosis runs. 

## generate_network.py
generate_network.py generates one network and per-node configuration files. The tool is configurable with specified number of nodes, topics, network types, node types and number of subnets.

```commandline
> python gennet.py --help

Usage: gennet.py [OPTIONS]

Options:
  --output-dir TEXT               [default: topology_generated]
  --num-nodes INTEGER             [default: 4]
  --num-topics INTEGER            [default: 1]
  --network-type [configmodel|scalefree|newmanwattsstrogatz|barbell|balancedtree|star]
                                  [default: newmanwattsstrogatz]
  --node-type [desktop|mobile]    [default: desktop]
  --num-subnets INTEGER           [default: -1]
  --num-partitions INTEGER        [default: 1]
  --config-file TEXT
  --help                          Show this message and exit.
```

CLI arguments have precedence from configuration file.

Example of configuration file:

```json
{
  "gennet": {
    "num_nodes": 3,
    "num_topics": 1,
    "node_type": "desktop",
    "network_type": "scalefree",
    "num_partitions": 1,
    "num_subnets": 1
  }
}
```

It has also a Dockerfile to run it in a docker container. Example assuming our configiguration file is in `config` folder:

```commandline
> docker build -t gennet .

> docker run --name gennet-container -v ${dir}/config/:/config gennet --config-file /config/my_config_file.json --output-dir /config/topology_generated
```

In this way, it will mount `config` as a volume, allowing the docker container to get our `my_config_file.json`, and writing the results on a new folder called `topology_generated` which as it will be in `config`, the host will have access to it.


## batch_gen.sh
batch_gen.sh can generate given number of Waku networks and outputs them to a directory. Please make sure that the output directory does NOT exist; both relative and absolute paths work. The Wakunode parameters are generated at random; edit the MIN and MAX for finer control. The script requires bc & /dev/urandom.<br>

> usage: $./batch_gen.sh <output-dir> <#number of networks needed> </br>
