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

If you want to run it with default arguments, if you are in the root of this repository, you can simply run:

`kurtosis run .`

There are arguments that can be modified:
- _same_toml_configuration_: boolean. Default: **true**. If **true**, the some `.toml` file will be applied to every Waku node. If **false*, every node will use its own `.toml` file.
- _topology_file_: string. Default: **waku_test_topology_small.json**. If defines the network topology that will be created.

Example modifying arguments:

`kurtosis run . '{"same_toml_configuration": false, "topology_file": "waku_test_topology_big.json"}'`

The enclaves that will be created have randon names, that can be checked with:

`kurtosis enclave ls`

You can set up a pre-defined enclave name, for example:

`kurtosis run --enclave-id wakurtosis .`

Note that, if you try to run the same kurtosis module again, you will have clashes. You can clean previous enclaves with:

`kurtosis clean -a`

#### Check Prometheus+Grafana

In order to know how to access to Prometheus or Grafana, run:

`kurtosis enclave inspect <enclave-name>'`

With this, you will be able to see the ports exposed to your local machine.

Please, any improvements/bugs that you see, create an issue, and we will work on it.
