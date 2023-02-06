Module to generate network models (in JSON) and node configuration files (in TOMLs) for wakurtosis runs. It can be deployed in two ways: as a stand-alone python tool or as a docker.

## gennet cli
`gennet.py` takes a range of CLI inputs, and outputs the network data --- in the form of a `network_data.json` file and a set of per-node TOML files. 

```commandline
> python gennet.py --help
 Usage: gennet.py [OPTIONS]                                                     
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --benchmark         --no-benchmark                        [default:          │
│                                                           no-benchmark]      │
│ --output-dir                          TEXT                [default: network_data]                   │
│ --prng-seed                           INTEGER             [default: 1]      │
│ --num-nodes                           INTEGER             [default: 4]      │
│ --num-topics                          INTEGER             [default: 1]      │
│ --network-type                        [configmodel|scale  [default:          │
│                                       free|newmanwattsst  newmanwattsstroga… │
│                                       rogatz|barbell|bal                     │
│                                       ancedtree|star|]                       │
│ --num-partitions                      INTEGER             [default: 1]      │
│ --num-subnets                         INTEGER             [default: -1]      │
│ --config-file                         TEXT                                   │
│ --help                                                    Show this message  │
│                                                           and exit.          │
╰──────────────────────────────────────────────────────────────────────────────╯
```

Our tool can also take arguments from a json file, specified using `--config-file` option.


Following is an example json file:


````json
{
  "general":{
    "prng_seed" : 67
  },
  "gennet": {
    "num_nodes": 100,
    "num_topics": 150,
    "num_partitions": 1,
    "num_subnets": 2,
    "node_type_distribution": { "nwaku":50, "gowaku":50},
    "node_type": "desktop",
    "network_type": "scalefree",
    "output_dir": "generated_network"
  }
}
```

Note that CLI arguments take precedence over the configuration file options.

## gennet docker
The gennet module can also be run as a docker. The Dockerfile provided can be used to build and run the gennet container as follows:


```commandline
> docker build -t gennet .

> docker run --name gennet-container -v ${dir}/config/:/config gennet --config-file /config/$input_config_file --output-dir /config/$output_dir
```

When run this way, the docker will mount the host's `config` dir as a volume, allowing the gennet container to access the `$input_config_file` in the host filesystem; gennet reads the config.json and outputs a network under the `$output_dir` which is made accessible to the host via a subsequent`docker cp`.


## batch_gen.sh
batch_gen.sh can generate given number of Waku networks and outputs them to a directory. Please make sure that the output directory does NOT exist; both relative and absolute paths work. The Wakunode parameters are generated at random; edit the MIN and MAX for finer control. The script requires bc & /dev/urandom.<br>

> usage: $./batch_gen.sh <output-dir> <#number of networks needed> </br>
