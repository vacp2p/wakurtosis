import typer

import sys
import os
#from stat import *
import stat
from pathlib import Path

import logging as log
import pandas as pd

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

# instantiate typer and set the commands
app = typer.Typer()

# process / plot docker-procfs.out
@app.command()
def procfs(procfs_fname: Path):
    if not path_ok(procfs_fname):
        sys.exit(0)
    df = pd.read_csv(procfs_fname, header=0,  comment='#', delim_whitespace=True)
    print(df.shape)
    print(df.columns)
    print(df.style)
    print(f'Got {procfs_fname}')

# process / plot docker-dstats.out
@app.command()
def dstats(dstats_fname: Path):
    if not path_ok(dstats_fname):
        sys.exit(0)
    df = pd.read_csv(dstats_fname, header=0,  comment='#', delimiter='/', usecols=["ContainerID", "ContainerName", "CPUPerc", "MemUse", "MemTotal", "MemPerc",  "NetRecv", "NetSent", "BlockR",  "BlockW",  "PIDS"])
    print(df.shape)
    print(df.columns)
    print(df.style)
    print(f'Got {dstats_fname}')

# add jordi's log processing for settling time
@app.command()
def simlog(log_dir: Path):
    if not path_ok(log_dir, True):
        sys.exit(0)
    print(f'Got {log_dir}')


if __name__ == "__main__":
    app()
