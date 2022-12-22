Wakurtosis Load Simualtor (WSL)
===============================

Kurtosis: https://docs.kurtosis.com/

### How to use:

To build docker image:
    `sh ./build.sh`
To run docker image: 
    `sh ./run.sh`

At the moment the targets.json file is copied to the container during build which means that the container imgage has to be rebuilt whenever the enclave restarts --- and the private IPs of the Waku nodes change. The targets.json is automatically generatted during the build step

#### Before using this repository make sure that: 
For the build step make sure that the Wakurtosis enclave exists and make sure the enclave is running before running the container