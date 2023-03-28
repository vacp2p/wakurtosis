import logging as log

import os, sys, threading, subprocess, signal

from collections import defaultdict

from procfs import Proc
import sched, time
import typer

CGROUP="/sys/fs/cgroup/"
OPREFIX="docker"
OEXT="out"

# TODO: return only relevant bits to compute the percentages for CPU
def get_cpu_metrics(f):
    f.seek(0)
    return f'CPU {f.read()}'


def get_mem_metrics(f):
    f.seek(0)
    rbuff = f.readlines()
    lst = [16, 17, 21] #VmPeak, VmSize, VmRSS
    res = ''.join([rbuff[i].replace("\t", " ").replace("\n", " ").replace(":", " ") for i in lst])
    return f'MEM {res}'


# TODO: return only Send/Recv
def get_net_metrics(f):
    f.seek(0)
    rbuff = f.readlines()
    res =  ''.join([line.replace("\t", " ").replace("\n", " ") for line in rbuff if "eth" in line])
    return f'NET {res}'


def get_blk_metrics(f, csize):
    f.seek(0)
    rbuff = f.readlines()
    lst = [0, 1] if csize == 1 else [4, 5]
    try: #sysfs is dodgy at times
        res = ''.join([rbuff[i].replace("\n", " ") for i in lst])
    except:
        res = "BLK Read 0  Write 0 "
    return res


class MetricsCollector:
    def __init__(self, csize=1, sampling_interval=1):
        self.csize = csize
        self.procfs_sampling_interval = sampling_interval
        self.pid2procfds = defaultdict(dict)

        self.docker_stats = 'docker stats --no-trunc --format  "{{.Container}} / {{.Name}} / {{.ID}} / {{.CPUPerc}} / {{.MemUsage}} / {{.MemPerc}} / {{.NetIO}} / {{.BlockIO}} / {{.PIDs}}" '
        self.docker_stats_pid = 0
        self.docker_stats_fname = 0

        self.docker_ps = 'docker ps --no-trunc --filter "ancestor=statusteam/nim-waku"  --filter "ancestor=gowaku" --format "{{.ID}}#{{.Names}}#{{.Image}}#{{.Command}}#{{.State}}#{{.Status}}#{{.Ports}}" '
        self.docker_ps_fname = ""
        self.docker_ids = []
        self.docker_name2id = {}

        self.docker_inspect = 'docker ps -q | xargs docker inspect --format "{{.State.Pid}}{{.Name}}/{{.Image}}/{{.State}}" '
        self.docker_inspect_fname = ""
        self.docker_pids = []
        self.docker_pid2name = {}

        self.docker_pid2id = {}

        self.ps_docker = 'ps -ef | grep -E "wakunode|waku" |grep -v docker | grep -v grep | awk \'{print $2}\''
        self.ps_pids_fname = "list-pids"
        self.ps_pids = []

        self.procfs_fname = ""
        self.procfs_fd = ""
        self.procfs_scheduler = sched.scheduler(time.time, time.sleep)
        self.procfs_sample_cnt = 0

        # self.container_id = -1 self.container_name = -1 self.cpu_usage = -1 
        # self.mem_usage_abs = -1 self.mem_usage_perc = -1 self.net_sends = -1
        # self.net_recvs = -1 self.block_reads = -1 self.block_writes = -1

    def build_and_exec(self, cmd, fname):
        cmdline = f'exec {cmd} > {OPREFIX}-{fname}.{OEXT}'
        subprocess.run(cmdline, shell=True)

    def launch_docker_monitor(self, dstats_fname):
        cmd = f'exec {self.docker_stats} > {OPREFIX}-{dstats_fname}.{OEXT}'
        log.info("docker monitor cmd : " +  cmd)
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, preexec_fn=os.setsid)
        self.docker_stats_pid, self.docker_stats_fname = process.pid, dstats_fname
        log.info(f'docker monitor started : {self.docker_stats_pid}, {self.docker_stats_fname}')

    def populate_file_handles(self):
        assert self.docker_pid2name != {} and self.docker_name2id != {} and self.docker_pid2id != {}
        self.pid2procfds[0]["cpu"] =  open(f'/proc/stat')
        for pid in self.docker_pids:
            self.pid2procfds[pid]["cpu"] =  open(f'/proc/{pid}/stat')
            self.pid2procfds[pid]["mem"] =  open(f'/proc/{pid}/status')
            self.pid2procfds[pid]["net"] =  open(f'/proc/{pid}/net/dev')
            #if self.csize == 1:
             #   self.pid2procfds[pid]["blk"] =  open((f'/sys/fs/cgroup/blkio/docker'
             #                                         f'/{self.docker_pid2id[pid]}/'
             #                                         f'blkio.throttle.io_service_bytes'
             #                                       ))
            #else:
             #   self.pid2procfds[pid]["blk"] =  open(f'/proc/{pid}/io') # need SUDO
        self.procfs_fd = open(f'{OPREFIX}-{self.procfs_fname}.{OEXT}', "w")

    def teardown_file_handles(self):
        self.pid2procfds[0]["cpu"].close()
        for pid in self.docker_pids:
            self.pid2procfds[pid]["cpu"].close()
            self.pid2procfds[pid]["mem"].close()
            self.pid2procfds[pid]["net"].close()
            #self.pid2procfds[pid]["blk"].close()
        self.procfs_fd.close()

    def procfs_reader(self):
        cpu_stat = " ".join(get_cpu_metrics(self.pid2procfds[0]["cpu"]).splitlines())
        for pid in self.docker_pids:
            cpu = get_cpu_metrics(self.pid2procfds[pid]["cpu"]).strip() # all cpu stats
            mem = get_mem_metrics(self.pid2procfds[pid]["mem"])
            net = get_net_metrics(self.pid2procfds[pid]["net"]) # Whole eth* row
          #  if self.csize == 1:
          #      blk = get_blk_metrics(self.pid2procfds[pid]["blk"], self.csize) # Read, Write
          #  else:
          #      blk = get_blk_metrics(self.pid2procfds[pid]["blk"], self.csize) # Read, Write, SUDO
            blk = "Read 0, Write 0"
            out = ( f'SAMPLE_{self.procfs_sample_cnt} '
                    f'{pid} {time.time()} '         # file has pid to docker_id map
                    f'{mem} {net} {blk} {cpu} {"".join(cpu_stat)}\n'
                  )
            #log.debug(str(pid)+str(out))
            self.procfs_fd.write(str(out))
        log.info("collected " + str(self.procfs_sample_cnt))
        self.procfs_sample_cnt += 1
        self.procfs_scheduler.enter(self.procfs_sampling_interval, 1, self.procfs_reader, ())

    def launch_procfs_monitor(self, procfs_fname):
        self.procfs_fname = procfs_fname
        self.populate_file_handles()    # including procfs_fd
        self.procfs_fd.write((f'#container_size = {self.csize} '
                              f'procfs_sampling interval = {self.procfs_sampling_interval}\n'
                              ))
        self.procfs_fd.write(f'# {", ".join([f"{pid} = {self.docker_pid2id[pid]}" for pid in self.docker_pid2id])}\n')
        log.info("files handles populated")
        self.procfs_scheduler.enter(self.procfs_sampling_interval, 1,
                     self.procfs_reader, ())
        self.procfs_scheduler.run()

    def record_the_basics(self, dps_fname, dinspect_fname, cpuinfo_fname, meminfo_fname):
        self.build_and_exec(self.docker_ps, dps_fname)
        self.build_and_exec(self.docker_inspect, dinspect_fname)
        self.build_and_exec("cat /proc/cpuinfo", cpuinfo_fname)
        self.build_and_exec("cat /proc/meminfo", meminfo_fname)
        self.docker_ps_fname, self.docker_inspect_fname = f'{OPREFIX}-{dps_fname}.{OEXT}', f'{OPREFIX}-{dinspect_fname}.{OEXT}'
        with open(self.docker_ps_fname, "r") as f:
            for line in f:
                l = line.split("#")
                self.docker_name2id[l[1]] = l[0]
                self.docker_ids.append(l[0])

    def build_pid2id(self):
        self.docker_pid2id = {pid :
                self.docker_name2id[self.docker_pid2name[pid]] for pid in self.docker_pids}

    def build_pid2name_1(self):
        with open(self.docker_inspect_fname, "r") as f:
            for line in f:
                la = line.split("/")
                self.docker_pid2name[la[0]] = la[1]
                self.docker_pids.append(la[0])
        log.info(f'docker: ids, pids : {str(self.docker_ids)}, {str(self.docker_pids)}')
        log.info(f'docker: maps : {self.docker_pid2name}, {self.docker_name2id}')

    def build_pid2name_n(self):
        log.info(self.ps_docker)
        self.build_and_exec(self.ps_docker, self.ps_pids_fname)
        self.ps_pids_fname = f'{OPREFIX}-{self.ps_pids_fname}.{OEXT}'
        with open(self.ps_pids_fname, "r") as f:
            self.ps_pids = f.read().strip().split("\n")
        log.info(f'docker: pids : {str(self.ps_pids)}')
        self.docker_pids = self.ps_pids
        for pid in self.docker_pids:
            get_shim_pid=((f'pstree -sg {pid} | '
                           f'head -n 1 | '
                           f'grep -Po "shim\([0-9]+\)---[a-z]+\(\K[^)]*"'
                         ))
            self.build_and_exec(get_shim_pid, f'shim-{pid}')
            with open(f'{OPREFIX}-shim-{pid}.{OEXT}', "r") as f:
                shim_pid = f.read().strip()
                os.remove(f'{OPREFIX}-shim-{pid}.{OEXT}')
                if shim_pid == "":
                    dname = f'thundering_typhoons{pid}'
                    did = f'nondockerwakuPID{pid}'
                    self.docker_pid2name[pid] = dname
                    self.docker_name2id[dname] = did
                    self.docker_pid2id[pid] = did
                    continue
                get_docker_name = ((f'docker inspect --format '
                                    '"{{.State.Pid}}, {{.Name}}"'
                                    f' $(docker ps -q) | grep {shim_pid}'
                                  ))
                self.build_and_exec(get_docker_name, f'name-{pid}')
                with open(f'{OPREFIX}-name-{pid}.{OEXT}', "r") as f:
                    tmp = f.read().strip().replace(" /", "")
                    pid, docker_name = tmp.split(',')
                    self.docker_pid2name[pid] = docker_name
                    os.remove(f'{OPREFIX}-name-{pid}.{OEXT}')

    def build_metadata(self, dps_fname, dinspect_fname, cpuinfo_fname, meminfo_fname, csize=1):
        self.record_the_basics(dps_fname, dinspect_fname, cpuinfo_fname, meminfo_fname)
        if self.csize == 1:
            self.build_pid2name_1()
        else:
            self.build_pid2name_n()
        self.build_pid2id()

    def register_signals(self):
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGQUIT, self.signal_handler)

    def spin_up(self, dstats_fname, procfs_fname):
        log.info("Starting the docker monitor...")
        self.register_signals()
        self.docker_thread = threading.Thread(
                target=self.launch_docker_monitor, args=(dstats_fname,), daemon=True)
        self.docker_thread.start()
        log.info("Starting the procfs builder...")
        self.procfs_thread = threading.Thread(
                target=self.launch_procfs_monitor, args=(procfs_fname,), daemon=True)
        self.procfs_thread.start()

    def clean_up(self):
        self.teardown_file_handles()
        os.kill(self.docker_stats_pid, signal.SIGTERM)
        log.info(f'docker monitor stopped : {self.docker_stats_pid}, {self.docker_stats_fname}')

    def signal_handler(self, sig, frame):
        self.clean_up()
        sys.exit(0)


def main(ctx: typer.Context,
        container_size: int = typer.Option(1,
        help="Specify the number of wakunodes per container"),
        sampling_interval: int = typer.Option(1, help="Set the sampling interval in secs")
        ):
    format = "%(asctime)s: %(message)s"
    log.basicConfig(format=format, level=log.INFO,
                        datefmt="%H:%M:%S")

    log.info("Metrics : starting")
    metrics = MetricsCollector(csize=container_size, sampling_interval=sampling_interval)

    log.info("Collecting system and container metadata...")
    metrics.build_metadata("ps", "inspect", "cpuinfo", "meminfo")

    log.info("Starting the Measurement Threads")
    metrics.spin_up("stats", "procfs")

    # get sim time info from config.json? or  ioctl/select from WLS? or docker wait?
    time.sleep(metrics.procfs_sampling_interval * 5)

    # x.join()

    metrics.clean_up()
    log.info("Metrics : all done")


if __name__ == "__main__":
    typer.run(main)
