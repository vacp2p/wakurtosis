import os
import fcntl
import asyncio
import aiodocker
import subprocess
import time
import re
import json

# Will filter containers based on the following sting
G_CONTAINER_NAME_PATTERN = "waku"

# Will filter processses within the containers based on the following sting
G_PROCESS_NAME_PATTERN = "waku"

# Time in seconds between samples
G_SAMPLING_INTERVAL = 10
G_DEFAULT_SIMULATION_PATH = './wakurtosis_logs'
G_DEFAULT_METRICS_FILENAME = 'metrics.log'

async def run_command(command):
    proc = await asyncio.create_subprocess_shell(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    
    return stdout.decode().strip()

async def find_processes(container_name_or_id, process_name):
    command = f"docker exec {container_name_or_id} ps -eo pid,comm,args | grep {process_name} | grep -v grep"
    process_list = await run_command(command)
    process_info = []

    for line in process_list.split('\n'):
        if line.strip():
            parts = line.split(maxsplit=2)
            pid, name, binary = parts[0], parts[1], parts[2]
            process_info.append({"pid": pid, "name": name, "binary": binary})

    return process_info

async def get_process_stats_fast(container_name_or_id, pid, nsenter_prefix=None):
    
    if not nsenter_prefix:
        
        # Cache the nsenter command prefix for future use
        command = f"docker inspect -f '{{{{.State.Pid}}}}' {container_name_or_id}"
        container_pid = await run_command(command)
        nsenter_prefix = f"sudo nsenter -t {container_pid} -n -m -u -i -p"

    try:
        stats_cmd = f"{nsenter_prefix} sh -c 'cat /proc/{pid}/net/dev | grep eth0 | awk {{print $$2, $$10}} && \
                    cat /proc/stat | grep ^cpu && \
                    cat /proc/{pid}/stat | awk {{print $$14, $$15, $$16, $$17}} && \
                    cat /proc/{pid}/statm && \
                    cat /proc/{pid}/io'"
        
        output = await run_command(stats_cmd)
    except Exception as e:
        print(f"Error running command '{command}': {e}")
        return None

    print('-->', stats_cmd)
    print('-->', output)

    # Parse the output of the stats command
    network_rx, network_tx = map(int, output.splitlines()[0].split())
    cpu_stats = list(map(int, output.splitlines()[1].split()[1:]))
    process_cpu_stats = list(map(int, output.splitlines()[2].split()))
    size, resident, shared, text, lib, data, dt = map(int, output.splitlines()[3].split())
    io_rchar, io_wchar = map(int, re.findall(r'(?<=rchar: )[0-9]+|(?<=wchar: )[0-9]+', output.splitlines()[4]))

    # Calculate the process's CPU usage percentage
    total_cpu_time = sum(cpu_stats)
    process_cpu_time = sum(process_cpu_stats)
    cpu_percentage = (process_cpu_time / total_cpu_time) * 100

    # Convert stats to MBytes
    network_rx_mbytes = network_rx / (1024.0 * 1024.0)
    network_tx_mbytes = network_tx / (1024.0 * 1024.0)
    memory_usage_mb = (resident * 4096) / (1024 * 1024)
    io_read_mbytes = io_rchar / (1024 * 1024)
    io_write_mbytes = io_wchar / (1024 * 1024)

    result = {
        "network_io_mbytes": {'rx': network_rx_mbytes, 'tx': network_tx_mbytes},
        "cpu_percentage": cpu_percentage,
        "memory_usage_mbytes": memory_usage_mb,
        "disk_io_mbytes": {'read': io_read_mbytes, 'write': io_write_mbytes}
    }

    return result

async def get_process_stats(container_name_or_id, pid):
    
    # print('--> Container: ', container_name_or_id, ' PID: ', pid)
    
    command = f"docker inspect -f '{{{{.State.Pid}}}}' {container_name_or_id}"
    container_pid = await run_command(command)
    nsenter_prefix = f"sudo nsenter -t {container_pid} -n -m -u -i -p"

    # Netowrk IO
    network_rx, network_tx = 0, 0
    network_stats_cmd = f"{nsenter_prefix} cat /proc/{pid}/net/dev | grep eth0 | awk '{{print $2, $10}}'"
    # print(network_stats_cmd)
    try:
        network_rx, network_tx = map(int, (await run_command(network_stats_cmd)).split())
    except ValueError as e:
        print(f"Error while parsing network stats: {e}")
        print(f"Command output: {await run_command(network_stats_cmd)}")
    # print(network_rx, network_tx)

    network_rx_mbytes = network_rx / (1024.0 * 1024.0)
    network_tx_mbytes = network_tx / (1024.0 * 1024.0)

    # CPU times
    cpu_stats_cmd =  f"{nsenter_prefix} cat /proc/stat | grep '^cpu '"
    # print(cpu_stats_cmd)
    try:

        # Get overall CPU usage from /proc/stat
        overall_cpu_usage_cmd = f"{nsenter_prefix} cat /proc/stat | grep '^cpu '"
        overall_cpu_times = await run_command(overall_cpu_usage_cmd)
        overall_cpu_times = list(map(int, overall_cpu_times.split()[1:]))
        total_cpu_time = sum(overall_cpu_times)

        # Get process CPU usage from /proc/[pid]/stat
        process_cpu_usage_cmd = f"{nsenter_prefix} cat /proc/{pid}/stat | awk '{{print $14, $15, $16, $17}}'"
        process_cpu_times = await run_command(process_cpu_usage_cmd)
        process_cpu_times = list(map(int, process_cpu_times.split()))
        process_cpu_time = sum(process_cpu_times)

        # Calculate the process's CPU usage percentage
        cpu_percentage = (process_cpu_time / total_cpu_time) * 100

    except ValueError as e:
        print(f"Error while parsing cpu_stats: {e}")
        print(f"Command output: {await run_command(cpu_stats_cmd)}")
    # print(utime, stime, cutime, cstime)

    # Memory
    size, resident, shared, text, lib, data, dt = 0, 0, 0, 0, 0, 0, 0
    memory_stats_cmd = f"{nsenter_prefix} cat /proc/{pid}/statm"
    # print(memory_stats_cmd)
    try:
        size, resident, shared, text, lib, data, dt = map(int, (await run_command(memory_stats_cmd)).split())
        memory_usage_mb = (resident * 4096) / (1024 * 1024)
    except ValueError as e:
        print(f"Error while parsing memory_stats: {e}")
        print(f"Command output: {await run_command(memory_stats_cmd)}")
    # print(size, resident, shared, text, lib, data, dt)

    # DISK IO of the process in MBytes? # Disk IO   
    io_rchar, io_wchar = 0, 0
    io_stats_cmd = f"{nsenter_prefix} cat /proc/{pid}/io"
    # print(io_stats_cmd)
    try:
        io_rchar, io_wchar = map(int, re.findall(r'(?<=rchar: )[0-9]+|(?<=wchar: )[0-9]+', await run_command(io_stats_cmd)))
    except ValueError as e:
        print(f"Error while parsing io_stats: {e}")
        print(f"Command output: {await run_command(io_stats_cmd)}")
    # print(io_rchar, io_wchar)

    # Convert disk I/O to MBytes
    io_read_mbytes = io_rchar / (1024 * 1024)
    io_write_mbytes = io_wchar / (1024 * 1024)

    result = {
        "network_io_mbytes": {'rx' : network_rx_mbytes, 'tx' : network_tx_mbytes},
        "cpu_percentage": cpu_percentage,
        "memory_usage_mbytes": memory_usage_mb,
        "disk_io_mbytes": {'read' : io_read_mbytes, 'write' : io_write_mbytes}
    }

    return result

async def list_containers(image_name):
    
    command = "docker ps --format '{{.ID}},{{.Names}},{{.Image}},{{.State}}'"
    
    container_info = await run_command(command)

    # Check if the output is empty or contains only whitespace
    if not container_info.strip():  
        return []

    container_list = []
    for line in container_info.split('\n')[:-1]:
        container_id, container_name, container_image, container_state = line.split(',')
        # Filter containers based on image_name
        if image_name in container_image:
            container_list.append({"id": container_id, "name": container_name, "image": container_image, "state": container_state})

    return container_list

async def container_events(image_pattern):
    
    async with aiodocker.Docker() as docker:
        
        events = docker.events.subscribe(filters={"event": ["start", "die"]})
        
        # Wait for container events ...
        while True:
            
            event = await events.get()
            
            if event.get('Type') == 'container':

                container_image = event.get('Actor').get('Attributes').get('image')
                
                if image_pattern in container_image:
                                    
                    action = event.get('Action')

                    return action
                    
            await asyncio.sleep(0.1)
            
            return None

async def monitor_container(container_id, container_name, container_image_name, wsl_pattern, processes):
    
    nonce = 0
    samples = []
     
    while True:
        
        start_time = time.perf_counter()
        
        # print(nonce, ' Container: ', container_id, ' Processes: ', processes)

        for process in processes:
            
            # print('Sampling process: ', process['pid'])
            
            pid = process["pid"]

            process_stats = await get_process_stats(container_id, pid)

            stats_sample = {
                
                "timestamp": time.time_ns(),
                "nonce": nonce,
                "container_id": container_id,
                "container_name": container_name,
                "container_image": container_image_name,
                "pid": pid,
                "process_name": process['name'],
                "process_binary": process['binary'],
                "network_io_mbytes": process_stats['network_io_mbytes'],
                "cpu_percentage": process_stats["cpu_percentage"],
                "memory_usage_mbytes": process_stats["memory_usage_mbytes"],
                "disk_io_mbytes": process_stats['disk_io_mbytes']
            }

            # print(stats_sample)

            # Not the most efficient way to store the data, but much faster than dumping to disk
            samples.append(stats_sample)

            nonce += 1

        # Sleep for the remaining time in the interval
        elapsed_time = time.perf_counter() - start_time
        delta_t =  G_SAMPLING_INTERVAL - elapsed_time

        if delta_t < 0:
            print('Warning: Monitoring took longer than the interval. Consider increasing the interval.')
        # else:
        #     print('Sleeping for %d ms (elapsed: %d ms)' %(delta_t * 1000, elapsed_time * 1000))

        # Pool WSL events during the delta time
        try:
            wsl_status = await asyncio.wait_for(container_events(wsl_pattern), timeout=max(0, delta_t))
            # We only care about the WSL container stops
            if wsl_status == 'die':
                break
        except asyncio.TimeoutError:
            pass

    # Dump samples to disk
    print('Dumping %d samples to disk ...' %(len(samples)))
    metrics_file_path = './%s' %(G_DEFAULT_METRICS_FILENAME)
    with open(metrics_file_path, "a") as f:
        
        # Get a lock on the file
        fcntl.flock(f, fcntl.LOCK_EX) 
        
        for sample in samples:
            json.dump(sample, f)
            f.write('\n')
        
        # Release the lock
        fcntl.flock(f, fcntl.LOCK_UN) 
        
    print('Stopped monitoring container %s. %d samples taken' %(container_name, nonce))

async def main():

    wsl_pattern = 'wsl'
    
    # Wait for the specific container to be running
    print(f"Waiting for container with name '{wsl_pattern}' to start...")
    container_status = None
    while container_status is None:
        container_status = await container_events(wsl_pattern)
        # await asyncio.sleep(1)
    
    print(f"Container '{wsl_pattern}' is running. Starting monitoring...")
    
    # Retrieve the list of containers to monitor
    containers = await list_containers(G_CONTAINER_NAME_PATTERN)
    print('Monitoring %d containers: %s' % (len(containers), containers))

    # Pre-fetch the processes for each container
    container_processes = {}
    for container in containers:
        container_id = container['id']
        processes = await find_processes(container_id, G_PROCESS_NAME_PATTERN)
        container_processes[container_id] = processes
    
    # Start monitoring (this will block until tasks are finished)
    tasks = [monitor_container(container['id'], container['name'], container['image'], wsl_pattern, container_processes[container['id']]) for container in containers]
    await asyncio.gather(*tasks)

    print('Monitoring finished.')
        
if __name__ == "__main__":
    
    # Clear the metrics file
    if os.path.exists(G_DEFAULT_METRICS_FILENAME):
        os.remove(G_DEFAULT_METRICS_FILENAME)

    asyncio.run(main())
