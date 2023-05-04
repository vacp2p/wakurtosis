import typer

import sys
import os
import stat
from pathlib import Path

import time

import re

import logging as log
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from tqdm_loggable.auto import tqdm
import seaborn as sns

from src import vars
from src import arg_parser
from src import topology
from src import log_parser
from src import analysis
#from src import prometheus
from src import analysis_logger
from src import plotting


# check if the path exists and is of appropriate type
def path_ok(path : Path, isDir=False):
    if not path.exists():
        log.error(f'"{path}" does not exist')
        return False
    mode = path.stat().st_mode
    if not isDir and not stat.S_ISREG(mode):
        log.error(f'File expected: "{path}" is not a file')
        return False
    if isDir and not stat.S_ISDIR(mode):
        log.error(f'Directory expected: "{path}" is not a directory')
        return False
    # lay off permission checks; resolve them lazily with open
    return True


# define singleton 
class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


# convert human readable sizes to bytes
class Human2BytesConverter(metaclass=Singleton):
    def __init__(self):     # add any human readable format/size and multiplier here
        self.letters    = {}
        self.letters[3] = {'GiB' : 1024*1024*1024, 'MiB' : 1024*1024, 'KiB' : 1024}
        self.letters[2] = {'GB' : 1024*1024*1024, 'MB' : 1024*1024, 'KB' : 1024,
                            'gB' : 1000*1000*1000, 'mB' : 1000*1000, 'kB' : 1000}
        self.letters[1] = {'B':1}

    def convert(self, value):
        for i in [3, 2, 1]:
            k = value[-i:]
            if k in self.letters[i]:
                return float(value[:-i]) * self.letters[i][k]
        return np.nan

# Base class for plots and common API
class Plots(metaclass=Singleton):
    def __init__(self, log_dir, oprefix):
        self.log_dir, self.oprefix = log_dir, oprefix
        self.df, self.n, self.waku_cids = "", 0, []
        self.col2title, self.col2units = {}, {}
        self.msg_settling_times, self.msg_injection_times = {}, {}

    # jordi's log processing
    def compute_settling_time(self):
        ldir = str(self.log_dir)

        topology_info = topology.load_topology(f'{ldir}/{vars.G_TOPOLOGY_FILE_NAME}')
        topology.load_topics_into_topology(topology_info, f'{ldir}/config/topology_generated/')
        injected_msgs_dict = log_parser.load_messages(ldir)
        node_logs, msgs_dict, min_tss, max_tss = analysis.analyze_containers(topology_info,
                                                                         ldir)

        """ Compute simulation time window """
        simulation_time_ms = round((max_tss - min_tss) / 1000000)
        analysis_logger.G_LOGGER.info(f'Simulation started at {min_tss}, ended at {max_tss}. '
                                  f'Effective simulation time was {simulation_time_ms} ms.')

        analysis.compute_message_delivery(msgs_dict, injected_msgs_dict)
        analysis.compute_message_latencies(msgs_dict)
        self.msg_propagation_times = analysis.compute_propagation_times(msgs_dict)
        self.msg_injection_times = analysis.compute_injection_times(injected_msgs_dict)
        print("message propagation_times: ", self.msg_propagation_times)

    def get_cid(self):
        return self.df.ContainerID

    def set_wakucids(self):
        self.waku_cids = self.df["ContainerID"].unique()

    def violin_plots_helper(self, col, cdf=True):
        fig, axes = plt.subplots(2, 2, layout='constrained', sharey=True)
        fig.set_figwidth(12)
        fig.set_figheight(10)
        fig.suptitle(self.col2title[col])
        fig.supylabel(self.col2units[col])

        pp = PdfPages(f'{self.oprefix}-{col}.pdf')
        cid_arr, all_arr = [], []

        # per docker violin plot
        axes[0,0].ticklabel_format(style='plain')
        axes[0,0].yaxis.grid(True)
        axes[0,0].set_xlabel('Container ID')
        for cid in self.waku_cids:
            if cdf:
                tmp = self.df[self.get_cid() == cid][col].values
            else:
                tmp = self.df[self.get_cid() == cid][col].diff().dropna().values
            cid_arr.append(tmp)
            all_arr = np.concatenate((all_arr, tmp), axis=0)

        axes[0,0].violinplot(dataset=cid_arr, showmeans=True)

        # pooled  violin plot
        axes[1,0].ticklabel_format(style='plain')
        axes[1,0].yaxis.grid(True)
        axes[1,0].set_xlabel('')
        axes[1,0].violinplot(dataset=all_arr, showmeans=True)

        # per docker scatter plot
        axes[0,1].ticklabel_format(style='plain')
        axes[0,1].yaxis.grid(True)
        axes[0,1].set_xlabel('Time')
        for y in cid_arr:
            axes[0, 1].scatter(x=range(0, len(y)), y=y, marker='.')

        # pooled scatter plot
        axes[1,1].ticklabel_format(style='plain')
        axes[1,1].yaxis.grid(True)
        axes[1,1].set_xlabel('Time')
        for y in cid_arr:
            c = [2] * len(y)
            axes[1, 1].scatter(x=range(0, len(y)), y=y, c=c,marker='.')

        pp.savefig(plt.gcf())
        pp.close()
        plt.show()

    def plot_settling_time(self):
        fig, axes = plt.subplots(2, 2, layout='constrained', sharey=True)
        fig.set_figwidth(12)
        fig.set_figheight(10)
        fig.suptitle("Settling Time")
        fig.supylabel("msecs")

        pp = PdfPages(f'{self.oprefix}-settling-time.pdf')
        cid_arr, all_arr = [], []

        #fig, axes = plt.subplots(2, 2, layout='constrained', sharey=True)
        axes[0,0].violinplot(self.msg_propagation_times, showmedians=True)
        axes[0,0].set_title(
            f'Message propagation times\n(sample size: {len(self.msg_propagation_times)} messages)')
        axes[0,0].set_ylabel('Propagation Time (ms)')
        axes[0,0].spines[['right', 'top']].set_visible(False)
        axes[0,0].axes.xaxis.set_visible(False)
        pp.savefig(plt.gcf())
        pp.close()
        plt.show()

    def get_df(self):
        return self.df

    def cluster_plots_helper(self, col):
        pass


# handle docker stats
class DStats(Plots, metaclass=Singleton):
    def __init__(self, log_dir, oprefix):
        Plots.__init__(self, log_dir, oprefix)
        self.fname = f'{log_dir}/host-proc-stats/docker-stats.out'
        self.col2title = {  "ContainerID": "Docker ID",
                            "ContainerName" : "Docker Name",
                            "CPUPerc" : "CPU Utilisation",
                            "MemUse" : "Memory Usage",
                            "MemTotal" : "Total Memory",
                            "MemPerc" : "Memory Utilisation",
                            "NetRecv" : "Network Received",
                            "NetSent" : "Network Sent",
                            "BlockR" : "Block Reads",
                            "BlockW" : "Block Writes",
                            "PIDS" : "Docker PIDS"}
        self.col2units = {  "ContainerID": "ID",
                            "ContainerName" : "Name",
                            "CPUPerc" : "Percentage (%)",
                            "MemUse" : "MiB",
                            "MemTotal" : "MiB",
                            "MemPerc" : "Percentage (%)",
                            "NetRecv" : "KiB",
                            "NetSent" : "KiB",
                            "BlockR" : "KiB",
                            "BlockW" : "KiB",
                            "PIDS" : "PIDS"}
        self.process_dstats_data()

    # remove the formatting artefacts
    def pre_process(self):
        if not path_ok(Path(self.fname)):
            sys.exit(0)
        regex = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        with open(self.fname) as f:
            cleaned_txt = regex.sub('', f.read())
        with open(self.fname, 'w') as f:
            f.write(cleaned_txt)

    # make sure the df is all numeric
    def post_process(self):
        for name in ["ContainerID", "ContainerName"]:
            self.df[name] = self.df[name].map(lambda x: x.strip())
        h2b, n = Human2BytesConverter(), len(self.waku_cids)
        for percent in ["CPUPerc", "MemPerc"]:
            self.df[percent] = self.df[percent].str.replace('%','').astype(float)
        for size in ["MemUse", "MemTotal"]:
            self.df[size] = self.df[size].map(lambda x: h2b.convert(x.strip())/(1024*1024)) # MiBs
        for size in ["NetRecv", "NetSent"]:
            self.df[size] = self.df[size].map(lambda x: h2b.convert(x.strip())/1024) # KiBs
        for size in ["BlockR", "BlockW"]:
            self.df[size] = self.df[size].map(lambda x: h2b.convert(x.strip())/1024) # KiBs
        self.df.to_csv("processed-dstats.csv", sep='/')
        self.set_wakucids()

    # build df from csv
    def process_dstats_data(self):
        log.info(f'processing {self.fname}...')
        self.pre_process()
        self.df = pd.read_csv(self.fname, header=0,  comment='#', skipinitialspace = True,
                                delimiter='/', usecols=["ContainerID", "ContainerName",
                                    "CPUPerc", "MemUse", "MemTotal", "MemPerc",
                                    "NetRecv", "NetSent", "BlockR","BlockW",  "PIDS"])
        self.post_process()

    def violin_plots(self, cdf):
        self.violin_plots_helper("CPUPerc")
        self.violin_plots_helper("MemUse")
        self.violin_plots_helper("NetSent", cdf)
        self.violin_plots_helper("NetRecv", cdf)
        self.violin_plots_helper("BlockR", cdf)
        self.violin_plots_helper("BlockW", cdf)


class ProcFS(Plots, metaclass=Singleton):
    def __init__(self, log_dir, oprefix):
        Plots.__init__(self, log_dir, oprefix)
        self.fname = f'{log_dir}/host-proc-stats/docker-proc.out'
        # TODO: define CPU stuff
        self.col2title = { 'VmPeak' : 'Peak Virtual Memory Usage',
                           'VmSize' : 'Current Virtual Memory Usage',
                           'VmHWM'  : 'Current Physical Memory Usage',
                            'VmRSS' : 'Peak Physical Memory Usage',
                            'VmData': 'Size of Data Segment',
                            'VmStk' : 'Size of Stack Segment',
                         'RxBytes'   : 'Received Bytes',
                         'RxPackets' : 'Received Packets',
                         'TxBytes'   : 'Transmitted Bytes',
                         'TxPackets' : 'Transmitted Packets',
                        'NetRX'      : 'NetRX',
                        'NetWX'      : 'NetWX',
                        'BLKR'       : 'Block Reads',
                        'BLKW'       : 'Block Writes'
                        }
        self.col2units = { 'VmPeak' : 'KBis',
                           'VmSize' : 'KBis',
                           'VmHWM'  : 'KBis',
                            'VmRSS' : 'KBis',
                            'VmData': 'KBis',
                            'VmStk' : 'KBis',
                         'RxBytes'   : 'Bytes',
                         'RxPackets' : 'Packets',
                         'TxBytes'   : 'Bytes',
                         'TxPackets' : 'Packets',
                        'NetRX'      : 'Bytes',
                        'NetWX'      : 'Bytes',
                        'BLKR'       : 'Bytes',
                        'BLKW'       : 'Bytes'
                        }
                    #'CPU-SYS', 'cpu', 'cpu0', 'cpu1', 'cpu2', 'cpu3',
                    #'cpu4', 'cpu5', 'cpu6', 'cpu7', 'cpu8', 'cpu9', 'CPUUTIME', 'CPUSTIME'
        self.process_procfs_data()

    def pid2cid(pid):
        pass

    def process_procfs_data(self):
        if not path_ok(Path(self.fname)):
            sys.exit(0)

        self.df = pd.read_csv(self.fname, header=0,  comment='#',
                delim_whitespace=True,
                usecols= ['EpochId', 'PID', 'TimeStamp', 'ContainerID',
                    'VmPeak', 'VmPeakUnit', 'VmSize', 'VmSizeUnit', 'VmHWM', 'VmHWMUnit',
                    'VmRSS', 'VmRSSUnit', 'VmData','VmDataUnit', 'VmStk', 'VmStkUnit',
                    'HostVIF', 'RxBytes', 'RxPackets', 'TxBytes', 'TxPackets',
                    'DockerVIF', 'NetRX', 'NetWX',
                    'BLKR', 'BLKW',
                    'CPU-SYS', 'cpu', 'cpu0', 'cpu1', 'cpu2', 'cpu3',
                    'cpu4', 'cpu5', 'cpu6', 'cpu7', 'cpu8', 'cpu9', 'CPUUTIME', 'CPUSTIME'])
        self.post_process()
        self.df.to_csv("processed-procfs.csv", sep=' ')

    def post_process(self):
        # TODO: compute CPU utilisation and add a column
        pass
        '''for name in  ['EpochId', 'PID', 'TimeStamp', 'ContainerID',
                    'VmPeak', 'VmPeakUnit', 'VmSize', 'VmSizeUnit', 'VmHWM', 'VmHWMUnit',
                    'VmRSS', 'VmRSSUnit', 'VmData','VmDataUnit', 'VmStk', 'VmStkUnit',
                    'HostVIF', 'RxBytes', 'RxPackets', 'TxBytes', 'TxPackets',
                    'DockerVIF', 'NetRX', 'NetWX',
                    'BLKR', 'BLKW']:
                    #'CPU-SYS', 'cpu', 'cpu0', 'cpu1', 'cpu2', 'cpu3',
                    #'cpu4', 'cpu5', 'cpu6', 'cpu7', 'cpu8', 'cpu9', 'CPUUTIME', 'CPUSTIME']:
            self.df[name] = self.df[name].map(lambda x: x.strip())
            '''

    def violin_plots(self, cdf):
        pass
        #self.violin_plots_helper("CPUPerc")
        #self.violin_plots_helper("MemUse")
        #self.violin_plots_helper("NetSent", cdf)
        #self.violin_plots_helper("NetRecv", cdf)
        #self.violin_plots_helper("BlockR", cdf)
        self.violin_plots_helper("BLKW", cdf)


# instantiate typer and set the commands
app = typer.Typer()

# process / plot docker-procfs.out
@app.command()
def procfs(log_dir: Path,
            oprefix:str = typer.Option("out", help="Specify the prefix for the plot pdfs"),
            cdf: bool = typer.Option(True, help="Specify the prefix for the plots")):
    if not path_ok(log_dir, True):
        sys.exit(0)

    procfs = ProcFS(log_dir, oprefix)
    procfs.violin_plots(cdf)
    #procfs.compute_settling_time()
    df = procfs.get_df()

    print(f'Got {log_dir}')


# process / plot docker-dstats.out
@app.command()
def dstats(log_dir: Path,
            oprefix:str = typer.Option("out", help="Specify the prefix for the plot pdfs"),
            cdf: bool = typer.Option(True, help="Specify the prefix for the plots")):
    if not path_ok(log_dir, True):
        sys.exit(0)

    dstats = DStats(log_dir, oprefix)
    #dstats.violin_plots(cdf)
    dstats.compute_settling_time()
    dstats.plot_settling_time()
    df = dstats.get_df()

    print(f'Got {log_dir}')



if __name__ == "__main__":
    app()
