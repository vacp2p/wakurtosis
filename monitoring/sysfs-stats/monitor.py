import logging as log

import os, sys, threading, subprocess, signal

from collections import defaultdict

from procfs import Proc
import sched, time
import typer

CGROUP="/sys/fs/cgroup/"
OPREFIX="docker"
OEXT="out"

# TODO: return only relevant bits for CPU
def get_cpu_metrics(f):
    f.seek(0)
    return f.read()


def get_mem_metrics(f, lst):
    f.seek(0)
    rbuff = f.readlines()
    res = ''.join([rbuff[i].replace("\t", " ").replace("\n", ", ").replace(":", " ") for i in lst])
    return res


def get_net_metrics(f, lst):
    f.seek(0)
    rbuff = f.readlines()
    res =  ''.join([line.replace("\t", " ").replace("\n", " ") for line in rbuff if "eth" in line])
    return res


def get_blk_metrics(f, lst):
    f.seek(0)
    rbuff = f.readlines()
    res = ''.join([rbuff[i].replace("\n", ", ") for i in lst])
    return res


def signal_handler(sig, frame):
    sys.exit(0)


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

        self.ps_docker = 'ps -ef | grep -E "wakunode|waku" |grep -v docker | grep -v grep | awk \"{print $2}\"'
        self.ps_pids_fname = "ps-pid-list"
        self.ps_pids = []

        self.procfs_fname = ""
        self.procfs_fd = ""
        self.procfs_scheduler = sched.scheduler(time.time, time.sleep)
        self.procfs_sample_cnt = 0

        # self.container_id = -1 self.container_name = -1 self.cpu_usage = -1 
        # self.mem_usage_abs = -1 self.mem_usage_perc = -1 self.net_sends = -1
        # self.net_recvs = -1 self.block_reads = -1 self.block_writes = -1

    def build_and_exec(self, cmd, fname):
        cmdline = f"exec {cmd} > {OPREFIX}-{fname}.{OEXT}"
        subprocess.run(cmdline, shell=True)

    def launch_docker_monitor(self, dstats_fname):
        cmd = f"exec {self.docker_stats} > {OPREFIX}-{dstats_fname}.{OEXT}"
        log.info("docker monitor cmd : " +  cmd)
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, preexec_fn=os.setsid)
        self.docker_stats_pid, self.docker_stats_fname = process.pid, dstats_fname
        log.info(f"docker monitor started : {self.docker_stats_pid}, {self.docker_stats_fname}")

    def pid2docker(self, pid):
        return self.docker_name2id[self.docker_pid2name[pid]]

    def populate_file_handles_1(self):
        # pid to file handles
        self.pid2procfds[0]["cpu"] =  open(f"/proc/stat")
        for pid in self.docker_pids:
            self.pid2procfds[pid]["cpu"] =  open(f"/proc/{pid}/stat")
            self.pid2procfds[pid]["mem"] =  open(f"/proc/{pid}/status") #grep ^VmPeak VmRSS /proc/*/status 
            self.pid2procfds[pid]["net"] =  open(f"/proc/{pid}/net/dev")
            self.pid2procfds[pid]["blk"] =  open((f"/sys/fs/cgroup/blkio/docker/"
                                                  f"{self.pid2docker(pid)}/"
                                                  f"blkio.throttle.io_service_bytes"
                                                ))
            #self.pid2procfds[pid]["blk"] =  open(f"/proc/{pid}/io") # per-procses, but needs SUDO
        self.procfs_fd = open(f"{OPREFIX}-{self.procfs_fname}.{OEXT}", "w")
            #pid2procfds[pid]["net"] =  open(f"/proc/{pid}/")

    def populate_file_handles_n(self):
        proc = Proc()
        wakus = proc.processes.cmdline('(nim-waku|waku)')
        log.info("wakus pids: " + str(wakus))
        self.pid2procfds[0]["cpu"] =  open(f"/proc/stat")
        for pid in self.ps_pids:
            self.pid2procfds[pid]["cpu"] =  open(f"/proc/{pid}/stat")
            self.pid2procfds[pid]["mem"] =  open(f"/proc/{pid}/status") #grep ^VmPeak VmRSS /proc/*/status 
            self.pid2procfds[pid]["net"] =  open(f"/proc/{pid}/net/dev")
            self.pid2procfds[pid]["blk"] =  open((f"/sys/fs/cgroup/blkio/docker"
                                                  f"/{self.pid2docker(pid)}/"
                                                  f"blkio.throttle.io_service_bytes"
                                                 ))
            #self.pid2procfds[pid]["blk"] =  open(f"/proc/{pid}/io") # per-procses, but needs SUDO
        self.procfs_fd = open(f"{OPREFIX}-{self.procfs_fname}.{OEXT}", "w")
            #pid2procfds[pid]["net"] =  open(f"/proc/{pid}/")

    def populate_file_handles(self):
        if self.csize == 1:
            self.populate_file_handles_1()
        else:
            self.populate_file_handles_n()

    def teardown_file_handles_1(self):
        self.pid2procfds[0]["cpu"].close()
        for pid in self.docker_pids:
            self.pid2procfds[pid]["cpu"].close()
            self.pid2procfds[pid]["mem"].close()
            self.pid2procfds[pid]["net"].close()
            self.pid2procfds[pid]["blk"].close()
        self.procfs_fd.close()

    def teardown_file_handles_n(self):
        self.pid2procfds[0]["cpu"].close()
        for pid in self.docker_pids:
            self.pid2procfds[pid]["cpu"].close()
            self.pid2procfds[pid]["mem"].close()
            self.pid2procfds[pid]["net"].close()
            self.pid2procfds[pid]["blk"].close()
        self.procfs_fd.close()

    def teardown_file_handles(self):
        if self.csize == 1:
            self.teardown_file_handles_1()
        else:
            self.teardown_file_handles_2()

    def procfs_reader(self):
        log.info("collecting " + str(self.procfs_sample_cnt))
        stat = " ".join(get_cpu_metrics(self.pid2procfds[0]["cpu"]).splitlines())
        for pid in self.docker_pids:
            docker_id = self.pid2docker(pid)
            cpu = get_cpu_metrics(self.pid2procfds[pid]["cpu"]).strip() + " , "
            mem = get_mem_metrics(self.pid2procfds[pid]["mem"], [16, 17, 21]) #VmPeak, VmSize, VmRSS
            net = get_net_metrics(self.pid2procfds[pid]["net"], [0, 1]) # Read, Write
            blk = get_blk_metrics(self.pid2procfds[pid]["blk"], [0, 1]) # Read, Write
            #blk = get_blk_metrics(self.pid2procfds[pid]["blk"], [4, 5]) # Read, Write
            out = ( f"SAMPLE_{self.procfs_sample_cnt} "
                    f"{docker_id} {time.time()} {mem} "
                    f"{net} {blk} {cpu} {''.join(stat)}\n"
                  )
            #out = f"SAMPLE_{cnt} {time.time()} {mem}# {net}# {blk} {''.join(stat)}\n"
            #print(str(out))
            self.procfs_fd.write(str(out))
        self.procfs_sample_cnt += 1
        self.procfs_scheduler.enter(self.procfs_sampling_interval, 1,
                     self.procfs_reader, ())

    def launch_procfs_monitor(self, procfs_fname):
        self.procfs_fname = procfs_fname
        self.populate_file_handles()
        log.info("files handles populated")
        self.procfs_scheduler.enter(self.procfs_sampling_interval, 1,
                     self.procfs_reader, ())
        self.procfs_scheduler.run()


    def build_the_basics(self, dps_fname, dinspect_fname, cpuinfo_fname, meminfo_fname):
        self.build_and_exec(self.docker_ps, dps_fname)
        self.build_and_exec(self.docker_inspect, dinspect_fname)
        self.build_and_exec("cat /proc/cpuinfo", cpuinfo_fname)
        self.build_and_exec("cat /proc/meminfo", meminfo_fname)

        self.docker_ps_fname, self.docker_inspect_fname = f"{OPREFIX}-{dps_fname}.{OEXT}", f"{OPREFIX}-{dinspect_fname}.{OEXT}"

    def build_docker_pids_1(self):
        with open(self.docker_ps_fname, "r") as f:
            for line in f:
                la = line.split("#")
                self.docker_name2id[la[1]] = la[0]
                self.docker_ids.append(la[0])
        with open(self.docker_inspect_fname, "r") as f:
            for line in f:
                la = line.split("/")
                self.docker_pid2name[la[0]] = la[1]
                self.docker_pids.append(la[0])
        log.info(f"docker: ids, pids : {str(self.docker_ids)}, {str(self.docker_pids)}")
        log.info(f"docker: maps : {self.docker_pid2name}, {self.docker_name2id}")

    def build_docker_pids_n(self):
        # multinode containers 
        # ps -ef | grep -E 'wakunode|waku' |grep -v docker | grep -v grep | awk '{print $2}'
        self.build_and_exe(cmd, self.ps_pids_fname)
        self.ps_pids_fname = f"{OPREFIX}-{self.ps_pids_fname}.{OEXT}"
        with open(self.ps_pids_fname, "r") as f:
            self.ps_pids = f.readline()
        log.info(f"docker: pids : {str(self.pids)}")

    def build_metadata(self, dps_fname, dinspect_fname, cpuinfo_fname, meminfo_fname, csize=1):
        self.build_the_basics(dps_fname, dinspect_fname, cpuinfo_fname, meminfo_fname)
        if self.csize == 1:
            self.build_docker_pids_1()
        else:
            self.build_docker_pids_n()

    def spin_up(self, dstats_fname, procfs_fname):
        log.info("Starting the docker monitor...")
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
        log.info(f"docker monitor stopped : {self.docker_stats_pid}, {self.docker_stats_fname}")

def main(ctx: typer.Context):
    format = "%(asctime)s: %(message)s"
    log.basicConfig(format=format, level=log.INFO,
                        datefmt="%H:%M:%S")
    signal.signal(signal.SIGINT, signal_handler)

    log.info("Metrics : starting")
    metrics = MetricsCollector(csize=1, sampling_interval=1)

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
