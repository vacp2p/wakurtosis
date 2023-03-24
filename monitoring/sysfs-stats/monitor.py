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


def get_blk_metrics(f, lst):
    f.seek(0)
    rbuff = f.readlines()
    res = ''.join([rbuff[i].replace("\n", ", ") for i in lst])
    return res


def signal_handler(sig, frame):
    sys.exit(0)


class MetricsCollector:
    def __init__(self):
        self.docker_ps = 'docker ps --no-trunc --filter "ancestor=statusteam/nim-waku"  --filter "ancestor=gowaku" --format "{{.ID}}#{{.Names}}#{{.Image}}#{{.Command}}#{{.State}}#{{.Status}}#{{.Ports}}" '
        self.ps_fname = ""
        self.dockers = []
        self.docker_name2id = {}

        self.docker_inspect = 'docker ps -q | xargs docker inspect --format "{{.State.Pid}}{{.Name}}/{{.Image}}/{{.State}}" '
        self.inspect_fname = ""
        self.docker_pids = []
        self.docker_pid2name = {}

        self.docker_stats = 'docker stats --no-trunc --format  "{{.Container}} / {{.Name}} / {{.ID}} / {{.CPUPerc}} / {{.MemUsage}} / {{.MemPerc}} / {{.NetIO}} / {{.BlockIO}} / {{.PIDs}}" '
        self.docker_stats_pid = 0
        self.docker_stats_fname = 0

        self.procfs_fname = ""
        self.procfs_fd = ""
        self.procfs_scheduler = sched.scheduler(time.time, time.sleep)
        self.procfs_sample_interval = 1

        self.pid2procfds = defaultdict(dict)
        # self.container_id = -1 self.container_name = -1 self.cpu_usage = -1 
        # self.mem_usage_abs = -1 self.mem_usage_perc = -1 self.net_sends = -1
        # self.net_recvs = -1 self.block_reads = -1 self.block_writes = -1

    def build_and_exec(self, cmd, fname):
        cmdline = f"exec {cmd} > {OPREFIX}-{fname}.{OEXT}"
        subprocess.run(cmdline, shell=True)

    def launch_docker_monitor(self, stats_fname):
        cmd = f"exec {self.docker_stats} > {OPREFIX}-{stats_fname}.{OEXT}"
        log.info("docker monitor cmd : " +  cmd)
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, preexec_fn=os.setsid)
        self.docker_stats_pid = process.pid
        self.docker_stats_fname = stats_fname
        log.info(f"docker monitor started : {self.docker_stats_pid}, {self.docker_stats_fname}")

    def pid2docker(self, pid):
        return self.docker_name2id[self.docker_pid2name[pid]]

    def populate_file_handles(self):
        # pid to file handles
        self.pid2procfds[0]["cpu"] =  open(f"/proc/stat")
        for pid in self.docker_pids:
            #self.pid2procfds[pid] = {}
            self.pid2procfds[pid]["cpu"] =  open(f"/proc/{pid}/stat")
            self.pid2procfds[pid]["mem"] =  open(f"/proc/{pid}/status") #grep ^VmPeak VmRSS /proc/*/status 
            self.pid2procfds[pid]["blk"] =  open(f"/sys/fs/cgroup/blkio/docker/{self.pid2docker(pid)}/blkio.throttle.io_service_bytes")
        self.procfs_fd = open(f"{OPREFIX}-{self.procfs_fname}.{OEXT}", "w")
            #pid2procfds[pid]["net"] =  open(f"/proc/{pid}/") 

    def procfs_collector(self, cnt):
        log.info("collecting " + str(cnt))
        stat = " ".join(get_cpu_metrics(self.pid2procfds[0]["cpu"]).splitlines())
        for pid in self.docker_pids:
            cpu = get_cpu_metrics(self.pid2procfds[pid]["cpu"]).strip() + " , "
            mem = get_mem_metrics(self.pid2procfds[pid]["mem"], [16, 17, 21]) #VmPeak, VmSize, VmRSS
            blk = get_blk_metrics(self.pid2procfds[pid]["blk"], [0, 1]) # Read, Write
            out = f"SAMPLE_{cnt} {time.time()} {mem} {blk} {cpu} {''.join(stat)}\n"
            #print(str(out))
            self.procfs_fd.write(str(out))
        self.procfs_scheduler.enter(self.procfs_sample_interval, 1,
                     self.procfs_collector, (cnt+1, ))

    def launch_procfs_monitor(self, procfs_fname):
        self.procfs_fname = procfs_fname
        proc = Proc()
        wakus = proc.processes.cmdline('(nim-waku|gowaku)')
        log.info("wakus pids: " + str(wakus))
        self.populate_file_handles()
        log.info("files handles populated")
        self.procfs_scheduler.enter(self.procfs_sample_interval, 1,
                     self.procfs_collector, (0, ))
        self.procfs_scheduler.run()


    def build_info(self, ps_fname, inspect_fname, cpuinfo_fname, meminfo_fname):
        self.build_and_exec(self.docker_ps, ps_fname)
        self.build_and_exec(self.docker_inspect, inspect_fname)
        self.build_and_exec("cat /proc/cpuinfo", cpuinfo_fname)
        self.build_and_exec("cat /proc/meminfo", meminfo_fname)

        self.ps_fname = f"{OPREFIX}-{ps_fname}.{OEXT}"
        self.inspect_fname = f"{OPREFIX}-{inspect_fname}.{OEXT}"

        with open(self.ps_fname, "r") as f:
            for line in f:
                la = line.split("#")
                self.docker_name2id[la[1]] = la[0]
                self.dockers.append(la[0])
        with open(self.inspect_fname, "r") as f:
            for line in f:
                la = line.split("/")
                self.docker_pid2name[la[0]] = la[1]
                self.docker_pids.append(la[0])

        print(self.docker_pid2name, self.docker_name2id)
        log.info(f"dockers, pids : {str(self.dockers)}, {str(self.docker_pids)}")

    def spin_up(self, docker_fname, sysfs_fname, procfs_fname):
        log.info("Starting the docker monitor...")
        self.docker_thread = threading.Thread(
                target=self.launch_docker_monitor, args=(docker_fname,), daemon=True)
        self.docker_thread.start()
        #log.info("Starting the sysfs monitor...")
        #self.sysfs_thread = threading.Thread(
        #        target=self.launch_sysfs_monitor, args=(sysfs_fname,), daemon=True)
        #self.sysfs_thread.start()
        log.info("Starting the procfs monitor...")
        self.procfs_thread = threading.Thread(
                target=self.launch_procfs_monitor, args=(procfs_fname,), daemon=True)
        self.procfs_thread.start()

    def clean_up(self):
        os.kill(self.docker_stats_pid, signal.SIGTERM)
        log.info(f"docker monitor stopped : {self.docker_stats_pid}, {self.docker_stats_fname}")

    def launch_sysfs_monitor(self, sysfs_fname):
        #paths = [f"CGROUP+
        while True:
            time.sleep(self.procfs_sample_interval)
            log.info("collecting")
            for docker in self.dockers:
                 print(f"/sys/fs/cgroup/cpu/docker/{docker}/cpuacct.usage_all")
                 print(f"/sys/fs/cgroup/memory/docker/{docker}/memory.max_usage_in_byte")
            #break
        print(sysfs_fname)


def main(ctx: typer.Context):
    format = "%(asctime)s: %(message)s"
    log.basicConfig(format=format, level=log.INFO,
                        datefmt="%H:%M:%S")
    signal.signal(signal.SIGINT, signal_handler)

    log.info("Metrics : starting")
    metrics = MetricsCollector()

    log.info("Collecting info on the system and containers...")
    metrics.build_info("ps", "inspect", "cpuinfo", "meminfo")

    log.info("Starting the Measurement Threads")
    metrics.spin_up("stats", "sysfs", "procfs")

    # get sim time info from config.json? or  ioctl/select from WLS? or docker wait?
    time.sleep(metrics.procfs_sample_interval * 5)
    metrics.procfs_fd.close()

    # x.join()

    metrics.clean_up()
    log.info("Metrics : all done")


if __name__ == "__main__":
    typer.run(main)
