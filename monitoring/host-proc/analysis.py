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

#from collections import defaultdict

#from tqdm_loggable.auto import tqdm
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
        self.df, self.n, self.keys = "", 0, []
        self.col2title, self.col2units, self.key2nodes = {}, {}, {}
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

    def get_key(self):
        return self.df.Key

    def set_keys(self):
        self.keys = self.df['Key'].unique()
        self.keys.sort()

    def build_key2nodes(self):
        pass

    def plot_settling_times(self):
        fig, axes = plt.subplots(1, 2, layout='constrained', sharey=True)
        fig.set_figwidth(12)
        fig.set_figheight(10)
        fig.suptitle(f'Settling Time: {len(self.msg_propagation_times)} messages')
        fig.supylabel("msecs")

        pp = PdfPages(f'{self.oprefix}-settling-time.pdf')
        #axes[0].violinplot([0], showmedians=True)
        # TODO: add docker id as legend to xticks 
        axes[0].set_xticks([x + 1 for x in range(len(self.keys))])
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
        per_key_arr, all_arr = [], []


        self.build_key2nodes()
        # per docker violin plot
        axes[0,0].ticklabel_format(style='plain')
        axes[0,0].yaxis.grid(True)
        for key in self.keys:
            if cdf:
                tmp = self.df[self.get_key() == key][col].values
            else:
                tmp = self.df[self.get_key() == key][col].diff().dropna().values
            per_key_arr.append(tmp)
            all_arr = np.concatenate((all_arr, tmp), axis=0)

        # NOTE: xticks are from self.df.Keys
        #axes[0,0].set_xticks([x + 1 for x in range(len(self.keys))])
        axes[0,0].set_xticks([x + 1 for x in range(len(self.keys))])
        labels = [ '{}{}'.format( ' ', k) for i, k in enumerate(self.keys)]
        axes[0,0].set_xticklabels(labels)
        legends = axes[0,0].violinplot(dataset=per_key_arr, showmeans=True)
        text = ""
        for key, nodes in self.key2nodes.items():
            text += f'{key} {", ".join(nodes)}\n'
        axes[0,0].text(0.675, 0.985, text, transform=axes[0,0].transAxes, 
                fontsize=7, verticalalignment='top')

        # consolidated  violin plot
        axes[1,0].ticklabel_format(style='plain')
        axes[1,0].yaxis.grid(True)
        axes[1,0].set_xlabel('All Containers')
        axes[1,0].violinplot(dataset=all_arr, showmeans=True)
        axes[1,0].set_xticks([])
        axes[1,0].axes.xaxis.set_visible(False)

        # per docker scatter plot
        axes[0,1].ticklabel_format(style='plain')
        axes[0,1].yaxis.grid(True)
        axes[0,1].set_xlabel('Time')
        legends = []
        for i, key in enumerate(self.keys):
            y = per_key_arr[i]
            legends.append(axes[0,1].scatter(x=range(0, len(y)), y=y, marker='.'))
        axes[0,1].legend(legends, self.keys, scatterpoints=1,
                        loc='upper left', ncol=5,
                        fontsize=8)

        # consolidated/summed-up scatter plot
        axes[1,1].ticklabel_format(style='plain')
        axes[1,1].yaxis.grid(True)
        axes[1,1].set_xlabel('Time')
        out, nkeys  = [], len(per_key_arr)
        for j in range(len(per_key_arr[0])):
            out.append(0)
            for i in range(nkeys):
                out[j] += per_key_arr[i][j]
            out[j] = out[j]/nkeys
        for y in per_key_arr:
            c = ['m'] * len(y)
            axes[1, 1].scatter(x=range(0, len(y)), y=y, c=c,marker='.')
        legends = axes[1,1].plot(out, color='g')
        axes[1,1].legend(legends, [f'Average {self.col2title[col]}'], scatterpoints=1,
                        loc='upper right', ncol=1,
                        fontsize=8)
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
        self.dstats_fname = f'{log_dir}/dstats-stats/docker-stats.out'
        self.kinspect_fname = f'{log_dir}/dstats-stats/docker-kinspect.out'
        self.col2title = {  "ContainerID"   : "Docker ID",
                            "ContainerName" : "Docker Name",
                            "CPUPerc"       : "CPU Utilisation",
                            "MemUse"        : "Memory Usage",
                            "MemTotal"      : "Total Memory",
                            "MemPerc"       : "Memory Utilisation",
                            "NetRecv"       : "Network Received",
                            "NetSent"       : "Network Sent",
                            "BlockR"        : "Block Reads",
                            "BlockW"        : "Block Writes",
                            "PIDS"          : "Docker PIDS"}
        self.col2units = {  "ContainerID"   : "ID",
                            "ContainerName" : "Name",
                            "CPUPerc"       : "Percentage (%)",
                            "MemUse"        : "MiB",
                            "MemTotal"      : "MiB",
                            "MemPerc"       : "Percentage (%)",
                            "NetRecv"       : "MiB",
                            "NetSent"       : "MiB",
                            "BlockR"        : "MiB",
                            "BlockW"        : "MiB",
                            "PIDS"          : "PIDS"}
        self.process_dstats_data()

    # remove the formatting artefacts
    def pre_process(self):
        if not path_ok(Path(self.dstats_fname)):
            sys.exit(0)
        regex = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        with open(self.dstats_fname) as f:
            cleaned_txt = regex.sub('', f.read())
        with open(self.dstats_fname, 'w') as f:
            f.write(cleaned_txt)

    # make sure the df is all numeric
    def post_process(self):
        for name in ["ContainerID", "ContainerName"]:
            self.df[name] = self.df[name].map(lambda x: x.strip())
        h2b, n = Human2BytesConverter(), len(self.keys)
        for percent in ["CPUPerc", "MemPerc"]:
            self.df[percent] = self.df[percent].str.replace('%','').astype(float)
        for size in ["MemUse", "MemTotal"]:
            self.df[size] = self.df[size].map(lambda x: h2b.convert(x.strip())/(1024*1024)) # MiBs
        for size in ["NetRecv", "NetSent"]:
            self.df[size] = self.df[size].map(lambda x: h2b.convert(x.strip())/(1024*1024)) # MiBs
        for size in ["BlockR", "BlockW"]:
            self.df[size] = self.df[size].map(lambda x: h2b.convert(x.strip())/(1024*1024)) # MiBs
        self.df['Key'] = self.df['ContainerName'].map(lambda x: x.split("--")[0])
        self.df.to_csv(f'{self.oprefix}-cleaned.csv', sep='/')
        self.set_keys()

    # build df from csv
    def process_dstats_data(self):
        log.info(f'processing {self.dstats_fname}...')
        self.pre_process()
        self.df = pd.read_csv(self.dstats_fname, header=0,  comment='#', skipinitialspace = True,
                                delimiter='/',
                                usecols=["ContainerID", "ContainerName",
                                    "CPUPerc", "MemUse", "MemTotal", "MemPerc",
                                    "NetRecv", "NetSent", "BlockR","BlockW",  "PIDS"])
        self.post_process()

    def build_key2nodes(self):
        with open(self.kinspect_fname) as f:
            for line in f:
                if "User Services" in line:
                    f.readline()
                    break
            for line in f:
                if line == "\n":
                    break
                larray = line.split()
                if "containers_" in larray[1]:
                    key = larray[1]
                    self.key2nodes[key] = [larray[2].split("libp2p-")[1].replace(':', '')]
                elif "libp2p-node" in larray[0]:
                    self.key2nodes[key].append(larray[0].split("libp2p-")[1].replace(':', ''))

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
        self.col2title = { 'VmPeak'     : 'Peak Virtual Memory Usage',
                            'VmSize'    : 'Current Virtual Memory Usage',
                            'VmRSS'     : 'Peak Physical Memory Usage',
                            'VmHWM'     : 'Current Physical Memory Usage',
                            'VmData'    : 'Size of Data Segment',
                            'VmStk'     : 'Size of Stack Segment',
                            'RxBytes'   : 'Network1: Received Bytes',
                            'RxPackets' : 'Network1: Received Packets',
                            'TxBytes'   : 'Network1: Transmitted Bytes',
                            'TxPackets' : 'Network1: Transmitted Packets',
                            'NetRX'     : 'Network2: NetRX',
                            'NetWX'     : 'Network2: NetWX',
                            'InOctets'  : 'Network3: InOctets',
                            'OutOctets' : 'Network3: OutOctets',
                            'BLKR'      : 'Block Reads',
                            'BLKW'      : 'Block Writes'
                        }
        self.col2units = { 'VmPeak'     : 'MiB',
                           'VmSize'     : 'MiB',
                           'VmHWM'      : 'MiB',
                            'VmRSS'     : 'MiB',
                            'VmData'    : 'MiB',
                            'VmStk'     : 'MiB',
                            'RxBytes'   : 'MiB',
                            'RxPackets' : 'Packets',
                            'TxBytes'   : 'MiB',
                            'TxPackets' : 'Packets',
                            'NetRX'     : 'MiB',
                            'NetWX'     : 'MiB',
                            'InOctets'  : 'MiB',
                            'OutOctets' : 'MiB',
                            'BLKR'      : 'MiB',
                            'BLKW'      : 'MiB'
                        }
                    #'CPU-SYS', 'cpu', 'cpu0', 'cpu1', 'cpu2', 'cpu3',
                    #'cpu4', 'cpu5', 'cpu6', 'cpu7', 'cpu8', 'cpu9', 'CPUUTIME', 'CPUSTIME'
        self.process_procfs_data()

    def build_key2nodes(self):
        self.key2nodes[key] = .append(larray[0].split("libp2p-")[1].replace(':', ''))

    def process_procfs_data(self):
        if not path_ok(Path(self.fname)):
            sys.exit(0)

        self.df = pd.read_csv(self.fname, header=0,  comment='#', skipinitialspace = True,
        #self.df = pd.read_fwf(self.fname, header=0,  comment='#', skipinitialspace = True)
                delimiter=r"\s+",
                usecols= ['EpochId', 'PID', 'TimeStamp', 'ContainerID', 'NodeName',
                    'VmPeak', 'VmPeakUnit', 'VmSize', 'VmSizeUnit', 'VmHWM', 'VmHWMUnit',
                    'VmRSS', 'VmRSSUnit', 'VmData','VmDataUnit', 'VmStk', 'VmStkUnit',
                    'HostVIF', 'RxBytes', 'RxPackets', 'TxBytes', 'TxPackets',
                    'VETH', 'InOctets', 'OutOctets',
                    'DockerVIF', 'NetRX', 'NetWX',
                    'VETH',  'InOctets', 'OutOctets',
                    'BLKR', 'BLKW',
                    'CPUPERC'])
                    #'CPU-SYS', 'cpu', 'cpu0', 'cpu1', 'cpu2', 'cpu3',
                   #'cpu4', 'cpu5', 'cpu6', 'cpu7', 'cpu8', 'cpu9', 'CPUUTIME', 'CPUSTIME'])
        #print(self.df[['BLKR']].to_string(index=False))
        #print(self.df.columns)
        #print(self.df.shape)
        self.post_process()
        self.df.to_csv(f'{self.oprefix}-cleaned.csv', sep='/')

    def post_process(self):
        #h2b = Human2BytesConverter()
        for size in ['VmPeak', 'VmSize', 'VmHWM','VmRSS', 'VmData','VmStk']:
            self.df[size] = self.df[size].map(lambda x: x/1024) # MiBs
        for size in ['RxBytes', 'TxBytes', 'InOctets','OutOctets', 'NetRX','NetWX']:
            self.df[size] = self.df[size].map(lambda x: x/(1024*1024)) # MiBs
        for size in ['BLKR', 'BLKW']:
            self.df[size] = self.df[size].map(lambda x: x/(1024*1024)) # MiBs
        self.df['Key'] = self.df['PID']
        #self.df.rename(columns={'NodeName': 'Key'}, inplace=True)
        self.df.to_csv(f'{self.oprefix}-cleaned.csv', sep='/')
        self.set_keys()

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
