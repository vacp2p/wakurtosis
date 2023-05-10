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

if [ $err != 0 ]
then
  echo "Gennet failed with error code $err"
  exit
fi
# Copy the network generated TODO: remove this extra copy
docker cp cgennet:/gennet/network_data ${dir}/config/topology_generated
docker rm cgennet > /dev/null 2>&1
##################### END


usr=`id -u`
grp=`id -g`
odir=stats
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
    # docker run --volume=/:/rootfs:ro --volume=/var/run:/var/run:rw --volume=/var/lib/docker/:/var/lib/docker:ro --volume=/dev/disk/:/dev/disk:ro --volume=/sys:/sys:ro --volume=/etc/machine-id:/etc/machine-id:ro --publish=8080:8080 --detach=true --name=cadvisor --privileged --device=/dev/kmsg gcr.io/cadvisor/cadvisor
elif  [ "$metrics_infra" = "host-proc" ]; then # HOST-PROC
    rclist=$odir/docker-rc-list.out
    cd monitoring/host-proc
    mkdir -p $odir
    mkfifo $signal_fifo
    chmod 0777 $signal_fifo
    sudo sh ./procfs.sh $rclist $odir $usr $grp $signal_fifo &
    cd -
elif  [ "$metrics_infra" = "container-proc" ]; then # CONTAINER-PROC
  #Jordi's metrics module prologue
    echo "Jordi's measurement infra  prologue goes here"

fi
##################### END


##################### KURTOSIS RUN

# Create the new enclave and run the simulation
jobs=$(cat config/${wakurtosis_config_file} | jq -r ".kurtosis.jobs")
echo -e "\nSetting up the enclave: $enclave_name"

kurtosis_cmd="kurtosis --cli-log-level \"$loglevel\" run --enclave ${enclave_name} . '{\"wakurtosis_config_file\" : \"config/${wakurtosis_config_file}\"}' --parallelism ${jobs} > kurtosisrun_log.txt 2>&1"

START=$(date +%s)
  eval $kurtosis_cmd
END1=$(date +%s)

DIFF1=$(( $END1 - $START ))
echo -e "Enclave $enclave_name is up and running: took $DIFF1 secs to setup"

# Extract the WLS service name
wls_service_name=$(kurtosis --cli-log-level $loglevel enclave inspect $enclave_name | grep "\<wls\>" | awk '{print $1}')
echo -e "\n--> To see simulation logs run: kurtosis service logs $enclave_name $wls_service_name <--"
##################### END



##################### EXTRACT WLS CID
# Get the container prefix/suffix for the WLS service
service_name=$(kurtosis --cli-log-level $loglevel  enclave inspect $enclave_name | grep $wls_service_name | awk '{print $2}')
service_uuid=$(kurtosis --cli-log-level $loglevel  enclave inspect --full-uuids $enclave_name | grep $wls_service_name | awk '{print $1}')

# Construct the fully qualified container name that kurtosis has created
wls_cid="$service_name--$service_uuid"
##################### END



##################### MONITORING MODULE EPILOGUE: WLS SIGNALLIN
if [ "$metrics_infra" = "cadvisor" ]; then
    echo "cadvisor: signaling WLS"
    docker exec $wls_cid touch /wls/start.signal
elif [ "$metrics_infra" = "dstats" ]; then
    odir=./monitoring/dstats/$odir
    echo "odir: $odir"
    mkdir -p $odir
    dps=$odir/docker-ps.out
    dids=$odir/docker-dids.out
    dstats=$odir/docker-stats.out
    filetrs="--filter ancestor=gowaku --filter ancestor=statusteam/nim-waku:nwaku-trace2"
    docker ps --no-trunc $filters --format "{{.ID}}#{{.Names}}#{{.Image}}#{{.Command}}#{{.State}}#{{.Status}}#{{.Ports}}" > $dps
    cut -f 1 -d '#' $dps > $dids
    # add date and the names/versions of waku images involved
    echo "dstats: starting the dstats monitor"
    echo "# dstats started: $(date)" > $dstats
    echo "# images involed: $(docker images | grep waku | tr '\n' '; ' )"  >> $dstats
    # add the generating command to aid parsing/debugging
    echo '# docker stats --no-trunc --format  "{{.Container}} / {{.Name}} / {{.ID}} / {{.CPUPerc}} / {{.MemUsage}} / {{.MemPerc}} / {{.NetIO}} / {{.BlockIO}} / {{.PIDs}}"' >> $dstats
    echo "ContainerID/ContainerName/ID/CPUPerc/MemUse/MemTotal/MemPerc/NetRecv/NetSent/BlockR/BlockW/PIDS"  >> $dstats
    # start the docker stats
    docker stats --no-trunc --format  "{{.Container}} / {{.Name}} / {{.ID}} / {{.CPUPerc}} / {{.MemUsage}} / {{.MemPerc}} / {{.NetIO}} / {{.BlockIO}} / {{.PIDs}}" $(cat $dids)  >> $dstats &
    dstats_pid=$!
    echo "dstats: started and running as $dstats_pid"
    echo "dstats: signalling WLS"
    docker exec $wls_cid touch /wls/start.signal
elif [ "$metrics_infra" = "host-proc" ]; then
    echo "Starting the /proc fs and docker stat measurements"
    cd monitoring/host-proc
    sh ./dstats.sh  $wls_cid $odir $signal_fifo &
    cd -
elif [ "$metrics_infra" = "container-proc" ]; then
    echo "Jordi's measurement infra's epilogue goes here"
    # Start process level monitoring (in background, will wait to WSL to be created)
    #sudo -E python3 ./monitoring/monitor.py & ? 
    #monitor_pid=$! ?
fi
##################### END


##################### GRAFANA
# Fetch the Grafana address & port

grafana_host=$(kurtosis enclave inspect $enclave_name | grep "\<grafana\>" | awk '{print $6}')

echo -e "\n--> Statistics in Grafana server at http://$grafana_host/ <--"
echo "Output of kurtosis run command written in kurtosisrun_log.txt"
##################### END


# Get the container prefix/uffix for the WLS service
service_name="$(kurtosis --cli-log-level $loglevel  enclave inspect $enclave_name | grep $wls_service_name | awk '{print $2}')"
service_uuid="$(kurtosis --cli-log-level $loglevel  enclave inspect --full-uuids $enclave_name | grep $wls_service_name | awk '{print $1}')"


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
#sleep 60

##################### GATHER CONFIG, LOGS & METRICS
# dump logs
echo "Dumping Kurtosis logs"
kurtosis enclave dump ${enclave_name} ${enclave_name}_logs > /dev/null 2>&1
cp kurtosisrun_log.txt ${enclave_name}_logs

# copy metrics data, config, network_data to the logs dir
cp -r ./config ${enclave_name}_logs


##################### MONITORING MODULE - COPY
if [ "$metrics_infra" = "dstats" ]; then
    echo "dstats: killing dstats at $dstats_pid"
    kill -15 $dstats_pid
    echo "dstats: copying the docker stat measurements"
    cp -r ./monitoring/dstats/stats  ${enclave_name}_logs/dstats-stats
elif [ "$metrics_infra" = "host-proc" ]; then
    echo "Copying the /proc fs and docker stat measurements"
    cp -r ./monitoring/host-proc/stats  ${enclave_name}_logs/host-proc-stats
elif [ "$metrics_infra" = "container-proc" ]; then
    echo "Jordi's data copy goes here"
    #echo -e "Waiting monitoring to finish ..." ?
    #wait $monitor_pid ?
fi

# Copy simulation results
# docker cp "$wls_cid:/wls/summary.json" "./${enclave_name}_logs" > /dev/null 2>&1
docker cp "$wls_cid:/wls/messages.json" "./${enclave_name}_logs"
docker cp "$wls_cid:/wls/network_topology/network_data.json" "./${enclave_name}_logs"

echo "- Metrics Infra:  $metrics_infra" > ./${enclave_name}_logs/run_args
echo "- Enclave name:  $enclave_name" >> ./${enclave_name}_logs/run_args
echo "- Configuration file:  $wakurtosis_config_file" >> ./${enclave_name}_logs/run_args

echo "Done."
##################### END
