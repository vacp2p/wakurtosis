import logging as log

import os, threading, subprocess, signal

import time
import typer

CGROUP="/sys/fs/cgroup/"

class MetricsCollector:
    def __init__(self):
        self.docker_ps = "docker ps --no-trunc --filter \"ancestor=statusteam/nim-waku\"  --filter \"ancestor=gowaku\" --format \"{{.ID}}#{{.Names}}#{{.Image}}#{{.Command}}#{{.State}}#{{.Status}}#{{.Ports}}\" "
        self.dockers = []

        self.docker_stats = "docker stats --no-trunc --format  \"{{.Container}} / {{.Name}} / {{.ID}} / {{.CPUPerc}} / {{.MemUsage}} / {{.MemPerc}} / {{.NetIO}} / {{.BlockIO}} / {{.PIDs}}\" "
        self.docker_stats_pid = 0
        self.docker_stats_fname = 0

        self.sample_rate = 10

        self.container_id = -1
        self.container_name = -1
        self.cpu_usage = -1
        self.mem_usage_abs = -1
        self.mem_usage_perc = -1
        self.net_sends = -1
        self.net_recvs = -1
        self.block_reads = -1
        self.block_writes = -1


    def launch_docker_monitor(self, fname):
        cmd = f"exec {self.docker_stats} > {fname}"
        log.info("docker monitor cmd : " +  cmd)
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, preexec_fn=os.setsid)
        self.docker_stats_pid = process.pid
        self.docker_stats_fname = fname
        log.info(f"docker monitor started : {self.docker_stats_pid}, {self.docker_stats_fname}")
        #process=subprocess.Popen("", shell=True)
        #os.killpg(os.getpgid(process.pid), signal.SIGTERM)  # Send the signal to all process groups

    def launch_sysfs_monitor(self, fname):
        while True:
            time.sleep(self.sample_rate)
            #break
        print(fname)

    def get_docker_info(self, fname):
        cmd = f"exec {self.docker_ps} > {fname}"
        log.info("docker data cmd : " +  cmd)
        subprocess.run(cmd, shell=True)
        with open(fname, "r") as f:
            self.dockers = [line.split("#")[0] for line in f]
        log.info("dockers : " + str(self.dockers))
 
    def spin_up(self, docker_fname, sysfs_fname):
        log.info("Starting the docker monitor...")
        self.docker_thread = threading.Thread(
                target=self.launch_docker_monitor, args=("docker-stats.out",), daemon=True)
        self.docker_thread.start()
        log.info("Starting the sysfs monitor...")
        self.sysfs_thread = threading.Thread(
                target=self.launch_sysfs_monitor, args=("sysfs.out",), daemon=True)
        self.sysfs_thread.start()

    def clean_up(self):
        os.kill(self.docker_stats_pid, signal.SIGTERM)  
        log.info(f"docker monitor stopped : {self.docker_stats_pid}, {self.docker_stats_fname}")


def main(ctx: typer.Context):
    format = "%(asctime)s: %(message)s"
    log.basicConfig(format=format, level=log.INFO,
                        datefmt="%H:%M:%S")

    log.info("Metrics : starting")
    metrics = MetricsCollector()

    log.info("Collecting info on running dockers...")
    metrics.get_docker_info("docker-ps.out")
    
    log.info("Starting the Measurement Threads")
    metrics.spin_up("docker-stats.out", "docker-sysfs-stats.out")

    # get sim time info from config.json? or  ioctl/select from WLS? 
    time.sleep(10)

    # x.join()

    metrics.clean_up()
    log.info("Metrics : all done")


if __name__ == "__main__":
    typer.run(main)
