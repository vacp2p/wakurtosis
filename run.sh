#!/bin/sh

# Parse arg if any
ARGS1=${1:-"./config/config.json"}
echo $ARGS1

# Main .json configuration file
config_file=$ARGS1

# Delete the enclave 
kurtosis enclave rm -f $enclave_name

# Create the new enclave and run the simulation
kurtosis_cmd="kurtosis run --enclave-id ${enclave_name} . '{\"config_file\" : \"github.com/logos-co/wakurtosis/${config_file}\"}'"
eval $kurtosis_cmd

# Fetch the WSL service id and display the log of the simulation
wsl_service_id=$(kurtosis enclave inspect wakurtosis | grep wsl- | awk '{print $1}')
kurtosis service logs wakurtosis $wsl_service_id
echo "--> To see simulation logs run: kurtosis service logs wakurtosis $wsl_service_id <--"

# Fetch the Grafana address & port
grafana_host=$(kurtosis enclave inspect wakurtosis | grep grafana- | awk '{print $6}')
echo "--> Statistics in Grafana server at http://$grafana_host/ <--"