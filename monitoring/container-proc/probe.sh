#!/bin/sh

set -eu

# Define filename for metrics output
METRICS_FILE="/tmp/metrics.json"

# Save PID to file
echo "$$" > /tmp/pid.tmp

# Trap SIGINT and call exit_gracefully()
trap "exit_gracefully" INT TERM KILL

exit_gracefully() {
  # End JSON list output
  # echo "]" >> "$METRICS_FILE"
  exit 0
}

# Variables:
#   time_interval - time interval between iterations (passed as an argument)
#   pids - a space-separated list of process IDs to monitor

# Parse arguments
time_interval="$1"
shift
pids="$@"

# Start sampling
nonce=0
# Begin JSON list output
# echo "[" >> "$METRICS_FILE"

while true; do
  start_time=$(date +%s%3N)

  for pid in $pids; do
    
    # Parse Network IO for the given PID
    pid_network_info=$(cat /proc/$pid/net/dev)

    # Clean up the pid_network_info string
    clean_pid_network_info=$(echo "$pid_network_info " | tr -d '\"' | tr -s '[:blank:]' ' ' | tr -d '\n')

    # CPU times, memory stats, and disk IO
    read -r total_cpu_time process_cpu_time resident io_rchar io_wchar \
      < <(awk -v pid=$pid '
        /^cpu / {for (i=2; i<=NF; i++) total_cpu+=$i}
        $1 == pid {process_cpu=$14+$15+$16+$17; resident=$24}
        /rchar:/ {rchar=$2}
        /wchar:/ {wchar=$2}
        END {print total_cpu, process_cpu, resident, rchar, wchar}' \
        /proc/stat /proc/$pid/stat /proc/$pid/io)

    # CPU usage
    cpu_percentage=$(echo "scale=8; ($process_cpu_time / $total_cpu_time) * 100" | bc | awk '{printf "%.8f", $0}')

    # Memory usage
    memory_usage_mb=$(echo "scale=2; ($resident * 4096) / (1024 * 1024)" | bc)

    # Output JSON object for the current PID
    echo "{ \"Timestamp\": $(date +%s), \"Nonce\": $nonce, \"PID\": $pid, \"NetStats\": \"$clean_pid_network_info\", \"MemoryUsageMB\": $memory_usage_mb, \"CPUPercentage\": $cpu_percentage, \"DiskIORChar\": $io_rchar, \"DiskIOWChar\": $io_wchar }" >> "$METRICS_FILE"
  done

  end_time=$(date +%s%3N)
  elapsed_time=$((end_time - start_time))
  # echo "Elapsed time: ${elapsed_time}ms" | tee -a "$METRICS_FILE"

  # Ensure the file is flushed at every iteration
  sync

  # Increment nonce by 1
  nonce=$((nonce + 1))

  sleep_time=$((time_interval - elapsed_time))
  if [ $sleep_time -gt 0 ]; then
    sleep $sleep_time
  fi

done

exit 1
