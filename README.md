Wakurtosis
=====================
Starting version for Waku network simulations (https://github.com/waku-org/pm/issues/2)

More info about Kurtosis: https://docs.kurtosis.com/

### How to use:

#### Before using this repository note that: 

- **You are using Kurtosis version 0.70.2**. This is important, as they are working on it and changes can be huge depending on different versions. You can find all Kurtosis versions [here](https://github.com/kurtosis-tech/kurtosis-cli-release-artifacts/releases).
- The topology files that will be used by default are defined in `config/topology_generated/`. This topology is created with the [gennet](gennet-module/Readme.md) module.
- Kurtosis can set up services in a parallel manner, defined in the `config.json` file (see below).
- Only `kurtosis` and `docker` are needed to run this.

#### How to run

From the root of the repo run:

`./build.sh`

`./run.sh <measurement_infra> [enclave_name] [config_file]` 

There are 4 different measurements: `cadvisor`, `dstats`, `host-proc`, `container-proc`. The other parameters are optional.

By default, the enclave name is `wakurtosis` and the config file is in `config/config.json`. 

#### JSON main configuration file options

These are arguments that can be modified:

- _prng_seed_: int. Seed to reproduce results.
- _enclave_name_: string. Default: **wakurtosis**. Defines the name of the Kurtosis enclave being created.
- _topology_path_: string. Topology information that will be read.
- _jobs_: int. Defines how many services will be instantiated at the same time.
- _interconnect_nodes_: It allows to skip the interconnection phase of the topology.
- _interconnection_batch_: int. If nodes are being connected by a given topology, this tells kurtosis how many connections will try to set up in the same node at a time. Used to avoid timeouts if a node has a lot of connections.

- [Gennet](gennet-module/Readme.md) module configuration
- [WLS](wls-module/README.md) module configuration

