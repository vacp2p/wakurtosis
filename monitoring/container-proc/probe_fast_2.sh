#!/bin/sh

set -eu

# Define filename for metrics output
METRICS_FILE="/tmp/metrics.json"

# Define filename for the log file
LOG_FILE="/tmp/metrics.log"

# Redirect stdout and stderr to the log file
exec > "$LOG_FILE" 2>&1

# Save PID to file
echo "$$" > /tmp/pid.tmp

# Trap SIGINT and call exit_gracefully()
trap "exit_gracefully" INT TERM 

exit_gracefully() {
  # End JSON list output
  echo "Received a signal, saving remaining data and exiting..."
  if [ -n "$BUFFER" ]; then
    echo -n "$BUFFER" >> "$METRICS_FILE"
    sync
  fi
  echo "Done."
  exit 0
}

get_uptime_ms() {
  cat /proc/uptime | awk '{print $1 * 1000}'
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
BUFFER=""
elapsed_time_ms=0

while true; do
  
  start_time_ms=$(get_uptime_ms)

  total_cpu_time=$(awk '/^cpu / {for (i=2; i<=NF; i++) total_cpu+=$i} END {print total_cpu}' /proc/stat)

  for pid in $pids; do
    
    if [ -e /proc/$pid/stat ] && [ -e /proc/$pid/io ] && [ -e /proc/$pid/net/dev ]; then
      read -r process_cpu_time resident io_rchar io_wchar \
        < <(awk -v pid=$pid '
          $1 == pid {process_cpu=$14+$15+$16+$17; resident=$24}
          /rchar:/ {rchar=$2}
          /wchar:/ {wchar=$2}
          END {print process_cpu, resident, rchar, wchar}' \
          /proc/$pid/stat /proc/$pid/io)

      cpu_percentage=$(echo "scale=8; ($process_cpu_time / $total_cpu_time) * 100" | bc | awk '{printf "%.8f", $0}')
      memory_usage_mb=$(echo "scale=2; ($resident * 4096) / (1024 * 1024)" | bc)

      pid_network_info=$(cat /proc/$pid/net/dev)
      clean_pid_network_info=$(echo "$pid_network_info " | tr -d '\"' | tr -s '[:blank:]' ' ' | tr -d '\n')

      BUFFER="${BUFFER}{ \"Timestamp\": $(date +%s), \"Nonce\": $nonce, \"PID\": $pid, \"NetStats\": \"$clean_pid_network_info\", \"MemoryUsageMB\": $memory_usage_mb, \"CPUPercentage\": $cpu_percentage, \"DiskIORChar\": $io_rchar, \"DiskIOWChar\": $io_wchar, \"LastElapsed\": $elapsed_time_ms}"$'\n'
    fi
  done

  nonce=$((nonce + 1))
  if [ $((nonce % 25)) -eq 0 ]; then
    echo -n "$BUFFER" >> "$METRICS_FILE"
    BUFFER=""
    echo "Data saved at iteration $nonce"
    sync
  fi

  end_time_ms=$(get_uptime_ms)
  # elapsed_time_ms=$(echo "$end_time_ms - $start_time_ms" | bc)
  elapsed_time_ms=$(echo "$end_time_ms $start_time_ms" | awk '{printf "%.0f", ($1-$2)}')
  
  sleep_time_ms=$(echo "scale=3; $time_interval * 1000 - $elapsed_time_ms" | bc)
  sleep_time_s=$(echo "scale=3; $sleep_time_ms / 1000" | bc)

  echo "Elapsed time: ${elapsed_time_ms}ms Sleeping for: ${sleep_time_s}s"

  if [ $(expr $sleep_time_ms + 0) -gt 0 ]; then
    echo "Sleeping for $sleep_time_s seconds..."
    sleep "${sleep_time_s}"
    # awk -v duration="$sleep_time_s" "BEGIN {sleep duration}"
  else
    echo "Warning: sampling is taking too long, consider reducing the time_interval"
  fi

  end_time_ms=$(get_uptime_ms)
  # elapsed_time_ms=$(echo "$end_time_ms - $start_time_ms" | bc)
  elapsed_time_ms=$(echo "$end_time_ms $start_time_ms" | awk '{printf "%.0f", ($1-$2)}')
  echo "Sample $nonce completed. Total elapsed time: ${elapsed_time_ms}ms"

done

exit 1