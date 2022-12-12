Wakurtosis
=====================

Starting version for Waku network simulations (https://github.com/waku-org/pm/issues/2)

Kurtosis: https://docs.kurtosis.com/

### How to use:

#### Before using this repository make sure that: 

- **You are using Kurtosis version 0.57.4**. This is important, as they are working on it and changes can be huge depending on different versions.
- The topology that will be instantiated is defined in `kurtosis-module/starlark/waku_test_topology.json`. This topology is created with https://github.com/logos-co/Waku-topology-test 
- Each node will need its own configuration file in `kurtosis-module/starlark/config_files/waku_X.toml` being `waku_X` the same name that is defined in the topology.
- It is assumed that you have a Waku docker image. Name is harcoded in `main.star` as `IMAGE_NAME = "wakunode"` in the first lane.

Run this repo with: `kurtosis run main.star`

Please, any improvements/bugs that you see, create an issue and we will work on it. 