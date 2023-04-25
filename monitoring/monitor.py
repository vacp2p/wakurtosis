#!/usr/bin/env python3

"""
Description: Wakurtosis process level monitoring tool

"""

import os, sys, time, io, tarfile, json, re, asyncio, subprocess, pickle, logging
import docker
import aiodocker
from docker.errors import NotFound
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures

""" Globals """
G_APP_NAME = 'WLS-MONITOR'
G_LOG_LEVEL = 'INFO'
G_DEFAULT_CONFIG_FILE = './config/config.json'
# G_DEFAULT_SIMULATION_PATH = './wakurtosis_logs'
# G_DEFAULT_METRICS_FILENAME = './monitoring/metrics.json'

G_LOGGER = None

""" Custom logging formatter """
class CustomFormatter(logging.Formatter):
    
    # Set different formats for every logging level
    time_name_stamp = "[%(asctime)s.%(msecs)03d] [" + G_APP_NAME + "]"
    FORMATS = {
        logging.ERROR: time_name_stamp + " ERROR in %(module)s.py %(funcName)s() %(lineno)d - %(msg)s",
        logging.WARNING: time_name_stamp + " WARNING - %(msg)s",
        logging.CRITICAL: time_name_stamp + " CRITICAL in %(module)s.py %(funcName)s() %(lineno)d - %(msg)s",
        logging.INFO:  time_name_stamp + " %(msg)s",
        logging.DEBUG: time_name_stamp + " %(funcName)s() %(msg)s",
        'DEFAULT': time_name_stamp + " %(msg)s",
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno, self.FORMATS['DEFAULT'])
        formatter = logging.Formatter(log_fmt, '%d-%m-%Y %H:%M:%S')
        return formatter.format(record)

async def signal_wsl(wsl_container):
    
    G_LOGGER.info(f'Signalling WSL container {wsl_container.id} to start the simulation ...')

    command = f"docker exec {wsl_container.id} touch /wls/start.signal"
    G_LOGGER.debug('Executing command: %s' %command)
    
    result = await run_command(command)

async def run_command(command):

    G_LOGGER.debug('Executing command: %s' %command)

    proc = await asyncio.create_subprocess_shell(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    
    return stdout.decode().strip()

async def is_container_running(container_id):
    
    async with aiodocker.Docker() as docker:
        try:
            container = docker.containers.container(container_id)
            container_info = await container.show()
            container_status = container_info.get("State", {}).get("Status", "")
            return container_status == "running"
        except aiodocker.exceptions.DockerError:
            # Container not found or an error occurred
            return False

async def get_running_container_id(image_pattern):
    
    async with aiodocker.Docker() as docker:
        
        all_containers = await docker.containers.list(all=True)

        for container in all_containers:
            try:
                container_info = await container.show()
            except aiodocker.exceptions.DockerError as e:
                if e.status == 404:
                    # Container not found, continue with the next container
                    continue
                else:
                    raise e  # Re-raise the exception if it's not a 404 error

            container_image = container_info.get("Config", {}).get("Image", "")
            container_status = container_info.get("State", {}).get("Status", "")

            if image_pattern in container_image:
                if container_status == "running":
                    return container_info.get("Id"), container

    return None, None

async def find_processes(container_name_or_id, process_name):
    
    command = f"docker exec {container_name_or_id} ps -eo pid,comm,args | grep {process_name} | grep -v grep"
    process_list = await run_command(command)
    process_info = []

    for line in process_list.split('\n'):
        if line.strip():
            parts = line.split(maxsplit=2)
            pid, name, binary = parts[0], parts[1], parts[2]
            process_info.append({"pid": int(pid), "name": name, "binary": binary})

    return process_info

def inject_probes(script_name, script_tar_data, containers_data_list, sampling_interval, num_threads=16):
    
    start_time = time.time()
    
    probe_pids = []

    def inject_probe(container_data):
        
        pids = [process['pid'] for process in container_data['processes']]
        
        container = container_data['container']
        
        try:
            G_LOGGER.debug('Injecting probe in container %s for PIDs: %s' %(container.id, pids))

            # Copy the probe script file to the container
            container.put_archive('/tmp', script_tar_data.getvalue())

            # Start the probe script in the container
            command = f'/bin/sh /tmp/{script_name} {sampling_interval} {" ".join(map(str, pids))}'

            container.exec_run(cmd=command, stdout=False, stderr=False, detach=True, tty=False)
            pid_tar_stream, _ = container.get_archive('/tmp/pid.tmp')
            
            # Retrieve the probe PID from the container
            with io.BytesIO() as pid_data:
                for chunk in pid_tar_stream:
                    pid_data.write(chunk)
                pid_data.seek(0)
                
                with tarfile.open(fileobj=pid_data) as pid_tar:
                    pid_file = pid_tar.extractfile('pid.tmp')
                    process_pid = pid_file.read().strip().decode('utf-8')
                    probe_pids.append(process_pid)
        
        except Exception as e:
            G_LOGGER.error(f"An error occurred while executing the script in container {container.id}: {e}")

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        
        futures = [executor.submit(inject_probe, container_data) for container_data in containers_data_list]
        
        for future in futures:
            future.result()

    G_LOGGER.info('Injected probe into %d containers in %d ms.' %(len(probe_pids), (time.time() - start_time) * 1000))
    
    return probe_pids
            
def parse_net_stats(output):
    
    interface_pattern = r"(\w+):\s+((\d+\s+){15}\d+)"
    matches = re.finditer(interface_pattern, output)

    net_stats = {'all': {}, 'interface': []}
    total_received = 0
    total_sent = 0

    for match in matches:
        
        interface_name = match.group(1)
        stats_values = match.group(2).split()

        receive_stats = {
            "bytes": int(stats_values[0]),
            "packets": int(stats_values[1]),
            "errs": int(stats_values[2]),
            "drop": int(stats_values[3]),
        }

        transmit_stats = {
            "bytes": int(stats_values[8]),
            "packets": int(stats_values[9]),
            "errs": int(stats_values[10]),
            "drop": int(stats_values[11]),
        }

        # Update total_received and total_sent
        total_received += int(stats_values[0])
        total_sent += int(stats_values[8])

        net_stats['interface'].append({
            "name": interface_name,
            "receive": receive_stats,
            "transmit": transmit_stats,
        })

    # Store the totals in the 'all' key
    net_stats['all'] = {
        "total_received": total_received,
        "total_sent": total_sent,
    }

    return net_stats

def gather_probes(containers_data, probes_ids, num_threads=16):
    
    start_time = time.time()

    G_LOGGER.info('Gathering probes from %d containers...' % len(containers_data))

    # Ensure that the ./metrics directory exists
    metrics_dir = './metrics'
    if not os.path.exists(metrics_dir):
        os.makedirs(metrics_dir)

    all_containers_metrics = {}

    def gather_probe(container_data, process_id):
        
        container = container_data['container']
        
        G_LOGGER.debug('Gathering probe from container %s' % container.id)
        
        # Stop the script execution by sending a SIGINT signal
        container.exec_run(cmd=f'kill -INT {process_id}', tty=True)
        
         # Retrieve the metrics.json file from the containers and store it in the host
        try:
            metrics_tar_stream, _ = container.get_archive('/tmp/metrics.json')
            with io.BytesIO() as metrics_data:
                
                for chunk in metrics_tar_stream:
                    metrics_data.write(chunk)
                metrics_data.seek(0)

                with tarfile.open(fileobj=metrics_data) as metrics_tar:
                    metrics_json_file = metrics_tar.extractfile('metrics.json')

                    # Save metrics.json to the local path
                    # local_file_path = os.path.join('./monitoring/', f"{container.id}_metrics.json")
                    # with open(local_file_path, "wb") as local_file:
                    #     local_file.write(metrics_json_file.read())

                    # Reset the file pointer to the beginning
                    # metrics_json_file.seek(0)

                    # Parse NetStats
                    container_metrics = []
                    max_nonce = 0
                    for line in metrics_json_file:
                        line = line.decode('utf-8').strip()
                        try:
                            json_line = json.loads(line)
                            json_line['NetStats'] = parse_net_stats(json_line['NetStats'])
                            container_metrics.append(json_line)
                            max_nonce = max(max_nonce, json_line['Nonce'])
                        except json.JSONDecodeError as e:
                            G_LOGGER.error(f"Error parsing JSON line: {line}\nError: {e}")
                    
                    # We dont need this
                    container_data.pop("container")
                    
                    # Convert the container image name to string
                    container_data['container_image_name'] = str(container_data['container_image_name'])
                    container_data['max_nonce'] = max_nonce
                    
                    all_containers_metrics[container.id] = {'info' : container_data, 'samples' : container_metrics}

        except NotFound:
            G_LOGGER.error(f"metrics.json not found in container {container.id}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = []
        for container_data, process_id in zip(containers_data, probes_ids):
            futures.append(executor.submit(gather_probe, container_data, process_id))

        for future in concurrent.futures.as_completed(futures):
            
            # Handle any exceptions that might have occurred during the execution of the task
            if future.exception() is not None:
                G_LOGGER.error(f"An exception occurred: {future.exception()}")

    G_LOGGER.info('Gather probe from %d containers took %d ms.' % (len(probes_ids), (time.time() - start_time) * 1000))

    print('all_containers_metrics: %d' % len(all_containers_metrics))

    return all_containers_metrics

def save_metrics_to_disk(metrics, filename):

    # with open(filename, 'wb') as f:  # Use 'wb' mode for writing binary data
    #     pickle.dump(metrics, f)
    
    with open(filename, 'w') as f:
        json.dump(metrics, f, indent=4)

def main():

    global G_LOGGER
    
    """ Init Logging """
    G_LOGGER = logging.getLogger(G_APP_NAME)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(CustomFormatter())
    G_LOGGER.addHandler(handler)

    # Set loglevel
    G_LOGGER.setLevel(G_LOG_LEVEL)
    handler.setLevel(G_LOG_LEVEL)

    G_LOGGER.info('Started')

    """ Load config file """
    try:
        with open(G_DEFAULT_CONFIG_FILE, "r") as read_file:
            config_obj = json.load(read_file)
            config_obj = config_obj['monitoring']

    except Exception as e:
        G_LOGGER.error('%s: %s' % (e.__doc__, e))
        sys.exit()

    G_LOGGER.info('Loaded configuration from %s' %G_DEFAULT_CONFIG_FILE)

    # Prepare the sampling probe we are going to inject into the containers
    script_tar_data = io.BytesIO()
    with tarfile.open(fileobj=script_tar_data, mode='w') as tar:
        tar.add(config_obj['probe_filename'], arcname=os.path.basename(config_obj['probe_filename']))
    script_tar_data.seek(0)

    # Wait for the simulation to start
    G_LOGGER.info(f"Waiting for WSL to start...")
    wsl_id, wsl_container = asyncio.run(get_running_container_id(config_obj['wsl_pattern']))
    while wsl_id is None:
        wsl_id, wsl_container  = asyncio.run(get_running_container_id(config_obj['wsl_pattern']))
        time.sleep(1)

    G_LOGGER.info('Found container with name \'%s\'.' %config_obj['wsl_pattern'])

    # Get all running containers
    client = docker.from_env()
    containers = client.containers.list()

    # Filter the containers that match the container_str_pattern
    node_containers = [container for container in containers if config_obj['container_str_pattern'] in container.image.tags[0]]
    if len(node_containers) == 0:
        G_LOGGER.error('No containers found matching \"%s\".' %config_obj['container_str_pattern'])
        exit(1)

    # Pre-fetch the processes from each container
    containers_data = []
    for container in node_containers:
       
        container_id = container.id
       
        processes = asyncio.run(find_processes(container_id, config_obj['container_str_pattern']))
       
        container_data = {
            "container" : container,
            "container_id": container_id,
            "container_name": container.name,
            "container_image_name": container.image,
            "processes": processes
        }
        containers_data.append(container_data)
    

    G_LOGGER.info('Injecting probes into %d containers' % len(node_containers))
        
    # Start the script in the target containers 
    probes_ids = inject_probes(os.path.basename(config_obj['probe_filename']), script_tar_data, containers_data, config_obj['sampling_interval_s'])
        
    # Notify the simulation that the probes are ready
    asyncio.run(signal_wsl(wsl_container))

    # Start the timer
    start_ts = time.time_ns()

    # Wait for simulation to finish
    G_LOGGER.info('Waiting for simulation to finish...')
    wsl_status = True
    while wsl_status:
        
       # Check if WSL is still running, and break the loop if not
        wsl_status = asyncio.run(is_container_running(wsl_id))
        if not wsl_status:
            break

        time.sleep(1)
        
    end_ts = time.time_ns()
    
    # Stop probes and gather metrics
    all_container_metrics = gather_probes(containers_data, probes_ids)

    header = {'elapsed_ns' : end_ts - start_ts, 'sampling_interval_s' : config_obj['sampling_interval_s'], 'start_ts' : start_ts, 'end_ts' : end_ts, \
              'num_containers' : len(node_containers), 'probe' : config_obj['probe_filename'], 'container_str_pattern' : config_obj['container_str_pattern'], \
              'process_str_pattern' : config_obj['process_str_pattern']}
    save_metrics_to_disk({'header' : header, 'containers' : all_container_metrics}, config_obj['metrics_filename'])

    """ We are done """
    G_LOGGER.info('Ended')

if __name__ == '__main__':
    main()