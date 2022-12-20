Wakurtosis
=====================

Starting version for Waku network simulations (https://github.com/waku-org/pm/issues/2)

Kurtosis: https://docs.kurtosis.com/

### How to use:

#### Before using this repository make sure that: 

- **You are using Kurtosis version 0.62.0**. This is important, as they are working on it and changes can be huge depending on different versions. You can find all Kurtosis versions [here](https://github.com/kurtosis-tech/kurtosis-cli-release-artifacts/releases).
- The topology that will be instantiated is defined in `kurtosis-module/starlark/waku_test_topology.json`. This topology is created with https://github.com/logos-co/Waku-topology-test 
- Each node will need its own configuration file in `kurtosis-module/starlark/config_files/waku_X.toml` being `waku_X` the same name that is defined in the topology.

If you want to use the same configuration for every node, you can use:

`kurtosis run --enclave-id wakurtosis main.star '{"same_toml_configuration": true}'`

This will use the file `kurtosis-module/starlark/config_files/waku_general.toml` for every node.

In order to access to Prometheus or Graphana, run:

`kurtosis enclave inspect wakurtosis'`

With this, you will be able to see the ports exposed to your local machine.

Please, any improvements/bugs that you see, create an issue, and we will work on it. 