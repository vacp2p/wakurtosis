#!/bin/sh

##################### SETUP & CLEANUP
if [ "$#" -eq 0 ]; then
    echo "Error: Must select the measurement infra: cadvisor, dstats, host-proc, container-proc"
    echo "Usage: sh ./run.sh <measurement_infra> [enclave_name] [config_file]"
    exit 1
fi

dir=$(pwd)

# Parse args
metrics_infra=${1:-"cadvisor"}
enclave_name=${2:-"wakurtosis"}
wakurtosis_config_file=${3:-"config.json"}

loglevel="error"
echo "- Metrics Infra: " $metrics_infra
echo "- Enclave name: " $enclave_name
echo "- Configuration file: " $wakurtosis_config_file

# Cleanup previous runs
echo -e "\Cleaning up previous runs"
sh ./cleanup.sh $enclave_name
echo -e "\Done cleaning up previous runs"

#make sure the prometheus and grafana configs are readable
chmod  a+r monitoring/prometheus.yml  monitoring/configuration/config/grafana.ini  ./monitoring/configuration/config/provisioning/dashboards/dashboard.yaml
##################### END


##################### GENNET
echo -e "\nRunning network generation"
docker run --name cgennet -v ${dir}/config/:/config:ro gennet --config-file /config/${wakurtosis_config_file} --traits-dir /config/traits
err=$?

if [ $err != 0 ]; then
  echo "Gennet failed with error code $err"
  exit
fi
# Copy the network generated TODO: remove this extra copy
docker cp cgennet:/gennet/network_data ${dir}/config/topology_generated
docker rm cgennet > /dev/null 2>&1
##################### END


kurtosis_inspect="kurtosis_inspect.log"
usr=`id -u`
grp=`id -g`
stats_dir=stats
signal_fifo=/tmp/hostproc-signal.fifo   # do not create fifo under ./stats, or inside the repo
##################### MONITORING MODULE PROLOGUES
if [ "$metrics_infra" = "cadvisor" ]; then #CADVISOR
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
elif  [ "$metrics_infra" = "dstats" ]; then # HOST-PROC
    odir=./monitoring/dstats/$stats_dir
    mkdir $odir
elif  [ "$metrics_infra" = "host-proc" ]; then # HOST-PROC
    odir=./monitoring/host-proc/$stats_dir
    rclist=$odir/docker-rc-list.out
    mkdir $odir
    mkfifo $signal_fifo
    chmod 0777 $signal_fifo
    sudo sh ./monitoring/host-proc/host-proc-helper.sh $rclist $odir $usr $grp $signal_fifo &
elif  [ "$metrics_infra" = "container-proc" ]; then # CONTAINER-PROC
  #Jordi's metrics module prologue
    echo "Jordi's measurement infra  prologue goes here"

fi
##################### END


##################### KURTOSIS RUN
# Create the new enclave and run the simulation
jobs=$(cat config/${wakurtosis_config_file} | jq -r ".kurtosis.jobs")
echo -e "\nSetting up the enclave: $enclave_name"

kurtosis_cmd="kurtosis --cli-log-level \"$loglevel\" run --full-uuids --enclave ${enclave_name} . '{\"wakurtosis_config_file\" : \"config/${wakurtosis_config_file}\"}' --parallelism ${jobs} > kurtosisrun_log.txt 2>&1"

START=$(date +%s)
  eval $kurtosis_cmd
END1=$(date +%s)

DIFF1=$(( $END1 - $START ))
echo -e "Enclave $enclave_name is up and running: took $DIFF1 secs to setup"

sed -n '/Starlark code successfully run. No output was returned./,$p'  kurtosisrun_log.txt  > $kurtosis_inspect

# Extract the WLS service name
wls_service_name=$(grep "\<wls\>" $kurtosis_inspect | awk '{print $1}')
echo -e "\n--> To see simulation logs run: kurtosis service logs $enclave_name $wls_service_name <--"
# Get the container prefix/suffix for the WLS service
service_name=$(grep  $wls_service_name $kurtosis_inspect | awk '{print $2}')
service_uuid=$(grep $wls_service_name $kurtosis_inspect | awk '{print $1}')

# Construct the fully qualified container name that kurtosis has created
wls_cid="$service_name--$service_uuid"
echo "The WLS_CID = $wls_cid"
##################### END


##################### MONITORING MODULE EPILOGUE: WLS SIGNALLING
if [ "$metrics_infra" = "cadvisor" ]; then
    echo "cadvisor: signaling WLS"
    docker exec $wls_cid touch /wls/start.signal
elif [ "$metrics_infra" = "dstats" ]; then
    echo "Starting dstats measurements.."
    # collect container/node mapping via kurtosis
    kinspect=$odir/docker-kinspect.out
    cp $kurtosis_inspect $kinspect
    sh ./monitoring/dstats/dstats.sh $wls_cid $odir &  # the process subtree takes care of itself
elif [ "$metrics_infra" = "host-proc" ]; then
    echo "Starting host-proc measurements.."
    kinspect=$odir/docker-kinspect.out
    cp $kurtosis_inspect $kinspect
    sh ./monitoring/host-proc/host-proc.sh  $wls_cid $odir $signal_fifo &
elif [ "$metrics_infra" = "container-proc" ]; then
    echo "Starting monitoring with probes in the containers"
    # Start process level monitoring (in background, will wait to WSL to be created)
   docker run \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v $(pwd)/monitoring/container-proc/:/cproc-mon/ \
    -v $(pwd)/config/config.json:/cproc-mon/config/config.json \
    container-proc:latest &
 
    monitor_pid=$!
fi
##################### END


##################### GRAFANA
# Fetch the Grafana address & port

#grafana_host=$(kurtosis enclave inspect $enclave_name | grep "\<grafana\>" | awk '{print $6}')
grafana_host=$(grep "\<grafana\>" $kurtosis_inspect | awk '{print $6}')

echo -e "\n--> Statistics in Grafana server at http://$grafana_host/ <--"
echo "Output of kurtosis run command written in kurtosisrun_log.txt"
##################### END



##################### WAIT FOR THE WLS TO FINISH
# Wait for the container to halt; this will block
echo -e "Waiting for simulation to finish ..."
status_code="$(docker container wait $wls_cid)"
echo -e "Simulation ended with code $status_code Results in ./${enclave_name}_logs"
END2=$(date +%s)
DIFF2=$(( $END2 - $END1 ))
echo "Simulation took $DIFF1 + $DIFF2 = $(( $END2 - $START)) secs"
##################### END

# give time for the messages to settle down before we collect the logs
sleep 60

##################### GATHER CONFIG, LOGS & METRICS
# dump logs
echo "Dumping Kurtosis logs"
kurtosis enclave dump ${enclave_name} ${enclave_name}_logs > /dev/null 2>&1
cp kurtosisrun_log.txt ${enclave_name}_logs
# copy metrics data, config, network_data to the logs dir
cp -r ./config ${enclave_name}_logs


##################### MONITORING MODULE - COPY
if [ "$metrics_infra" = "dstats" ]; then
    # unfortunately no way to introduce a race-free finish signalling
    echo "dstats: copying the dstats data"
    cp -r ./monitoring/dstats/stats  ${enclave_name}_logs/dstats-data
elif [ "$metrics_infra" = "host-proc" ]; then
    echo "Copying the host-proc data"
    cp -r ./monitoring/host-proc/stats  ${enclave_name}_logs/host-proc-data
elif [ "$metrics_infra" = "container-proc" ]; then
    echo -e "Waiting monitoring to finish ..."
    wait $monitor_pid
    echo "Copying the container-proc measurements"
    cp ./monitoring/container-proc/cproc_metrics.json "./${enclave_name}_logs/cproc_metrics.json" > /dev/null 2>&1
    # \rm -r ./monitoring/container-proc/cproc_metrics.json > /dev/null 2>&1
fi

# Copy simulation results
docker cp "$wls_cid:/wls/messages.json" "./${enclave_name}_logs"
docker cp "$wls_cid:/wls/network_topology/network_data.json" "./${enclave_name}_logs"

echo "- Metrics Infra:  $metrics_infra" > ./${enclave_name}_logs/run_args
echo "- Enclave name:  $enclave_name" >> ./${enclave_name}_logs/run_args
echo "- Configuration file:  $wakurtosis_config_file" >> ./${enclave_name}_logs/run_args

# Run analysis
if jq -e ."plotting" >/dev/null 2>&1 "./config/${wakurtosis_config_file}"; then
    if [ "$metrics_infra" = "container-proc" ]; then
        docker run --network "host" -v "$(pwd)/wakurtosis_logs:/simulation_data/" --add-host=host.docker.internal:host-gateway analysis src/main.py -i container-proc >/dev/null 2>&1
    elif [ "$metrics_infra" = "cadvisor" ]; then
        prometheus_port=$(grep "\<prometheus\>" $kurtosis_inspect | awk '{print $6}' | awk -F':' '{print $2}')
        docker run --network "host" -v "$(pwd)/wakurtosis_logs:/simulation_data/" --add-host=host.docker.internal:host-gateway analysis src/main.py -i cadvisor -p "$prometheus_port" >/dev/null 2>&1
    fi
fi

echo "Done."
##################### END
