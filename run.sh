#!/bin/sh

dir=$(pwd)

# Parse arg if any
ARGS1=${1:-"cadvisor"}
ARGS2=${2:-"wakurtosis"}
ARGS3=${3:-"config.json"}

# Main .json configuration file
metrics_infra=$ARGS1
enclave_name=$ARGS2
wakurtosis_config_file=$ARGS3
loglevel="error"

echo "- Enclave name: " $enclave_name
echo "- Configuration file: " $wakurtosis_config_file

# Cleanup previous runs
echo -e "\Cleaning up previous runs"
sh ./cleanup.sh $enclave_name

##################### CADVISOR
if [ "$metrics_infra" = "cadvisor" ];
then
    # Preparing enclave
    echo "Preparing the enclave..."
    kurtosis  --cli-log-level $loglevel  enclave add --name ${enclave_name}
    enclave_prefix=$(kurtosis --cli-log-level $loglevel  enclave inspect --full-uuids $enclave_name | grep UUID: | awk '{print $2}')
    echo "Enclave network: "$enclave_prefix

    # Get enclave last IP
    subnet="$(docker network inspect $enclave_prefix | jq -r '.[].IPAM.Config[0].Subnet')"
    echo "Enclave subnetork: $subnet"
    last_ip="$(ipcalc $subnet | grep HostMax | awk '{print $2}')"
    echo "cAdvisor IP: $last_ip"

    # Set up Cadvisor
    docker run --volume=/:/rootfs:ro --volume=/var/run:/var/run:rw --volume=/var/lib/docker/:/var/lib/docker:ro --volume=/dev/disk/:/dev/disk:ro --volume=/sys:/sys:ro --volume=/etc/machine-id:/etc/machine-id:ro --publish=8080:8080 --detach=true --name=cadvisor --privileged --device=/dev/kmsg --network $enclave_prefix --ip=$last_ip gcr.io/cadvisor/cadvisor:v0.47.0
    # docker run --volume=/:/rootfs:ro --volume=/var/run:/var/run:rw --volume=/var/lib/docker/:/var/lib/docker:ro --volume=/dev/disk/:/dev/disk:ro --volume=/sys:/sys:ro --volume=/etc/machine-id:/etc/machine-id:ro --publish=8080:8080 --detach=true --name=cadvisor --privileged --device=/dev/kmsg gcr.io/cadvisor/cadvisor
fi
##################### END


##################### GENNET
# Run Gennet docker container
echo -e "\nRunning network generation"
docker run --name gennet -v ${dir}/config/:/config:ro gennet --config-file /config/${wakurtosis_config_file} --traits-dir /config/traits
err=$?
if [ $err != 0 ]
then
  echo "Gennet failed with error code $err"
  exit
fi
# Copy the network generated TODO: remove this extra copy
docker cp gennet:/gennet/network_data ${dir}/config/topology_generated
docker rm gennet > /dev/null 2>&1
##################### END



##################### KURTOSIS RUN
# Create the new enclave and run the simulation
jobs=$(cat config/${wakurtosis_config_file} | jq -r ".kurtosis.jobs")
echo -e "\nSetting up the enclave: $enclave_name"
kurtosis_cmd="kurtosis --cli-log-level \"$loglevel\" run --enclave-id ${enclave_name} . '{\"wakurtosis_config_file\" : \"config/${wakurtosis_config_file}\"}' --parallelism ${jobs} > kurtosisrun_log.txt 2>&1"
START=$(date +%s)
eval $kurtosis_cmd
END1=$(date +%s)
DIFF1=$(( $END1 - $START ))
echo -e "Enclave $enclave_name is up and running: took $DIFF1 secs to setup"

# Extract the WLS service name
wls_service_name=$(kurtosis --cli-log-level $loglevel enclave inspect $enclave_name | grep wls | awk '{print $1}')
# kurtosis service logs $enclave_name $wls_service_name
echo -e "\n--> To see simulation logs run: kurtosis service logs $enclave_name $wls_service_name <--"
##################### END



##################### EXTRACT CIDS
# Fetch the Grafana address & port
grafana_host=$(kurtosis --cli-log-level $loglevel  enclave inspect $enclave_name | grep grafana | awk '{print $6}')
echo -e "\n--> Statistics in Grafana server at http://$grafana_host/ <--"
echo "Output of kurtosis run command written in kurtosisrun_log.txt"

# Get the container prefix/suffix for the WLS service
service_name=$(kurtosis --cli-log-level $loglevel  enclave inspect $enclave_name | grep $wls_service_name | awk '{print $2}')
service_uuid=$(kurtosis --cli-log-level $loglevel  enclave inspect --full-uuids $enclave_name | grep $wls_service_name | awk '{print $1}')

# Construct the fully qualified container name that kurtosis has created
cid="$service_name--$service_uuid"
##################### END

sh ./monitoring/procfs-stats/monitor.sh $cid &

# Wait for the container to halt; this will block
echo -e "Waiting for simulation to finish ..."
status_code="$(docker container wait $cid)"
##################### END


### Logs
kurtosis enclave dump ${enclave_name} ${enclave_name}_logs > /dev/null 2>&1
echo -e "Simulation ended with code $status_code Results in ./${enclave_name}_logs"

# copy metrics data, config, network_data to the logs dir
cp -r ./config ${enclave_name}_logs
cp -r ./monitoring/procfs-stats/stats  ${enclave_name}_logs/procfs-stats

END2=$(date +%s)
DIFF2=$(( $END2 - $END1 ))

echo "Simulation took $DIFF1 + $DIFF2 = $(( $END2 - $START)) secs"
# Copy simulation results
# docker cp "$cid:/wls/summary.json" "./${enclave_name}_logs" > /dev/null 2>&1
docker cp "$cid:/wls/messages.json" "./${enclave_name}_logs"

echo "Done."
