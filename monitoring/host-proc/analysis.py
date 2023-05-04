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
#import seaborn as sns

from src import vars
#from src import arg_parser
from src import topology
from src import log_parser
from src import analysis
#from src import prometheus
#from src import analysis_logger
#from src import plotting


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
    def compute_settling_times(self):
        ldir = str(self.log_dir)
        topology_info = topology.load_topology(f'{ldir}/{vars.G_TOPOLOGY_FILE_NAME}')
        topology.load_topics_into_topology(topology_info, f'{ldir}/config/topology_generated/')
        injected_msgs_dict = log_parser.load_messages(ldir)
        node_logs, msgs_dict, min_tss, max_tss = analysis.analyze_containers(topology_info, ldir)
        simulation_time_ms = round((max_tss - min_tss) / 1000000)
        log.info((f'Simulation started at {min_tss}, ended at {max_tss}. '
                  f'Effective simulation time was {simulation_time_ms} ms.'))
        analysis.compute_message_delivery(msgs_dict, injected_msgs_dict)
        analysis.compute_message_latencies(msgs_dict)
        self.msg_propagation_times = analysis.compute_propagation_times(msgs_dict)
        self.msg_injection_times = analysis.compute_injection_times(injected_msgs_dict)
        #print("message propagation_times: ", self.msg_propagation_times)

    def get_cid(self):
        return self.df.ContainerID

    def set_wakucids(self):
        self.waku_cids = self.df["ContainerID"].unique()

    def plot_settling_times(self):
        fig, axes = plt.subplots(1, 2, layout='constrained', sharey=True)
        fig.set_figwidth(12)
        fig.set_figheight(10)
        fig.suptitle(f'Settling Time: {len(self.msg_propagation_times)} messages')
        fig.supylabel("msecs")

        pp = PdfPages(f'{self.oprefix}-settling-time.pdf')
        #axes[0].violinplot([0], showmedians=True)
        # TODO: add docker id as legend to xticks 
        axes[0].set_xticks([x + 1 for x in range(len(self.waku_cids))])
        #axes[0].set_xticks(ticks=[x + 1 for x in range(len(self.waku_cids))], labels=self.df["ContainerID"].unique())
        axes[0].set_xlabel('TODO: revisit after Jordi added per-container settling times')

        #fig, axes = plt.subplots(2, 2, layout='constrained', sharey=True)
        axes[1].violinplot(self.msg_propagation_times, showmedians=True)
        #axes[0].spines[['right', 'top']].set_visible(False)
        axes[1].axes.xaxis.set_visible(False)
        pp.savefig(plt.gcf())
        pp.close()
        plt.show()

    def violin_plots_helper(self, col, cdf=True):
        fig, axes = plt.subplots(2, 2, layout='constrained', sharey=True)
        fig.set_figwidth(12)
        fig.set_figheight(10)
        fig.suptitle(self.col2title[col])
        fig.supylabel(self.col2units[col])

        pp = PdfPages(f'{self.oprefix}-{col}.pdf')
        per_cid_arr, all_arr = [], []

        # per docker violin plot
        axes[0,0].ticklabel_format(style='plain')
        axes[0,0].yaxis.grid(True)
        axes[0,0].set_xlabel('Container ID')
        for cid in self.waku_cids:
            if cdf:
                tmp = self.df[self.get_cid() == cid][col].values
            else:
                tmp = self.df[self.get_cid() == cid][col].diff().dropna().values
            #print(f'{cid}-{col}: ', tmp)
            per_cid_arr.append(tmp)
            all_arr = np.concatenate((all_arr, tmp), axis=0)

        axes[0,0].violinplot(dataset=per_cid_arr, showmeans=True)
        # TODO: add docker id as legend to xticks 
        axes[0,0].set_xticks([x + 1 for x in range(len(self.waku_cids))])

        # pooled  violin plot
        axes[1,0].ticklabel_format(style='plain')
        axes[1,0].yaxis.grid(True)
        axes[1,0].set_xlabel('')
        axes[1,0].violinplot(dataset=all_arr, showmeans=True)
        axes[1,0].axes.xaxis.set_visible(False)

        # per docker scatter plot
        axes[0,1].ticklabel_format(style='plain')
        axes[0,1].yaxis.grid(True)
        axes[0,1].set_xlabel('Time')
        for y in per_cid_arr:
            axes[0, 1].scatter(x=range(0, len(y)), y=y, marker='.')

        # pooled scatter plot
        axes[1,1].ticklabel_format(style='plain')
        axes[1,1].yaxis.grid(True)
        axes[1,1].set_xlabel('Time')
        for y in per_cid_arr:
            c = [2] * len(y)
            axes[1, 1].scatter(x=range(0, len(y)), y=y, c=c,marker='.')

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
                            "NetRecv" : "MiB",
                            "NetSent" : "MiB",
                            "BlockR" : "MiB",
                            "BlockW" : "MiB",
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
            self.df[size] = self.df[size].map(lambda x: h2b.convert(x.strip())/(1024*1024)) # MiBs
        for size in ["BlockR", "BlockW"]:
            self.df[size] = self.df[size].map(lambda x: h2b.convert(x.strip())/(1024*1024)) # MiBs
        self.df.to_csv(f'{self.oprefix}-cleaned.csv', sep='/')
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
        self.col2title = { 'VmPeak' : 'Memory: Peak Virtual Memory Usage',
                            'VmSize' : 'Memory: Current Virtual Memory Usage',
                            'VmHWM'  : 'Memory: Current Physical Memory Usage',
                            'VmRSS' : 'Memory: Peak Physical Memory Usage',
                            'VmData': 'Memory: Size of Data Segment',
                            'VmStk' : 'Memory: Size of Stack Segment',
                            'RxBytes'   : 'Network: Received Bytes',
                            'RxPackets' : 'Network: Received Packets',
                            'TxBytes'   : 'Network: Transmitted Bytes',
                            'TxPackets' : 'Network: Transmitted Packets',
                            'NetRX'      : 'Network: NetRX',
                            'NetWX'      : 'Network: NetWX',
                            'InOctets'   : 'Network: InOctets',
                            'OutOctets'  : 'Network: OutOctets',
                        'BLKR'       : 'Block Reads',
                        'BLKW'       : 'Block Writes'
                        }
        self.col2units = { 'VmPeak' : 'MiB',
                           'VmSize' : 'MiB',
                           'VmHWM'  : 'MiB',
                            'VmRSS' : 'MiB',
                            'VmData': 'MiB',
                            'VmStk' : 'MiB',
                         'RxBytes'   : 'MiB',
                         'RxPackets' : 'Packets',
                         'TxBytes'   : 'MiB',
                         'TxPackets' : 'Packets',
                        'NetRX'      : 'MiB',
                        'NetWX'      : 'MiB',
                        'InOctets'   : 'MiB',
                        'OutOctets'  : 'MiB',
                        'BLKR'       : 'MiB',
                        'BLKW'       : 'MiB'
                        }
                    #'CPU-SYS', 'cpu', 'cpu0', 'cpu1', 'cpu2', 'cpu3',
                    #'cpu4', 'cpu5', 'cpu6', 'cpu7', 'cpu8', 'cpu9', 'CPUUTIME', 'CPUSTIME'
        self.process_procfs_data()

    def pid2cid(pid):
        pass

    def process_procfs_data(self):
        if not path_ok(Path(self.fname)):
            sys.exit(0)

        self.df = pd.read_csv(self.fname, header=0,  comment='#', skipinitialspace = True,
        #self.df = pd.read_fwf(self.fname, header=0,  comment='#', skipinitialspace = True)
                delimiter=r"\s+",
                #delimiter=r"\s+"),
                usecols= ['EpochId', 'PID', 'TimeStamp', 'ContainerID',
                    'VmPeak', 'VmPeakUnit', 'VmSize', 'VmSizeUnit', 'VmHWM', 'VmHWMUnit',
                    'VmRSS', 'VmRSSUnit', 'VmData','VmDataUnit', 'VmStk', 'VmStkUnit',
                    'HostVIF', 'RxBytes', 'RxPackets', 'TxBytes', 'TxPackets',
                    'VETH', 'InOctets', 'OutOctets',
                    'DockerVIF', 'NetRX', 'NetWX',
                 'VETH',  'InOctets', 'OutOctets',
                    'BLKR', 'BLKW',
                    'CPU-SYS', 'cpu', 'cpu0', 'cpu1', 'cpu2', 'cpu3',
                   'cpu4', 'cpu5', 'cpu6', 'cpu7', 'cpu8', 'cpu9', 'CPUUTIME', 'CPUSTIME'])
        #print(self.df[['BLKR']].to_string(index=False))
        #print(self.df.columns)
        #print(self.df.shape)
        self.post_process()
        self.df.to_csv(f'{self.oprefix}-cleaned.csv', sep='/')

    def post_process(self):
        self.set_wakucids()
        #h2b = Human2BytesConverter()
        for size in ['VmPeak', 'VmSize', 'VmHWM','VmRSS', 'VmData','VmStk']:
            self.df[size] = self.df[size].map(lambda x: x/1024) # MiBs
        for size in ['RxBytes', 'TxBytes', 'InOctets','OutOctets', 'NetRX','NetWX']:
            self.df[size] = self.df[size].map(lambda x: x/(1024*1024)) # MiBs

        # TODO: compute CPU utilisation and add it as a column
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
        self.violin_plots_helper("VmPeak")
        self.violin_plots_helper("VmRSS")
        self.violin_plots_helper("VmSize")
        self.violin_plots_helper("VmHWM")
        self.violin_plots_helper("VmData")
        self.violin_plots_helper("VmStk")
        self.violin_plots_helper("RxBytes")
        self.violin_plots_helper("TxBytes")
        self.violin_plots_helper("NetRX")
        self.violin_plots_helper("NetWX")
        self.violin_plots_helper("InOctets")
        self.violin_plots_helper("OutOctets")
        self.violin_plots_helper("BLKR")
        self.violin_plots_helper("BLKW")


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
    procfs.compute_settling_times()
    procfs.violin_plots(cdf)
    procfs.plot_settling_times()
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
    dstats.compute_settling_times()
    dstats.violin_plots(cdf)
    dstats.plot_settling_times()
    df = dstats.get_df()

    print(f'Got {log_dir}')



if __name__ == "__main__":
    app()
