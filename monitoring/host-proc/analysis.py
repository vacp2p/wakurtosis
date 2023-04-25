import typer

import sys
import os
#from stat import *
import stat
from pathlib import Path

import time
import re

import matplotlib.pyplot as plt

import logging as log
import pandas as pd
import numpy as np


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


# remove formatting artefacts
def sanitise_dstats_file(fname):
    regex = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    with open(fname) as f:
        cleaned_txt = regex.sub('', f.read())
    with open(fname, 'w') as f:
        f.write(cleaned_txt)


let3 = {'GiB':1024*1024*1024, 'MiB':1024*1024, 'KiB':1024}
let22 = {'GB':1024*1024*1024, 'MB':1024*1024, 'KB':1024}
let21 = {'gB':1000*1000*1000, 'mB':1000*1000, 'kB':1000}
let1 = {'B':1}

# convert human readable sizes to bytes
def size_convert(value):
    k3, k2, k1 = value[-3:], value[-2:], value[-1:]
    if k3 in let3:
        return float(value[:-3])*let3[k3]
    elif k2 in let22:
        return float(value[:-2])*let22[k2]
    elif k2 in let21:
        return float(value[:-2])*let21[k2]
    elif k1 in let1:
      return float(value[:-1])
    else:
      return np.nan

# make sure the df is all numeric
def sanitise_dstats_df(df):
    df['CPUPerc'] = df['CPUPerc'].str.replace('%','').astype(float)
    df['MemPerc'] = df['MemPerc'].str.replace('%','').astype(float)
    for size in ["MemUse", "MemTotal", "NetRecv", "NetSent", "BlockR", "BlockW"]:
        df[size] = df[size].map(lambda x: size_convert(x.strip()))
    return df


def get_dstats_df(dstats_fname):
    sanitise_dstats_file(dstats_fname)
    df = pd.read_csv(dstats_fname, header=0,  comment='#', skipinitialspace = True, delimiter='/', usecols=["ContainerID", "ContainerName", "CPUPerc", "MemUse", "MemTotal", "MemPerc",  "NetRecv", "NetSent", "BlockR",  "BlockW",  "PIDS"])
    return sanitise_dstats_df(df)


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
def dstats(dstats_fname: Path):
    if not path_ok(dstats_fname):
        sys.exit(0)

    df = get_dstats_df(dstats_fname)
    wakus = df["ContainerID"].unique()
    print(f'unique: {len(wakus)}')
    df["CPUPerc"].plot()
    df["MemPerc"].plot()
    df["MemUse"].plot()
    plt.show()
    print(f'Got {dstats_fname}')

# add jordi's log processing for settling time
@app.command()
def simlog(log_dir: Path):
    if not path_ok(log_dir, True):
        sys.exit(0)
    print(f'Got {log_dir}')


if __name__ == "__main__":
    app()
