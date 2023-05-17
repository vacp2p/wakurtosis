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

from sklearn.cluster import KMeans

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
        self.df, self.n, self.keys, self.cols = pd.DataFrame(), 0, [], []
        self.col2title, self.col2units, self.key2nodes = {}, {}, {}
        self.msg_settling_times, self.msg_injection_times = {}, {}
        self.grp2idx, self.idx2grp = {}, {}
        self.fig, self.axes = "", ""

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

    def plot_settling_times(self):
        self.set_panel_size(2, 2, False)
        self.fig.set_figwidth(12)
        self.fig.set_figheight(10)
        self.fig.suptitle(f'Settling Time: {len(self.msg_propagation_times)} messages')
        self.fig.supylabel("msecs")

        pp = PdfPages(f'{self.oprefix}-settling-time.pdf')
        #axes[0].violinplot([0], showmedians=True)
        self.axes[0,0].set_xticks([x + 1 for x in range(len(self.keys))])
        #axes[0].set_xticks(ticks=[x + 1 for x in range(len(self.waku_cids))], labels=self.df["ContainerID"].unique())
        self.axes[0,0].set_xlabel('TODO: revisit after Jordi added per-container settling times')

        #fig, axes = plt.subplots(2, 2, layout='constrained', sharey=True)
        self.axes[1,0].violinplot(self.msg_propagation_times, showmedians=True)
        #axes[0].spines[['right', 'top']].set_visible(False)
        self.axes[1,0].axes.xaxis.set_visible(False)
        self.cluster_plot_helper(grp='ContainerID', cols=self.cols, axis=self.axes[0,1])
        pp.savefig(plt.gcf())
        pp.close()
        plt.show()

    def set_panel_size(self, m, n, shareY=False):
        self.fig, self.axes = plt.subplots(m, n, layout='constrained', sharey=shareY)

    def column_panel_helper(self, col, cdf=True):
        self.set_panel_size(2, 2)
        #fig, axes = plt.subplots(2, 2, layout='constrained', sharey=False)
        self.fig.set_figwidth(12)
        self.fig.set_figheight(10)
        self.fig.suptitle(self.col2title[col])
        self.fig.supylabel(self.col2units[col])

        pp = PdfPages(f'{self.oprefix}-{col}.pdf')
        per_key_arr, all_arr = [], []

        self.build_key2nodes()

        # per docker violin plot
        self.axes[0,0].ticklabel_format(style='plain')
        self.axes[0,0].yaxis.grid(True)
        for key in self.keys:
            if cdf:
                tmp = self.df[self.get_key() == key][col].values
            else:
                tmp = self.df[self.get_key() == key][col].diff().dropna().values
            per_key_arr.append(tmp)
            all_arr = np.concatenate((all_arr, tmp), axis=0)

        # NOTE: xticks are from self.df.Keys
        #axes[0,0].set_xticks([x + 1 for x in range(len(self.keys))])
        self.axes[0,0].set_xticks([x + 1 for x in range(len(self.keys))])
        labels = [ '{}{}'.format( ' ', k) for i, k in enumerate(self.keys)]
        self.axes[0,0].set_xticklabels(labels)
        legends = self.axes[0,0].violinplot(dataset=per_key_arr, showmeans=True)
        text = ""
        for key, nodes in self.key2nodes.items():
            text += f'{key} {", ".join(nodes)}\n'
        self.axes[0,0].text(0.675, 0.985, text, transform=self.axes[0,0].transAxes,
                fontsize=7, verticalalignment='top')

        # consolidated  violin plot
        self.axes[1,0].ticklabel_format(style='plain')
        self.axes[1,0].yaxis.grid(True)
        self.axes[1,0].set_xlabel('All Containers')
        self.axes[1,0].violinplot(dataset=all_arr, showmeans=True)
        self.axes[1,0].set_xticks([])
        self.axes[1,0].axes.xaxis.set_visible(False)

        # per docker scatter plot
        self.axes[0,1].ticklabel_format(style='plain')
        self.axes[0,1].yaxis.grid(True)
        self.axes[0,1].set_xlabel('Time')
        legends = []
        for i, key in enumerate(self.keys):
            y = per_key_arr[i]
            legends.append(self.axes[0,1].scatter(x=range(0, len(y)), y=y, marker='.'))
        self.axes[0,1].legend(legends, self.keys, scatterpoints=1,
                        loc='upper left', ncol=5,
                        fontsize=8)

        # consolidated/summed-up scatter plot
        self.axes[1,1].ticklabel_format(style='plain')
        self.axes[1,1].yaxis.grid(True)
        self.axes[1,1].set_xlabel('Time')
        out, out_avg, nkeys  = [], [], len(per_key_arr)
        # omit the very last measurement: could be a partial record
        jindices, iindices  =  range (len(per_key_arr[0])-1), range(len(per_key_arr))
        for j in jindices:
            out.append(0.0)
            for i in iindices:
                out[j] += per_key_arr[i][j]
            out_avg.append(out[j]/nkeys)
        self.axes[1,1].plot(out, color='b')
        self.axes[1,1].plot(out_avg, color='y')
        self.axes[1,1].legend([f'Total {self.col2title[col]}', f'Average {self.col2title[col]}'],
                loc='upper right', ncol=1, fontsize=8)
        pp.savefig(plt.gcf())
        pp.close()
        plt.show()

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

    def get_df(self):
        return self.df

    def build_cluster_index(self, grp):
        lst = self.df[grp].unique()
        self.grp2idx =  { val : i for i, val in enumerate(lst)}
        self.idx2grp =  { i : val for i, val in enumerate(lst)}
        self.df[f'{grp}_idx'] = self.df[grp].map(lambda x: self.grp2idx[x])

    def cluster_plot_helper(self, grp, cols, axis):
        self.build_cluster_index(grp)
        kmeans = KMeans(n_clusters= 10)

        groups = self.df[grp].unique()
        groups.sort()
        for g in groups:
            X =self.df.loc[self.df[grp] == g][cols]
#        for gid in self.df[grp].unique():
#            print("gid, grp :", gid, grp, self.df[grp].unique())
 #           sys.exit()
 #           X =self.df[self.df.ContainerID == gid][col]
            #print(X)
            labels = kmeans.fit_predict(X)
            #TODO: plot better. it is not interpretable now
            #plt.scatter(X.iloc[:, 0], X.iloc[:, 1], c=labels,  cmap='plasma')
            axis.scatter(x=range(0, len(labels)), y=labels, marker='.')#(X.iloc[:, 0], X.iloc[:, 1], c=labels,  cmap='plasma')
        axis.set_xlabel('Time')
        #axis.set_yticks([x  for x in range(len(groups))])
        axis.set_yticks(range(len(groups)))
        labels = [ '{}{}'.format( ' ', k) for i, k in enumerate(self.keys)]
        axis.set_yticklabels(labels)
        #plt.show()

    def phase_helper(self, grp, col):
        pass


# handle docker stats
class DStats(Plots, metaclass=Singleton):
    def __init__(self, log_dir, oprefix):
        Plots.__init__(self, log_dir, oprefix)
        self.dstats_fname = f'{log_dir}/dstats-data/docker-stats.out'
        self.kinspect_fname = f'{log_dir}/dstats-data/docker-kinspect.out'
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
        self.cols = ["CPUPerc", "MemUse","NetRecv", "NetSent", "BlockR", "BlockW"]
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
        self.df.to_csv(f'dstats-cleaned.csv', sep='/')
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

    def plot_column_panels(self, cdf):
        self.column_panel_helper("CPUPerc")
        self.column_panel_helper("MemUse")
        self.column_panel_helper("NetSent", cdf)
        self.column_panel_helper("NetRecv", cdf)
        self.column_panel_helper("BlockR", cdf)
        self.column_panel_helper("BlockW", cdf)


class HostProc(Plots, metaclass=Singleton):
    def __init__(self, log_dir, oprefix):
        Plots.__init__(self, log_dir, oprefix)
        self.fname = f'{log_dir}/host-proc-data/docker-proc.out'
        self.kinspect_fname = f'{log_dir}/host-proc-data/docker-kinspect.out'
        self.col2title = {  'CPUPERC'   : 'CPU Utilisation',
                            'VmPeak'    : 'Peak Virtual Memory Usage',
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
        self.col2units = {  'CPUPERC'   : '%',
                            'VmPeak'    : 'MiB',
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
        self.cols = ['VmPeak', 'VmSize', 'VmHWM', 'VmRSS', 'VmData', 'VmStk',
                            'RxBytes', 'RxPackets', 'TxBytes', 'TxPackets', 'NetRX', 'NetWX'
                            'InOctets', 'OutOctets', 'BLKR', 'BLKW']
        self.process_host_proc_data()

    '''def build_key2nodes(self):
        for key in self.df["Key"]:
            self.key2nodes[key] = self.df.loc[self.df['Key'] == key, 'NodeName'].unique()
            #self.df[Node][self.df.Key=key].unique()
    '''

    def process_host_proc_data(self):
        if not path_ok(Path(self.fname)):
            sys.exit(0)

        self.df = pd.read_csv(self.fname, header=0,  comment='#', skipinitialspace = True,
        #self.df = pd.read_fwf(self.fname, header=0,  comment='#', skipinitialspace = True)
                delimiter=r"\s+",
                usecols= ['EpochId', 'PID', 'TimeStamp', 'ContainerName', 'ContainerID', 'NodeName',
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
        #self.df['Key'] = self.df['ContainerName'].map(lambda x: x.split("--")[0])
        self.df['Key'] = self.df['NodeName']#.map(lambda x: x.split("--")[0])
        #self.df.rename(columns={'NodeName': 'Key'}, inplace=True)
        self.df.to_csv(f'host-proc-cleaned.csv', sep='/')
        self.set_keys()
        self.df.fillna(0)

    def plot_column_panels(self, cdf):
        self.column_panel_helper("CPUPERC")
        self.column_panel_helper("VmPeak")
        self.column_panel_helper("VmRSS")
        self.column_panel_helper("VmSize")
        self.column_panel_helper("VmHWM")
        self.column_panel_helper("VmData")
        self.column_panel_helper("VmStk")
        self.column_panel_helper("RxBytes")
        self.column_panel_helper("TxBytes")
        self.column_panel_helper("NetRX")
        self.column_panel_helper("NetWX")
        self.column_panel_helper("InOctets")
        self.column_panel_helper("OutOctets")
        self.column_panel_helper("BLKR")
        self.column_panel_helper("BLKW")

    def plot_clusters(self, grp, cdf, axes):
        self.cluster_plot_helper(col=['CPUPERC', 'VmPeak', 'VmRSS', 'VmSize', 'VmHWM', 'VmData'], grp=grp, axes=axes)

# instantiate typer and set the commands
app = typer.Typer()

# process / plot docker-procfs.out
@app.command()
def host_proc(log_dir: Path,
            oprefix:str = typer.Option("out", help="Specify the prefix for the plot pdfs"),
            cdf: bool = typer.Option(True, help="Specify whether to accumulate or dis-aggregate")):
    if not path_ok(log_dir, True):
        sys.exit(0)

    host_proc = HostProc(log_dir, oprefix)
    host_proc.compute_settling_times()
    host_proc.build_cluster_index('ContainerID')
    #host_proc.plot_clusters('ContainerID', cdf)
    host_proc.plot_column_panels(cdf)
    host_proc.plot_settling_times()
    df = host_proc.get_df()

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
    dstats.plot_settling_times()
    dstats.plot_column_panels(cdf)
    df = dstats.get_df()

    print(f'Got {log_dir}')



if __name__ == "__main__":
    app()
