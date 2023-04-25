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
  echo "Received a signal, saving remaining data and exiting..."
  if [ -n "$BUFFER" ]; then
    echo -n "$BUFFER" >> "$METRICS_FILE"
    sync
  fi
  exit 0
}

get_valid_pids() {
  input_pids="$1"
  valid_pids=""
  for pid in $input_pids; do
    if [ -e /proc/$pid/stat ] && [ -e /proc/$pid/io ] && [ -e /proc/$pid/net/dev ]; then
      valid_pids="${valid_pids} ${pid}"
    fi
  done
  echo "$valid_pids"
}

get_uptime_ms() {
  cat /proc/uptime | awk '{print $1 * 1000}'
}

get_cpu_total() {
  awk '/^cpu / {for (i=2; i<=NF; i++) total_cpu+=$i} END {print total_cpu}' /proc/stat
}

get_process_info() {
  pid=$1
  total_cpu=$2
  awk -v pid=$pid -v total_cpu=$total_cpu '
    $1 == pid {process_cpu=$14+$15+$16+$17; resident=$24; cpu_percentage=(process_cpu/total_cpu)*100; memory_usage_mb=(resident*4096)/(1024*1024)}
    /rchar:/ {rchar=$2}
    /wchar:/ {wchar=$2}
    END {print process_cpu, resident, rchar, wchar, cpu_percentage, memory_usage_mb}' \
    /proc/$pid/stat /proc/$pid/io
}

calculate_pid_metrics() {
  pid=$1
  total_cpu_time=$2

  read -r process_cpu_time resident io_rchar io_wchar cpu_percentage memory_usage_mb \
    < <(get_process_info $pid $total_cpu_time)

  pid_network_info=$(cat /proc/$pid/net/dev)
  clean_pid_network_info=$(echo "$pid_network_info " | tr -d '\"' | tr -s '[:blank:]' ' ' | tr -d '\n')

  echo "{ \"Timestamp\": $(date +%s), \"Nonce\": $nonce, \"PID\": $pid, \"NetStats\": \"$clean_pid_network_info\", \"MemoryUsageMB\": $memory_usage_mb, \"CPUPercentage\": $cpu_percentage, \"DiskIORChar\": $io_rchar, \"DiskIOWChar\": $io_wchar, \"LastElapsed\": $elapsed_time_ms}"
}

# Export the calculate_pid_metrics function
export -p calculate_pid_metrics total_cpu_time get_process_info
 
# Set number of parallel processes
num_procs=4

main() {
  time_interval="$1"
  shift
  pids="$@"

  # Check the PIDs actually exist
  valid_pids=$(get_valid_pids "$pids")
  
  nonce=0
  BUFFER=""
  elapsed_time_ms=0

  while true; do
    start_time_ms=$(get_uptime_ms)
    total_cpu_time=$(get_cpu_total)

    for pid in $valid_pids; do
      pid_metrics=$(calculate_pid_metrics $pid $total_cpu_time)$'\n'
      BUFFER="${BUFFER}${pid_metrics}"
    done

    nonce=$((nonce + 1))
    
    # Handle the output buffer
    if [ $((nonce % 25)) -eq 0 ]; then
      echo -n "$BUFFER" >> "$METRICS_FILE"
      BUFFER=""
      echo "Data saved at iteration $nonce"
      sync
    fi

    end_time_ms=$(get_uptime_ms)

    elapsed_time_ms=$(echo "$end_time_ms $start_time_ms" | awk '{printf "%.0f", ($1-$2)}')

    sleep_time_ms=$((time_interval * 1000 - elapsed_time_ms))
    # sleep_time_s=$((sleep_time_ms / 1000))
    # sleep_time_s=$(echo "scale=3; $sleep_time_ms / 1000" | bc)
    sleep_time_s=$(awk -v t=$sleep_time_ms 'BEGIN { print t / 1000 }')
    echo "Elapsed time: ${elapsed_time_ms}ms Sleeping for: ${sleep_time_s}s"

    # Sleep for the remaining time if any or warn if it's taking too long
    if [ $(expr $sleep_time_ms + 0) -gt 0 ]; then
      echo "Sleeping for $sleep_time_s seconds..."
      sleep "${sleep_time_s}"
    else
      echo "Warning: sampling is taking too long, consider reducing the time_interval"
    fi

    end_time_ms=$(get_uptime_ms)
    elapsed_time_ms=$(echo "$end_time_ms $start_time_ms" | awk '{printf "%.0f", ($1-$2)}')
    echo "Sample $nonce completed. Total elapsed time: ${elapsed_time_ms}ms"

  done

  exit 1
}

main "$@"

