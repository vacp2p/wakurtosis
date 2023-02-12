Wakurtosis
=====================

Starting version for Waku network simulations (https://github.com/waku-org/pm/issues/2)

More info about Kurtosis: https://docs.kurtosis.com/

### How to use:

#### Before using this repository note that: 

- **You are using Kurtosis version 0.66.2**. This is important, as they are working on it and changes can be huge depending on different versions. You can find all Kurtosis versions [here](https://github.com/kurtosis-tech/kurtosis-cli-release-artifacts/releases).
- The topology files that will be used by default are defined in `config/topology_generated/`. This topology is created with the [gennet](gennet-module/Readme.md) module.
- Kurtosis can set up services in a parallel manner, defined in the `config.json` file (see below).
- Only `kurtosis` and `docker` are needed to run this.

#### How to run

From the root of the repo run:

`sh ./run.sh` 

This will load the default configuration file **./config/config.json**. You can also specify a different .json config file and its location with:

`sh ./run.sh ./config/config.json`

#### JSON main configuration file options

These are arguments that can be modified:

- _prng_seed_: int. Seed to reproduce results.
- _enclave_name_: string. Default: **wakurtosis**. Defines the name of the Kurtosis enclave being created.
- _topology_file_: string. Default: **waku_test_topology_small.json**. If defines the network topology that will be created.
- _jobs_: int. Defines how many services will be instantiated at the same time.
- _interconnection_batch_: int. If nodes are being connected by a given topology, this tells kurtosis how many connections will try to set up in the same node at a time. Used to avoid timeouts if a node has a lot of connections.

- [WLS](wsl-module/README.md) module configuration
- [Gennet](gennet-module/Readme.md) module configuration

#### What will happen

Kurtosis will automatically add one node as container inside the enclave. The way that nodes are interconnected is given by the topology.
The configuration of each node is given by the configuration file. 

Once all nodes are ready, prometheus and grafana will be set up and connected to all nodes.

Once all nodes have been interconnected the simulation starts and will inject traffic into the network following the parameters specified in the configuration file.

#### Check Prometheus+Grafana+Logs

- Simulation log:

'kurtosis service logs wakurtosis $(kurtosis enclave inspect <enclave-name> | grep wsl- | awk '{print $1}')'

- Grafana server:

To display the IP address and Port of the Grafana server on your local machine run:

'kurtosis enclave inspect <enclave-name> | grep grafana- | awk '{print $6}'

Remember that by default <enclave-name> is 'wakurtosis'.

Please, any improvements/bugs that you see, create an issue, and we will work on it.
