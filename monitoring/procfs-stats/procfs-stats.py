
import os, sys, pathlib
import threading, subprocess, signal

from collections import defaultdict

#from procfs import Proc
import sched, time
import typer

import logging as log


# TODO: return the CPU %s instead?
# pulls system-wide jiffies
def get_cpu_system(f):
    f.seek(0)
    rbuff = f.readlines()
    return f'{rbuff[0].strip()}'


# pulls per-process user/system jiffies
def get_cpu_process(f):
    f.seek(0)
    rbuff = f.read().strip().split()
    lst = [-3, -2]  # user jiffies, system jiffies
    return f'{rbuff[-3]} {rbuff[-2]}'


# pulls VmPeak, VmSize, VmRSS stats per wakunode
def get_mem_metrics(f):
    f.seek(0)
    rbuff = f.readlines()
    lst = [16, 17, 20, 21, 25, 26] #VmPeak, VmSize, VmHWM, VmRSS, VmData, VmStack
    out = [' '.join(rbuff[i].replace("\n", " ").replace(":", "").split()) for i in lst]
    res = ' '.join(out)
    return res


# pulls Rx/Tx Bytes and Packers per wakunode
def get_net1_metrics(f, host_if):
    f.seek(0)
    rbuff = f.readlines()
    out = [line.strip().split() for line in rbuff if "eth0" in line]        # docker
    if out == []:
        out = [line.strip().split() for line in rbuff if host_if in line]     # host
    out = out[0]
    res = f'{out[0]} RxBytes {out[1]} RxPackers {out[2]} TxBytes {out[9]} TxPackets {out[10]}'
    return res

# TODO: reconcile with net1 and net3
# pulls Rx/Tx Bytes per wakunode
def get_net2_metrics(f, veth="eth0"):
    f.seek(0)
    rbuff = f.readlines()
    ra = rbuff[3].split()
    res = f'InOctets {ra[7]} OutOctets {ra[8]}'
    return f'{veth} {res}'


# pulls Rx/Tx Bytes per wakunode
def get_net3_metrics(frx, ftx, veth="eth0"):
    frx.seek(0)
    ftx.seek(0)
    return f'{veth} NETRX {frx.read().strip()} NETWX {ftx.read().strip()}'


# pulls the disk read/write bytes per wakunodes
# TODO: demonise block reads: UNIX sockets/IPC/MSG QUEUES
def get_blk_metrics(f):
    f.seek(0)
    rbuff = f.readlines()
    lst = [4, 5]        #lst = [0, 1] if csize == 1 else [4, 5]
    res = ''.join([rbuff[i].replace("\n", " ").replace("259:0 ", "") for i in lst])
    return res


class MetricsCollector:
    def __init__(self, prefix, sampling_interval):
        self.prefix = prefix
        self.procfs_sampling_interval = sampling_interval
        self.pid2procfds = defaultdict(dict)

        self.docker_pids = []
        self.docker_pid2name = {}

        self.docker_ps_fname =  os.environ["DPS_FNAME"]
        self.docker_ids = []
        self.docker_name2id = {}

        self.ps_pids_fname = os.environ["PIDLIST_FNAME"]
        self.ps_pids = []

        self.docker_pid2veth_fname=os.environ["ID2VETH_FNAME"]
        self.docker_id2veth={}
        self.docker_pid2veth={}

        self.docker_pid2id = {}

        self.procout_fname = os.environ["PROCOUT_FNAME"]
        self.procfs_fd = ""
        self.procfs_scheduler = sched.scheduler(time.time, time.sleep)
        self.procfs_sample_cnt = 0

        self.host_if=os.environ["LOCAL_IF"]

        # self.container_id = -1 self.container_name = -1 self.cpu_usage = -1
        # self.mem_usage_abs = -1 self.mem_usage_perc = -1 self.net_sends = -1
        # self.net_recvs = -1 self.block_reads = -1 self.block_writes = -1

    # build, exec, and collect output
    def build_and_exec(self, cmd, fname):
        cmdline = f'exec {cmd} > {fname}'
        subprocess.run(cmdline, shell=True)

    # open the /proc files ahead to save up parsing, lookup, fd alloc etc.
    def populate_file_handles(self):
        assert self.docker_pid2name != {} and self.docker_name2id != {} and self.docker_pid2id != {}
        self.pid2procfds[0]["cpu"] =  open(f'/proc/stat')
        for pid in self.docker_pids:
            self.pid2procfds[pid]["cpu"] =  open(f'/proc/{pid}/stat')
            self.pid2procfds[pid]["mem"] =  open(f'/proc/{pid}/status')
            self.pid2procfds[pid]["net1"] =  open(f'/proc/{pid}/net/dev')
            self.pid2procfds[pid]["net2"] =  open(f'/proc/{pid}/net/netstat')
            self.pid2procfds[pid]["net3rx"] =  open(f'/sys/class/net/{self.docker_pid2veth[pid]}/statistics/rx_bytes')
            self.pid2procfds[pid]["net3tx"] =  open(f'/sys/class/net/{self.docker_pid2veth[pid]}/statistics/tx_bytes')
            #blk = ((f'/sys/fs/cgroup/blkio/docker'
            #        f'/{self.docker_pid2id[pid]}/'
            #        f'blkio.throttle.io_service_bytes'
            #     )) if self.csize == 1 else f'/proc/{pid}/io'
            self.pid2procfds[pid]["blk"] =  open(f'/proc/{pid}/io') # require SUDO
        self.procfs_fd = open(self.procout_fname, "w")

    # close all the opened file handles
    def teardown_file_handles(self):
        self.pid2procfds[0]["cpu"].close()
        for pid in self.docker_pids:
            self.pid2procfds[pid]["cpu"].close()
            self.pid2procfds[pid]["mem"].close()
            self.pid2procfds[pid]["net1"].close()
            self.pid2procfds[pid]["net2"].close()
            self.pid2procfds[pid]["net3rx"].close()
            self.pid2procfds[pid]["net3tx"].close()
            self.pid2procfds[pid]["blk"].close()
        self.procfs_fd.close()

    # the /proc reader : this is is in fast path
    def procfs_reader(self):
        for pid in self.docker_pids:
            veth = self.docker_pid2veth[pid]
            sys_stat = get_cpu_system(self.pid2procfds[0]["cpu"])
            stat = get_cpu_process(self.pid2procfds[pid]["cpu"])
            mem = get_mem_metrics(self.pid2procfds[pid]["mem"])
            net1 = get_net1_metrics(self.pid2procfds[pid]["net1"], self.host_if) # eth0 'in' docker?
            net2 = get_net2_metrics(self.pid2procfds[pid]["net2"], veth) # SNMP MIB
            net3 = get_net3_metrics(self.pid2procfds[pid]["net3rx"],
                    self.pid2procfds[pid]["net3tx"], veth) # sysfs/cgroup stats
            blk = get_blk_metrics(self.pid2procfds[pid]["blk"]) # Read, Write
            out = ( f'SAMPLE_{self.procfs_sample_cnt} '
                    f'{pid} {time.time()} '
                    f'MEM {mem} NET {net1} {net2} {net3} '
                    f'BLK {blk} CPU-SYS {sys_stat} CPU-process {stat}\n'
                  )
            self.procfs_fd.write(str(out))
        log.info("collected " + str(self.procfs_sample_cnt))
        self.procfs_sample_cnt += 1
        self.procfs_scheduler.enter(self.procfs_sampling_interval, 1, self.procfs_reader, ())

    # add headers and schedule /proc reader's first read
    def launch_procfs_monitor(self, wls_cid):
        self.populate_file_handles()    # including procout_fname
        self.procfs_fd.write((f'# procfs_sampling interval = {self.procfs_sampling_interval}\n'))
        self.procfs_fd.write(f'# {", ".join([f"{pid} = {self.docker_pid2id[pid]}" for pid in self.docker_pid2id])}\n')
        self.procfs_fd.write(f'# {", ".join([f"{pid} = {self.docker_pid2veth[pid]}" for pid in self.docker_pid2id])}\n')
        log.info("files handles populated")
        signal_wls = f'docker exec {wls_cid} touch /wls/start.signal'
        build_and_exec(signal_wls, "wls-signal")
        print(signal_wls)
        sys.exit(0)
        self.procfs_scheduler.enter(self.procfs_sampling_interval, 1,
                     self.procfs_reader, ())
        self.procfs_scheduler.run()

    # collect and record the basic info about the system and running dockers
    def populate_docker_name2id(self):
        #self.docker_ps_fname = f'{OPREFIX}-{docker_ps_fname}.{OEXT}'
        with open(self.docker_ps_fname) as f:
            for line in f:
                l = line.split("#")
                self.docker_name2id[l[1]] = l[0]
                self.docker_ids.append(l[0])

    # build the process pid to docker name map : will include non-docker wakunodes
    def build_pid2name_n(self):
        #self.ps_pids_fname = f'{OPREFIX}-{self.ps_pids_fname}.{OEXT}'
        with open(self.ps_pids_fname) as f:
            self.ps_pids = f.read().strip().split("\n")
        #log.info(f'docker: waku pids : {str(self.ps_pids)}')
        self.docker_pids = self.ps_pids
        for pid in self.docker_pids:
            get_shim_pid=((f'pstree -sg {pid} | '
                           f'head -n 1 | '
                           f'grep -Po "shim\([0-9]+\)---[a-z]+\(\K[^)]*"'
                         ))
            self.build_and_exec(get_shim_pid, f'shim-{pid}')
            with open(f'shim-{pid}') as f:
                shim_pid = f.read().strip()
                os.remove(f'shim-{pid}')
                if shim_pid == "":
                    dname = f'thundering_typhoons{pid}'
                    did = f'nondockerwakuPID{pid}'
                    self.docker_pid2name[pid] = dname
                    self.docker_name2id[dname] = did
                    self.docker_pid2id[pid] = did
                    self.docker_id2veth[did] = self.host_if
                    self.docker_pid2veth[pid] = self.host_if
                    continue
                get_docker_name = ((f'docker inspect --format '
                                    '"{{.State.Pid}}, {{.Name}}"'
                                    f' $(docker ps -q) | grep {shim_pid}'
                                  ))
                self.build_and_exec(get_docker_name, f'name-{pid}')
                with open(f'name-{pid}') as f:
                    tmp = f.read().strip().replace(" /", "")
                    pid, docker_name = tmp.split(",")
                    self.docker_pid2name[pid] = docker_name
                    os.remove(f'name-{pid}')


    # build the process pid to docker id map
    def build_docker_pid2id(self):
        self.docker_pid2id = {pid :
                self.docker_name2id[self.docker_pid2name[pid]] for pid in self.docker_pids}

    # build the pid to host side veth pair map
    def build_docker_pid2veth(self):
        with open(self.docker_pid2veth_fname) as f:
            for line in f.readlines():
                la = line.strip().split(":")
                self.docker_id2veth[la[0]]=la[1]
        self.docker_pid2veth = {pid :
                self.docker_id2veth[self.docker_pid2id[pid]] for pid in self.docker_pids}

    # build metadata for the runs: about docker, build name2id, pid2name and pid2id maps
    def process_metadata(self):
        self.populate_docker_name2id()
        self.build_pid2name_n()
        log.info(f'docker: waku pids : {str(self.docker_pids)}')
        self.build_docker_pid2id()
        self.build_docker_pid2veth()

    # after metadata is collected, create the threads and launch data collection
    def spin_up(self):
        log.info("Starting the procfs monitor...")
        self.launch_procfs_monitor()

    # kill docker stats : always kill, never TERM/QUIT/INT
    def terminate_docker_stats(self):
        log.info(f'stopping docker monitor : {self.docker_stats_pid}, {self.docker_stats_fname}')
        os.kill(self.docker_stats_pid, signal.SIGKILL) # do not use TERM/QUIT/INT

    # the cleanup: close the file handles and kill the docker
    def clean_up(self):
        self.teardown_file_handles()

    # register interruptible signals' handlers
    def register_signal_handlers(self):
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGQUIT, self.signal_handler)

    # the signal handler: does not return
    def signal_handler(self, sig, frame):
        log.info(f'Metrics: got signal: {sig}, cleaning up')
        self.clean_up()
        sys.exit(0)

# ensure sampling_interval > 0
def _sinterval_callback(ctx: typer, Context, sinterval: int):
    if sinterval <= 0 :
        raise ValueError(f"sampling_interval must be > 0")
    return sinterval

# does not return
def main(ctx: typer.Context,
        wls_cid: str = typer.Option("",
            help="Specify the WLS container id signal"),
        prefix: str = typer.Option("",
            help="Specify the path for find the data files"),
        local_if: str = typer.Option("eth0",
            help="Specify the local interface to account non-docker nw stats"),
        #container_size: int = typer.Option(1, callback=_csize_callback,
        #    help="Specify the number of wakunodes per container"),
        sampling_interval: int = typer.Option(1, callback=_sinterval_callback,
            help="Set the sampling interval in secs")):

    format = "%(asctime)s: %(message)s"
    log.basicConfig(format=format, level=log.INFO,
                        datefmt="%H:%M:%S")

    #pathlib.Path(ODIR).mkdir(parents=True, exist_ok=True)

    log.info("Metrics : Setting up")
    metrics = MetricsCollector(prefix=prefix, sampling_interval=sampling_interval)

    log.info("Metrics: Processing system and container metadata...")
    metrics.process_metadata()

    log.info("Metrics: Registering signal handlers...")
    metrics.register_signal_handlers()

    log.info("Metrics: Starting the data collection threads")
    metrics.spin_up(wls_cid)

    # get sim time info from config.json? or  ioctl/select from WLS? or docker wait?
    #time.sleep(metrics.procfs_sampling_interval * 15)


    #log.info("Metrics : Clean up")
    #metrics.clean_up()

    #log.info("Metrics : All done")


if __name__ == "__main__":
    typer.run(main)
