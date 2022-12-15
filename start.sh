#!/bin/sh
ENCLAVE_ID="wakurtosis"
PROMETHEUS_YML="prometheus.yml"

# Check Kurtosis version
kurtosis_version=$(kurtosis version)
if [ "$kurtosis_version" != "0.57.4" ]; then
    echo "Kurtosis version $kurtosis_version is not supported. Please use version 0.57.4*"
    exit 1
fi

# TODO: Check if the enclave already exists 
# kurtosis enclave stop $ENCLAVE_ID
# kurtosis enclave rm $ENCLAVE_ID

# Start the Kurtosis enclave
# kurtosis run --enclave-id $ENCLAVE_ID main.star

# Fetch the prometheus targets from the Kurtosis output
prometheus_targets=$(kurtosis enclave inspect $ENCLAVE_ID | grep 'prometheus' | sed -e 's/^.*-> \([^ ]*\) .*$/\1/' | sed "s/.*/\"&\"/;H;1h;"'$!d;x;s/\n/, /g')

# Fetch the RPC targets from the Kurtosis output
rpc_targets=$(kurtosis enclave inspect $ENCLAVE_ID | grep 'rpc' | sed -e 's/^.*-> \([^ ]*\) .*$/\1/' | sed "s/.*/\"&\"/;H;1h;"'$!d;x;s/\n/, /g')

# Generate the targets file for Prometheus
echo "Building Prometheus targets  ..."
echo "[{\"labels\": {\"job\": \"wakurtosis\"}, \"prometheus targets\" : [$prometheus_targets], \"rpc targets\" : [$rpc_targets] } ]" | tee './targets.json' > /dev/null

echo "RPC targets are: $rpc_targets"
echo "Prometheus targets are: $prometheus_targets"

# Start Prometheus on http:/localhost:9090
# prometheus --config.file=./prometheus.yml 

# Follow the instructions to setup Grafana on https://github.com/waku-org/nwaku/blob/master/docs/operators/how-to/monitor.md
# Grafana server http://localhost:3000