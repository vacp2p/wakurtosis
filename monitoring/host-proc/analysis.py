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

import seaborn as sns

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
class Human2ByteConverter(metaclass=Singleton):
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


# handle docker stats
class DStats:
    def __init__(self, fname, oprefix):
        self.fname, self.df, self.waku_cids, self.n, self.prefix = fname, "", [], 0, oprefix
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
        self.start_processing()

    # remove the formatting artefacts
    def pre_process(self):
        regex = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        with open(self.fname) as f:
            cleaned_txt = regex.sub('', f.read())
        with open(self.fname, 'w') as f:
            f.write(cleaned_txt)

    # make sure the df is all numeric
    def post_process(self):
        for name in ["ContainerID", "ContainerName"]:
            self.df[name] = self.df[name].map(lambda x: x.strip())
        self.waku_cids = self.df["ContainerID"].unique()
        h2b, n = Human2ByteConverter(), len(self.waku_cids)
        for percent in ["CPUPerc", "MemPerc"]:
            self.df[percent] = self.df[percent].str.replace('%','').astype(float)
        for size in ["MemUse", "MemTotal"]:
            self.df[size] = self.df[size].map(lambda x: h2b.convert(x.strip())/(1024*1024)) # MiBs
        for size in ["NetRecv", "NetSent"]:
            self.df[size] = self.df[size].map(lambda x: h2b.convert(x.strip())/1024) # KiBs
        for size in ["BlockR", "BlockW"]:
            self.df[size] = self.df[size].map(lambda x: h2b.convert(x.strip())/1024) # KiBs
        #self.df.to_csv("processed.csv", sep='/')

    # build df from csv
    def start_processing(self):
        self.pre_process()
        self.df = pd.read_csv(self.fname, header=0,  comment='#', skipinitialspace = True,
                                delimiter='/', usecols=["ContainerID", "ContainerName",
                                    "CPUPerc", "MemUse", "MemTotal", "MemPerc",
                                    "NetRecv", "NetSent", "BlockR","BlockW",  "PIDS"])
        self.post_process()

    def violin_plots_helper(self, col, diff=False):
        fig, axes = plt.subplots(2, 2, layout='constrained', sharey=True)
        fig.set_figwidth(12)
        fig.set_figheight(10)
        fig.suptitle(self.col2title[col])
        fig.supylabel(self.col2units[col])

        pp = PdfPages(f'{self.prefix}-{col}.pdf')
        cid_arr, all_arr = [], []

        # per docker violin plot
        axes[0,0].ticklabel_format(style='plain')
        axes[0,0].yaxis.grid(True)
        axes[0,0].set_xlabel('Container ID')
        for cid in self.waku_cids:
            if diff:
                tmp = self.df[self.df.ContainerID == cid][col].diff().dropna().values
            else:
                tmp = self.df[self.df.ContainerID == cid][col].values
            cid_arr.append(tmp)
            all_arr = np.concatenate((all_arr, tmp), axis=0)
        axes[0,0].violinplot(dataset=cid_arr, showmeans=True)

        # blended  violin plot
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

        # blended scatter plot
        axes[1,1].ticklabel_format(style='plain')
        axes[1,1].yaxis.grid(True)
        axes[1,1].set_xlabel('Time')
        for y in cid_arr:
            c = [2] * len(y)
            axes[1, 1].scatter(x=range(0, len(y)), y=y, c=c,marker='.')

        pp.savefig(plt.gcf())
        pp.close()
        plt.show()

    def violin_plots(self):
        self.violin_plots_helper("CPUPerc")
        self.violin_plots_helper("MemUse")
        self.violin_plots_helper("NetSent", True)
        self.violin_plots_helper("NetRecv", True)
        self.violin_plots_helper("BlockR", True)
        self.violin_plots_helper("BlockW", True)

    def cluster_plots(self):
        pass

    def get_df(self):
        return self.df


# instantiate typer and set the commands
app = typer.Typer()

# process / plot docker-procfs.out
@app.command()
def procfs(procfs_fname: Path):
    if not path_ok(procfs_fname):
        sys.exit(0)
    df = pd.read_csv(procfs_fname, header=0,  comment='#', delim_whitespace=True, usecols= ['EpochId', 'PID', 'TimeStamp',  'VmPeak', 'VmPeakUnit', 'VmSize', 'VmSizeUnit', 'VmHWM', 'VmHWMUnit', 'VmRSS', 'VmRSSUnit', 'VmData','VmDataUnit', 'VmStk', 'VmStkUnit', 'HostVIF', 'RxBytes', 'RxPackets', 'TxBytes', 'TxPackets', 'DockerVIF', 'NetRX', 'NetWX', 'BLKR', 'BLKW', 'CPU-SYS', 'cpu', 'cpu0', 'cpu1', 'cpu2', 'cpu3', 'cpu4', 'cpu5', 'cpu6', 'cpu7', 'cpu8', 'cpu9', 'CPUUTIME', 'CPUSTIME'])
    print(df.shape)
    print(df.columns)
    print(df.style)
    print(f'Got {procfs_fname}')


# process / plot docker-dstats.out
@app.command()
def dstats(dstats_fname: Path, prefix:str = typer.Option("out",
            help="Specify the prefix for the plots")):
    if not path_ok(dstats_fname):
        sys.exit(0)

    dstats = DStats(dstats_fname, prefix)
    dstats.violin_plots()
    df = dstats.get_df()

    print(f'Got {dstats_fname}')

# add jordi's log processing for settling time
@app.command()
def simlog(log_dir: Path):
    if not path_ok(log_dir, True):
        sys.exit(0)
    print(f'Got {log_dir}')


if __name__ == "__main__":
    app()
