Wakurtosis
=====================

Starting version for Waku network simulations (https://github.com/waku-org/pm/issues/2)

More info about Kurtosis: https://docs.kurtosis.com/

### How to use:

#### Before using this repository note that: 

- **You are using Kurtosis version 0.62.0**. This is important, as they are working on it and changes can be huge depending on different versions. You can find all Kurtosis versions [here](https://github.com/kurtosis-tech/kurtosis-cli-release-artifacts/releases).
- The topology files that will be used by default are defined in `config/network_topology/`. This topology is created with https://github.com/logos-co/Waku-topology-test
- Each node will need its own configuration file in `config/waku_config_files/waku_X.toml` being `waku_X` the same name that is defined in the topology.
- Only `kurtosis` and `docker` are needed to run this.

#### How to run

From the root of the repo run:

`sh ./run.sh` 

This will load the default confiration .json file **./config/config.json**. You can also specify a different .json config file and its location with:

`sh ./run.sh ./config/config.json`

#### JSON main configuration file options

These are arguments that can be modified:

- _enclave_name_: string. Default: **wakurtosis**. Defines the name of the Kurtosis enclave being created.
- _same_toml_configuration_: boolean. Default: **true**. If **true**, the some `.toml` file will be applied to every Waku node. If **false*, every node will use its own `.toml` file.
- _topology_file_: string. Default: **waku_test_topology_small.json**. If defines the network topology that will be created.
- _simulation_time_: int. Default: **300**. Specifies the simulation time in seconds.
- _message_rate_: int. Default: **25**. Specifies the message rate in packets per second.
- _min_packet_size_: int. Default: **1**. Specifies the minimum size of the packet in bytes. Must be an even number (Waku constrain).
- _min_packet_size_: int. Default: **1024**. Specifies the maximum size of the packet in bytes. Must be an even number (Waku constrain).
- _dist_type_: int. Default: **uniform**. Specifies the size distribution of the messages being injected into the network. Options are: **gaussian** and **uniform**
- _emitters_fraction_: int. Default: **0.5**. Specifies the fraction of nodes that will be injecting traffic.
- _inter_msg_type_: int. Default: **poisson**. Specifies the inter-message times. Options are: **poisson** and **uniform**

dist_type : "gaussian"

    # Fraction (of the total number of nodes) that inject traffic
    # Values: [0., 1.]
    emitters_fraction : 0.5

    # Inter-message times
    # Values: uniform and gaussian
    inter_msg_type : "uniform"

- _num_nodes_: int. Number of nodes in the enclave.
- _num_topics_: int. Number of topics.
- _node_type_: string. Type of node. Options are **desktop and **mobile**
- _network_type_: string. Network topology. Options are **configmodel**, **scalefree**, **newmanwattsstrogatz**, **barbell**, **balancedtree**, and **star**
- _num_partitions_: int. Number of partitions within the network.
- _num_subnets_: int. Number of subnetworks.

#### What will happen

Kurtosis will automatically add one Waku node as container inside the enclave. The way that nodes are interconnected is given by the topology.
The configuration of each node is given by the configuration files. Services are being instantiated SEQUENTIALLY. After each node is set up,
there are 5 seconds (defined in `system_variables`) of waiting time for that node to be ready, and then the ID is requested and saved.

Once all nodes are ready, prometheus and grafana will be set up and connected to all waku nodes.

Once all nodes have been interconnected the simulation starts and will inject traffic into the network following the parameters specified in the configuration file.

#### Check Prometheus+Grafana+Logs

- Simulation log:

'kurtosis service logs wakurtosis $(kurtosis enclave inspect <enclave-name> | grep wsl- | awk '{print $1}')'

- Grafana server:

To display the IP address and Port of the Grafana server on your local machine run:

'kurtosis enclave inspect <enclave-name> | grep grafana- | awk '{print $6}'

Remember that by default <enclave-name> is 'wakurtosis'.

Please, any improvements/bugs that you see, create an issue, and we will work on it.
