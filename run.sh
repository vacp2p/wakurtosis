#!/bin/sh

# Parse arg if any
ARGS1=${1:-"./config/config.json"}
echo $ARGS1

# Main .json configuration file
config_file=$ARGS1

# Needs JQ to parse the main .json config file: 
# sudo apt-get install jq
# brew install jq

enclave_name=$(cat $config_file | jq -r ".enclave_name")
topology_path=$(cat $config_file | jq -r ".topology_path")
num_nodes=$(cat $config_file | jq -r ".num_nodes")
num_topics=$(cat $config_file | jq -r ".num_topics")
node_type=$(cat $config_file | jq -r ".node_type")
network_type=$(cat $config_file | jq -r ".network_type")
num_partitions=$(cat $config_file | jq -r ".num_partitions")
num_subnets=$(cat $config_file | jq -r ".num_subnets")

# Generate the topology
echo "Deleting previously generted topology in $topology_path ..."
rm -rf $topology_path
echo "Generating ./generate_network.py --dirname $topology_path --num-nodes $num_nodes --num-topics $num_topics --nw-type $network_type --node-type $node_type --num-partitions $num_partitions --num-subnets $num_subnets ...."
./gennet/generate_network.py --dirname $topology_path --num-nodes $num_nodes --num-topics $num_topics --network-type $network_type --node-type $node_type --num-partitions $num_partitions --num-subnets $num_subnets

# Delete the enclave 
kurtosis enclave rm -f $enclave_name

# Create the new enclave and run the simulation
kurtosis_cmd="kurtosis run --enclave-id ${enclave_name} . '{\"config_file\" : \"github.com/logos-co/wakurtosis/${config_file}\"}'"
eval $kurtosis_cmd

# Fetch the WSL service id and display the log of the simulation
wsl_service_id=$(kurtosis enclave inspect wakurtosis | grep wsl- | awk '{print $1}')
kurtosis service logs wakurtosis $wsl_service_id
echo "--> To see simulation logs run: kurtosis enclave inspect wakurtosis $wsl_service_id <--"

# Fetch the Grafana address & port
grafana_host=$(kurtosis enclave inspect wakurtosis | grep grafana- | awk '{print $6}')
echo "--> Statistics in Grafana server at http://$grafana_host/ <--"