#!/bin/sh

##################### SETUP & CLEANUP
if [ "$#" -eq 0 ]; then
    echo "Error: Must select the measurement infra: cadvisor, dstats, host-proc, container-proc"
    echo "Usage: sh ./run.sh <measurement_infra> [enclave_name] [config_file]"
    exit 1
fi

# get the args
metrics_infra=${1:-"cadvisor"}
enclave_name=${2:-"wakurtosis"}
wakurtosis_config_file=${3:-"config.json"}

dir=$(pwd)
loglevel="error"
echo "- Metrics Infra: " "$metrics_infra"
echo "- Enclave name: " "$enclave_name"
echo "- Configuration file: " "$wakurtosis_config_file"

# Cleanup previous runs
echo "Cleaning up previous runs"
sh ./bash-utils/cleanup.sh $enclave_name
echo "Done cleaning up previous runs"

# make sure the prometheus and grafana configs are readable
chmod  a+r monitoring/prometheus.yml  monitoring/configuration/config/grafana.ini  ./monitoring/configuration/config/provisioning/dashboards/dashboard.yaml
##################### END

kurtosis_run="kurtosis_run.log"
kurtosis_inspect="kurtosis_inspect.log"

usr=`id -u`
grp=`id -g`
stats_dir=stats
signal_fifo=/tmp/hostproc-signal.fifo   # do not create fifo under ./stats, or inside the repo

##################### PREPARING ENCLAVE
# prepare the enclave
    echo "Preparing the enclave..."
    kurtosis  --cli-log-level $loglevel  enclave add --name ${enclave_name}
    enclave_prefix=$(kurtosis --cli-log-level $loglevel  enclave inspect --full-uuids $enclave_name | grep UUID: | awk '{print $2}')
    echo "Enclave network: "$enclave_prefix
    # get the last IP of the enclave
    subnet="$(docker network inspect $enclave_prefix | jq -r '.[].IPAM.Config[0].Subnet')"
    echo "Enclave subnetork: $subnet"
    last_ip="$(ipcalc $subnet | grep HostMax | awk '{print $2}')"
#####################

##################### MONITORING MODULE PROLOGUES
if [ "$metrics_infra" = "cadvisor" ]; then #CADVISOR
    echo "cAdvisor IP: $last_ip"
    # set up the cadvisor
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
    # get the sudo sorted out in the main thread itself
    echo "host-proc: need sudo rights, please enter suitable credentials at the prompt"
    sudo echo "host-proc: got the credentials, starting the host-proc helper" # dummy sudo cmd
    sudo sh ./monitoring/host-proc/host-proc-helper.sh $rclist $odir $usr $grp $signal_fifo &
fi
##################### END


##################### BOOTSTRAP NODE
echo "Setting up bootstrap node"
# Get bootstrap IP in enclave
IFS='.' ip_parts="$last_ip"

part1=$(echo "$ip_parts" | cut -d '.' -f 1)
part2=$(echo "$ip_parts" | cut -d '.' -f 2)
part3=$(echo "$ip_parts" | cut -d '.' -f 3)
part4=$(echo "$ip_parts" | cut -d '.' -f 4)

previous_part=$((part4 - 1))

bootstrap_ip="$part1.$part2.$part3.$previous_part"
IFS=' '
echo "Bootstrap node IP: $bootstrap_ip"
docker run --name bootstrap_node -p 127.0.0.1:60000:60000 -p 127.0.0.1:8008:8008 -p 127.0.0.1:9000:9000 -p 127.0.0.1:8545:8545 -v "$(pwd)/bash-utils/run_bootstrap_node.sh:/opt/runnode.sh:Z" --detach=true --network $enclave_prefix --ip="$bootstrap_ip" --entrypoint sh statusteam/nim-waku:nwaku-trace3 -c "/opt/runnode.sh" >/dev/null 2>&1

RETRIES_TRAFFIC=${RETRIES_TRAFFIC:=10}
while [ -z "${NODE_ENR}" ] && [ ${RETRIES_TRAFFIC} -ge 0 ]; do
  NODE_ENR=$(wget -O - --post-data='{"jsonrpc":"2.0","method":"get_waku_v2_debug_v1_info","params":[],"id":1}' --header='Content-Type:application/json' http://localhost:8545/ 2> /dev/null | sed 's/.*"enrUri":"\([^"]*\)".*/\1/');
  echo "Trying to get Bootstrap ENR, but node still not ready, retrying (retries left: ${RETRIES_TRAFFIC})"
  sleep 1
  RETRIES_TRAFFIC=$(( $RETRIES_TRAFFIC - 1 ))
done
echo "Bootstrap ENR: ${NODE_ENR}"

# Specify the path to your TOML file
echo "Injecting ENR in Discv5 toml"
toml_file="config/traits/discv5.toml"
sed -i "s|discv5-bootstrap-node=\(.*\)|discv5-bootstrap-node=[\"${NODE_ENR}\"]|" $toml_file
##################### END


##################### GENNET
# Run Gennet docker container
echo "Running network generation"
docker run --name cgennet -v ${dir}/config/:/config:ro gennet --config-file /config/"${wakurtosis_config_file}" --traits-dir /config/traits
err=$?

if [ $err != 0 ]; then
  echo "Gennet failed with error code $err"
  exit
fi
# Copy the network generated TODO: remove this extra copy
docker cp cgennet:/gennet/network_data "${dir}"/config/topology_generated
docker rm cgennet > /dev/null 2>&1
##################### END


##################### KURTOSIS RUN
# Create the new enclave and run the simulation
jobs=$(cat "${dir}"/config/"${wakurtosis_config_file}" | jq -r ".kurtosis.jobs")
echo "\nSetting up the enclave: $enclave_name"

kurtosis_cmd="kurtosis --cli-log-level \"$loglevel\" run --full-uuids --enclave ${enclave_name} . '{\"wakurtosis_config_file\" : \"config/${wakurtosis_config_file}\"}' --parallelism ${jobs} > $kurtosis_run 2>&1"

START=$(date +%s)
  eval "$kurtosis_cmd"
END1=$(date +%s)

DIFF1=$(( $END1 - $START ))
echo "Enclave $enclave_name is up and running: took $DIFF1 secs to setup"
sed -n '/Starlark code successfully run. No output was returned./,$p'  $kurtosis_run  > $kurtosis_inspect

# Extract the WLS service name
wls_service_name=$(grep "\<wls\>" $kurtosis_inspect | awk '{print $1}')
echo "\n--> To see simulation logs run: kurtosis service logs $enclave_name $wls_service_name <--"

# Get the container prefix/suffix for the WLS service
wls_sname=$(grep $wls_service_name $kurtosis_inspect | awk '{print $2}')
wls_suuid=$(grep $wls_service_name $kurtosis_inspect | awk '{print $1}')

# Construct the fully qualified container name that kurtosis has created
wls_cid="$wls_sname--$wls_suuid"
#echo "The WLS_CID = $wls_cid"
collnet_sname="CollectNet"
collnet_suuid=$(grep $collnet_sname $kurtosis_inspect | awk '{print $1}')
collnet_cid="$collnet_sname--$collnet_suuid"
echo "CollectNet is at $collnet_cid"
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

echo "\n--> Statistics in Grafana server at http://$grafana_host/ <--"
echo "Output of kurtosis run command written in $kurtosis_run"
##################### END



##################### WAIT FOR THE WLS TO FINISH
# Wait for the container to halt; this will block
echo "Waiting for simulation to finish ..."
status_code="$(docker container wait $wls_cid)"
echo "Simulation ended with code $status_code Results in ./${enclave_name}_logs"
END2=$(date +%s)
DIFF2=$(( $END2 - $END1 ))
echo "Simulation took $DIFF1 + $DIFF2 = $(( $END2 - $START)) secs"
##################### END


##################### GATHER CONFIG, LOGS & METRICS
# give time for the messages to settle down before we collect the logs
sleep 60

# dump logs
echo "Dumping Kurtosis logs"
kurtosis enclave dump ${enclave_name} ${enclave_name}_logs > /dev/null 2>&1
cp $kurtosis_run $kurtosis_inspect ${enclave_name}_logs
# copy metrics data, config, network_data to the logs dir
cp -r ./config ${enclave_name}_logs


##################### MONITORING MODULE - COPY
if [ "$metrics_infra" = "dstats" ]; then
    # unfortunately there is no way to introduce a race-free finish signalling
    echo "dstats: copying the dstats data"
    cp -r ./monitoring/dstats/stats  ${enclave_name}_logs/dstats-data
elif [ "$metrics_infra" = "host-proc" ]; then
    echo "Copying the host-proc data"
    cp -r ./monitoring/host-proc/stats  ${enclave_name}_logs/host-proc-data
elif [ "$metrics_infra" = "container-proc" ]; then
    echo "Waiting monitoring to finish ..."
    wait $monitor_pid
    echo "Copying the container-proc measurements"
    cp ./monitoring/container-proc/cproc_metrics.json "./${enclave_name}_logs/cproc_metrics.json" > /dev/null 2>&1
    # \rm -r ./monitoring/container-proc/cproc_metrics.json > /dev/null 2>&1
fi

echo "- Metrics Infra:  $metrics_infra" > ./${enclave_name}_logs/run_args
echo "- Enclave name:  $enclave_name" >> ./${enclave_name}_logs/run_args
echo "- Configuration file:  $wakurtosis_config_file" >> ./${enclave_name}_logs/run_args

# Copy simulation results
docker cp "$wls_cid:/wls/network_topology/network_data.json" "./${enclave_name}_logs"
docker cp "$wls_cid:/wls/messages.json" "./${enclave_name}_logs"
docker cp "$wls_cid:/wls/prometheus_data.json" "./${enclave_name}_logs"

# Copy collectnet files. as required
docker cp "$collnet_cid:/collectnet/observed_network.json" "./${enclave_name}_logs"
collectnet_debug=`jq '.kurtosis.collectnet.debug'  config/config.json`
if [ "$collectnet_debug" = "true" ]; then
  docker cp "$collnet_cid:/collectnet/debug-observed_network.json" "./${enclave_name}_logs"
fi

# Run analysis
if jq -e ."plotting" >/dev/null 2>&1 "./config/${wakurtosis_config_file}"; then
    if [ "$metrics_infra" = "dstats" ]; then
        docker run --name "dstats" --network "host" -v "$(pwd)/wakurtosis_logs:/simulation_data/" --add-host=host.docker.internal:host-gateway analysis src/hproc.py dstats /simulation_data/ --config-file /simulation_data/config/config.json  >/dev/null 2>&1
        docker cp dstats:/analysis/plots/ wakurtosis_logs/dstats-plots
        cd wakurtosis_logs
        ln -s dstats-plots/output-dstats-compare.pdf analysis.pdf
        cd ..
    elif [ "$metrics_infra" = "host-proc" ]; then
        docker run --name "host-proc" --network "host" -v "$(pwd)/wakurtosis_logs:/simulation_data/" --add-host=host.docker.internal:host-gateway analysis src/hproc.py host-proc /simulation_data/ --config-file /simulation_data/config/config.json  >/dev/null 2>&1
        docker cp host-proc:/analysis/plots/ wakurtosis_logs/host-proc-plots
        cd wakurtosis_logs
        ln -s host-proc-plots/output-host-proc-compare.pdf analysis.pdf
        cd ..
    elif [ "$metrics_infra" = "container-proc" ]; then
        docker run --network "host" -v "$(pwd)/wakurtosis_logs:/simulation_data/" --add-host=host.docker.internal:host-gateway analysis src/main.py -i container-proc >/dev/null 2>&1
    elif [ "$metrics_infra" = "cadvisor" ]; then
        prometheus_port=$(grep "\<prometheus\>" $kurtosis_inspect | awk '{print $6}' | awk -F':' '{print $2}')
        docker run --network "host" -v "$(pwd)/wakurtosis_logs:/simulation_data/" --add-host=host.docker.internal:host-gateway analysis src/main.py -i cadvisor -p "$prometheus_port" >/dev/null 2>&1
    fi
fi

echo "Done."
##################### END
