import os
import sys
import pathlib
import resource
import threading
import subprocess
import signal
import sched
import time
import typer

import logging as log
from pathlib import Path
#from procfs import Proc
from collections import defaultdict

# define singleton 
class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class Parser(metaclass=Singleton):
    def __init__(self, csize):
        self.csize = csize

    # pulls system-wide jiffies
    def system_cpu(self, f):
        f.seek(0)
        line = f.readline()
        return sum(int(s) for s in line.split()[2:])

    # pulls per-process user/system jiffies
    def process_cpu(self, f):
        f.seek(0)
        rbuff = f.readline().split()
        ptot = int(rbuff[13]) + int(rbuff[14])
        return ptot

    # pulls VmPeak, VmSize, VmRSS stats per wakunode
    def mem_metrics(self, f):
        f.seek(0)
        rbuff = f.readlines()
        lst = [16, 17, 21, 25, 26] #VmPeak, VmSize, VmRSS, VmData, VmStack
        out = [' '.join(rbuff[i].replace("\n", " ").replace(":", "").split()) for i in lst]
        res = ' '.join(out)
        return res

    # pulls Rx/Tx Bytes and Packers per wakunode
    def net1_metrics(self, f, host_if):
        f.seek(0)
        rbuff = f.readlines()
        out = [line.strip().split() for line in rbuff if "eth0" in line]        # docker
        if out == []:
            out = [line.strip().split() for line in rbuff if host_if in line]     # host
        out = out[0]
        res = f'{out[0]} RxBytes {out[1]} RxPackets {out[2]} TxBytes {out[9]} TxPackets {out[10]}'
        return res

    # TODO: reconcile with net1 and net3
    # pulls Rx/Tx Bytes per wakunode
    def net2_metrics(self, f, veth="eth0"):
        f.seek(0)
        rbuff = f.readlines()
        ra = rbuff[3].split()
        res = f'InOctets {ra[7]} OutOctets {ra[8]}'
        return f'{veth} {res}'

    # pulls Rx/Tx Bytes per wakunode
    def net3_metrics(self, frx, ftx, veth="eth0"):
        frx.seek(0)
        ftx.seek(0)
        return f'{veth} NETRX {frx.read().strip()} NETWX {ftx.read().strip()}'

    # pulls the disk read/write bytes per wakunodes
    # TODO: demonise block reads if cszie > 1: UNIX sockets/IPC/MSG QUEUES
    def blk_metrics(self, f):
        f.seek(0)
        rbuff = f.readlines()
        lst = [4, 5]
        #lst = [0, 1] if self.csize == 1 else [4, 5]
        res = ''.join([rbuff[i].replace("\n", " ").replace("259:0 ", "") for i in lst])
        return res


class MetricsCollector:
    def __init__(self, csize, prefix, sampling_interval):
        self.csize = csize
        self.prefix = prefix
        self.procfs_sampling_interval = sampling_interval
        self.pid2procfds = defaultdict(dict)
        self.parser = Parser(csize)


        self.docker_ps_fname =  os.environ["DPS_FNAME"]
        self.docker_inspect_fname =  os.environ["DINSPECT_FNAME"]
        self.ps_pids_fname = os.environ["PIDLIST_FNAME"]
        self.docker_pid2veth_fname = os.environ["ID2VETH_FNAME"]

        self.docker_pids = []
        self.docker_npids = len(self.docker_pids)
        self.ps_pids = []

        self.did2veth = {}
        self.pid2veth = {}
        self.pid2did = {}
        self.pid2node_name = {}
        self.pid2kdid = {}

        self.procout_fname = os.environ["PROCOUT_FNAME"]
        self.procfs_fd = ""
        self.procfs_scheduler = sched.scheduler(time.time, time.sleep)
        self.procfs_sample_cnt = 0
        self.got_signal = False

        self.host_if = os.environ["LOCAL_IF"]
        self.signal_fifo = os.environ["SIGNAL_FIFO"]

        self.last_tstamp = 0
        self.start_time = 0

        self.last_sys_ctot, self.last_pid_ctot = {}, {}

    # check if a wakunode/pid exists
    def pid_exists(self, pid):
        pid = int(pid)
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        else:
            return True

    # open the /proc files ahead to save up parsing, lookup, fd alloc etc.
    def populate_file_handles(self):
        # up the ulimit -n = number of waku nodes * 10 filehandles
        t1 = time.time()
        resource.setrlimit(resource.RLIMIT_NOFILE, (self.docker_npids*10, self.docker_npids*10))
        self.pid2procfds[0]["cpu"] =  open(f'/proc/stat')
        for pid in self.docker_pids:
            self.pid2procfds[pid]["cpu"] =  open(f'/proc/{pid}/stat')
            self.pid2procfds[pid]["mem"] =  open(f'/proc/{pid}/status')
            self.pid2procfds[pid]["net1"] =  open(f'/proc/{pid}/net/dev')
            self.pid2procfds[pid]["net2"] =  open(f'/proc/{pid}/net/netstat')
            self.pid2procfds[pid]["net3rx"] =  open(f'/sys/class/net/{self.pid2veth[pid]}/statistics/rx_bytes')
            self.pid2procfds[pid]["net3tx"] =  open(f'/sys/class/net/{self.pid2veth[pid]}/statistics/tx_bytes')
            #self.pid2procfds[pid]["blk"]  = open((f'/sys/fs/cgroup/blkio/docker'
            #                                      f'/{self.pid2did[pid]}/'
            #                                      f'blkio.throttle.io_service_bytes'
            #                                 )) if self.csize == 1 else open(f'/proc/{pid}/io')
            self.pid2procfds[pid]["blk"] =  open(f'/proc/{pid}/io') # require SUDO
        self.procfs_fd = open(self.procout_fname, "a")
        t2 = time.time()
        log.info((f'Metrics: populate_file_handles took {t2-t1:.5f} secs '
                  f'for 7 * {self.docker_npids} = {7*self.docker_npids} file handles'))

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

    # the /proc reader : the fast path
    def procfs_collector(self):
        for pid in self.docker_pids:
            veth = self.pid2veth[pid]
            sys_ctot = self.parser.system_cpu(self.pid2procfds[0]["cpu"])
            pid_ctot = self.parser.process_cpu(self.pid2procfds[pid]["cpu"])
            cpu_perc = (pid_ctot - self.last_pid_ctot[pid]) / (sys_ctot - self.last_sys_ctot[pid])
            self.last_sys_ctot[pid], self.last_pid_ctot[pid] = sys_ctot, pid_ctot
            mem = self.parser.mem_metrics(self.pid2procfds[pid]["mem"])
            net1 = self.parser.net1_metrics(self.pid2procfds[pid]["net1"], self.host_if)
            #net2 = self.parser.net2_metrics(self.pid2procfds[pid]["net2"], veth) # SNMP MIB
            #net3 = self.parser.net3_metrics(self.pid2procfds[pid]["net3rx"],
            #        self.pid2procfds[pid]["net3tx"], veth) # sysfs/cgroup stats
            blk = self.parser.blk_metrics(self.pid2procfds[pid]["blk"]) # Read, Write
            out = ( f'SAMPLE_{self.procfs_sample_cnt} '
                    f'{pid} {self.pid2node_name[pid]} {time.time()} '
                    f'{self.pid2did[pid]} {self.pid2kdid[pid]} '
                    f'MEM {mem} NET {net1} '
                    f'BLK {blk} CPU {cpu_perc}\n'
                  )
            self.procfs_fd.write(str(out))
        self.procfs_sample_cnt += 1     # schedule the next event ASAP
        if not self.got_signal: # could be xpensive for n > 1000 : branch
            self.procfs_scheduler.enter(self.procfs_sampling_interval, 1, self.procfs_collector, ())
        if  (self.procfs_sample_cnt-1) % 50 == 0: # could be xpensive for n > 1000 : branch + mod
            tstamp = time.time()
            n = self.docker_npids
            elapsed = tstamp - self.last_tstamp
            log.info((f'Metrics: sample cnt = {self.procfs_sample_cnt}: '
                f'avg time took to sample {n}\t wakunodes ~ '
                f'{elapsed/50-self.procfs_sampling_interval:.5f} secs'))
            self.last_tstamp = tstamp

    # keep track of cpu stats from last run
    def set_last_cpu_totals(self):
        log.info("Metrics: set last_cpu_totals")
        for pid in self.docker_pids:
            self.last_sys_ctot[pid] = self.parser.system_cpu(self.pid2procfds[0]["cpu"])
            self.last_pid_ctot[pid] = self.parser.process_cpu(self.pid2procfds[pid]["cpu"])

    # add headers and schedule /proc reader's first read
    def launch_procfs_monitor(self, wls_cid):
        t1 = time.time()
        self.populate_file_handles()    # including procout_fname
        self.procfs_fd.write((f'# procfs_sampling interval = {self.procfs_sampling_interval} : '
                              f'{len(self.docker_pids)}\n'))
        self.procfs_fd.write(f'# {", ".join([f"{pid} = {self.pid2did[pid]}" for pid in self.pid2did])} : {len(self.pid2did.keys())}\n')
        self.procfs_fd.write(f'# {", ".join([f"{pid} = {self.pid2veth[pid]}" for pid in self.pid2did])} : {len(self.pid2veth.keys())}\n')
        self.procfs_fd.write(f'# {", ".join([f"{pid} = {self.pid2node_name[pid]}" for pid in self.pid2did])} : {len(self.pid2node_name.keys())}\n')
        # write the df column names
        self.procfs_fd.write((f'EpochId PID NodeName TimeStamp ContainerID ContainerName '
                f'MEM VmPeakKey VmPeak VmPeakUnit '
                f'VmSizeKey VmSize VmSizeUnit '
                f'VmRSSKey VmRSS VmRSSUnit '
                f'VmDataKey VmData VmDataUnit '
                f'VmStkKey VmStk VmStkUnit '
                f'NET HostVIF RxBytesKey NetSent RxPacketsKey NetSentPkts '
                f'TxBytesKey NetRecv TxPacketsKey NetRecvPkts '
                #f'VETH InOctetsKey InOctets OutOctetsKey OutOctets '
                #f'DockerVIF NetRXKey NetRX NETWXKey NetWX '
                f'BLK READKEY BlockR WRITEKEY BlockW '
                #f'CPU-SYS cpu cpu0 cpu1 cpu2 cpu3 cpu4 cpu5 cpu6 cpu7 cpu8 cpu9 '
                #f'CPU-Process CPUUTIME CPUSTIME 
                f'CPU CPUPerc\n'))
        log.info("Metrics: launch_procfs_monitor: signalling WLS")
        signal_wls = f'docker exec {wls_cid} touch /wls/start.signal'
        subprocess.run(signal_wls, shell=True) # revisit after Jordi's pending branch merge
        self.set_last_cpu_totals()
        self.start_time = time.time()
        self.last_tstamp = time.time()
        self.procfs_scheduler.enter(self.procfs_sampling_interval, 1,
                     self.procfs_collector, ())
        self.procfs_scheduler.run()

    # build the pid to kurtosis did map from docker ps
    def build_pid2kdid(self):
        did2kdid = {}
        with open(self.docker_ps_fname) as f:
            line = f.readline()
            while line:
                larr = line.split('#')
                did2kdid[larr[0]] = larr[1]
                line = f.readline()
        for pid in self.pid2did:
            self.pid2kdid[pid] = did2kdid[self.pid2did[pid]]

    # build the host pid to docker id map : will include non-docker wakunodes
    def build_pid2did(self):
        with open(self.ps_pids_fname) as f:
            self.ps_pids = f.read().strip().split("\n")

        for pid in self.ps_pids:
            if not self.pid_exists(pid):  # assert that these pids are live
                continue
            with open(f'/proc/{pid}/cmdline') as f:
                line = f.readline()
                # assert that these pids are waku's and have config enabled
                if "waku" not  in line or "--config-file=" not in line:
                    log.info(f'non-waku pid {pid} = {line}')
                    continue
                self.pid2node_name[pid] = line.split("--config-file=")[1].split('/')[3]
            did = ""
            self.docker_pids.append(pid)
            # FORMAT
            #'/proc/{pid}/cmdline  = /usr/bin/wakunode--rpc-address=0.0.0.0
                                    #--metrics-server-address=0.0.0.0
                                    #--log-level=TRACE
                                    #--config-file=/node/configuration_file/node-6/node-6.toml
                                    #--ports-shift=2m
            with open(f'/proc/{pid}/mountinfo') as f: # or /proc/{pid}/cgroup
                line = f.readline()
                while line:
                    if '/docker/containers/' in line:
                        did = line.split('/docker/containers/')[1]
                        did = did.split('/')[0]
                        break
                    line = f.readline()
            if did == "":
                did = f'nondockerwakuPID{pid}'
                self.pid2did[pid] = did
                self.did2veth[did] = self.host_if
                self.pid2veth[pid] = self.host_if
                continue
            self.pid2did[pid] = did
        self.docker_npids = len(self.docker_pids)

    # build the host pid to host side veth pair map
    def build_pid2veth(self):
        with open(self.docker_pid2veth_fname) as f:
            for line in f.readlines():
                la = line.strip().split(":")
                self.did2veth[la[0]]=la[1].strip().split(' ')[-1]
        self.pid2veth = {pid : self.did2veth[self.pid2did[pid]] for pid in self.docker_pids}

    # build metadata for the runs: pid2did, did2veth, pid2veth
    def process_metadata(self):
        t1 = time.time()
        self.build_pid2did()
        self.build_pid2kdid()
        t2 = time.time()
        self.build_pid2veth()
        t3 = time.time()
        log.info(f'Metrics: process_metadata: pid2did/kdid = {t2-t1:.5f} secs, pid2veth = {t3-t2:0.5f} secs')
        log.info(f'Metrics: process_metadata took {t3-t1:.5f} secs')

    # after metadata is collected, create the threads and launch data collection
    def spin_up(self, wls_cid):
        log.info("Metrics: spin_up: starting the procfs monitor...")
        self.launch_procfs_monitor(wls_cid)

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
        stop_time = time.time()
        dur = stop_time - self.start_time
        log.info((f'Metrics: ran for {dur} secs, got {signal.Signals(sig).name} '
                  f'@ sample cnt {self.procfs_sample_cnt}, cleaning up...'))
        self.got_signal = True
        time.sleep(self.procfs_sampling_interval)
        self.clean_up()
        sys.exit(0)


# ensure sampling_interval > 0
def _sinterval_callback(ctx: typer, Context, sinterval: int):
    if sinterval <= 0:
        raise ValueError(f"sampling-interval must be > 0")
    return sinterval

# ensure container_size > 0
def _csize_callback(ctx: typer, Context, csize: int):
    if csize <= 0:
        raise ValueError(f"container-size must be > 0")
    return csize

# does not return
def main(ctx: typer.Context,
        wls_cid: str = typer.Option("",
            help="Specify the WLS container id signal"),
        prefix: str = typer.Option("",
            help="Specify the path for find the data files"),
        local_if: str = typer.Option("eth0",
            help="Specify the local interface to account non-docker nw stats"),
        container_size: int = typer.Option(1, callback=_csize_callback,
            help="Specify the number of wakunodes per container"),
        sampling_interval: int = typer.Option(1, callback=_sinterval_callback,
            help="Set the sampling interval in secs")):

    format = "%(asctime)s: %(message)s"
    log.basicConfig(format=format, level=log.INFO,
                        datefmt="%H:%M:%S")

    log.info("Metrics: setting up")
    metrics = MetricsCollector(csize=container_size,
                        prefix=prefix,
                        sampling_interval=sampling_interval)

    log.info("Metrics: processing system and container metadata...")
    metrics.process_metadata()

    num_wakus = len(metrics.docker_pids)
    log.info(f'Metrics: total waku nodes present: {num_wakus}')
    log.debug(f'Metrics: waku pids: {num_wakus}: {metrics.docker_pids}')

    log.info("Metrics: registering signal handlers...")
    metrics.register_signal_handlers()

    log.info("Metrics: starting the data collection")
    metrics.spin_up(wls_cid)


if __name__ == "__main__":
    typer.run(main)
