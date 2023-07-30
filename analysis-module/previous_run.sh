
# Run analysis

#if jq -e ."plotting" >/dev/null 2>&1 "./config/${wakurtosis_config_file}"; then
#    if [ "$metrics_infra" = "dstats" ]; then
#        docker run --name "dstats" --network "host" -v "$(pwd)/wakurtosis_logs:/simulation_data/" --add-host=host.docker.internal:host-gateway analysis src/hproc.py dstats /simulation_data/ --config-file /simulation_data/config/config.json  >/dev/null 2>&1
#        docker cp dstats:/analysis/plots/ wakurtosis_logs/dstats-plots
#        cd wakurtosis_logs
#        ln -s dstats-plots/output-dstats-compare.pdf analysis.pdf
#        cd ..
#    elif [ "$metrics_infra" = "host-proc" ]; then
#        docker run --name "host-proc" --network "host" -v "$(pwd)/wakurtosis_logs:/simulation_data/" --add-host=host.docker.internal:host-gateway analysis src/hproc.py host-proc /simulation_data/ --config-file /simulation_data/config/config.json  >/dev/null 2>&1
#        docker cp host-proc:/analysis/plots/ wakurtosis_logs/host-proc-plots
#        cd wakurtosis_logs
#        ln -s host-proc-plots/output-host-proc-compare.pdf analysis.pdf
#        cd ..
#    elif [ "$metrics_infra" = "container-proc" ]; then
#        docker run --network "host" -v "$(pwd)/wakurtosis_logs:/simulation_data/" --add-host=host.docker.internal:host-gateway analysis src/main.py -i container-proc >/dev/null 2>&1
#    elif [ "$metrics_infra" = "cadvisor" ]; then
#        prometheus_port=$(grep "\<prometheus\>" $kurtosis_inspect | awk '{print $6}' | awk -F':' '{print $2}')
#        docker run --network "host" -v "$(pwd)/wakurtosis_logs:/simulation_data/" --add-host=host.docker.internal:host-gateway analysis src/main.py -i cadvisor -p "$prometheus_port" >/dev/null 2>&1
#    fi
#fi
