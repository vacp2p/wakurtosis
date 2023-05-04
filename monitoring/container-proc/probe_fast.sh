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
trap "exit_gracefully" SIGINT

exit_gracefully() {
  # End JSON list output
  echo "Received a signal, saving remaining data and exiting..."
  if [ -n "$BUFFER" ]; then
    echo -n "$BUFFER" >> "$METRICS_FILE"
    sync
  fi
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
BUFFER=""
sleep_time_ms=0
elapsed_time_ms=0

while true; do
  
  start_time=$(date +%s%N)
  echo start_time: $start_time

  total_cpu_time=$(awk '/^cpu / {for (i=2; i<=NF; i++) total_cpu+=$i} END {print total_cpu}' /proc/stat)

  for pid in $pids; do
    
    pid_start_time=$(date +%s%N)
    
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

      pid_elapsed_time_ns=$(( $(date +%s%N) - pid_start_time ))
      echo "Nonce: $nonce PID $pid: Elapsed: $pid_elapsed_time_ns ns."
  
      BUFFER="${BUFFER}{ \"Timestamp\": $(date +%s), \"Nonce\": $nonce, \"PID\": $pid, \"NetStats\": \"$clean_pid_network_info\", \"MemoryUsageMB\": $memory_usage_mb, \"CPUPercentage\": $cpu_percentage, \"DiskIORChar\": $io_rchar, \"DiskIOWChar\": $io_wchar, \"last_delta_ms\": $(printf "%.6f" $sleep_time_ms), \"elapsed_time_ms\": $(printf "%.6f" $elapsed_time_ms) }"$'\n'

    fi
  done

  nonce=$((nonce + 1))

  if [ $((nonce % 25)) -eq 0 ]; then
    echo -n "$BUFFER" >> "$METRICS_FILE"
    BUFFER=""
    echo "Data saved at iteration $nonce"
    sync
  fi

  end_time=$(date +%s%N)
  elapsed_time_ns=$((end_time - start_time))
  echo end_time: $end_time elapsed_time_ns: $elapsed_time_ns

  elapsed_time_ms=$(echo "scale=6; $elapsed_time_ns / 1000000" | bc)

  sleep_time_ns=$((time_interval * 1000000000 - elapsed_time_ns))
  sleep_time_ms=$(echo "scale=6; $sleep_time_ns / 1000000" | bc)
  sleep_time_s=$(echo "scale=6; $sleep_time_ms / 1000" | bc)
  sleep_time_s_rounded=$(printf "%.0f" $sleep_time_s)

  echo "Iteration $nonce completed. Elapsed time: ${elapsed_time_ns}ns Sleeping for: ${sleep_time_s_rounded}s"

  if [ $sleep_time_s_rounded -gt 0 ]; then
    echo "Sleeping for $sleep_time_s_rounded seconds..."
    sleep $sleep_time_s_rounded
  fi

done

exit 1
