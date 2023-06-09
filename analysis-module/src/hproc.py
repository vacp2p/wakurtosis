import typer
import sys
import os
import stat
import math
from pathlib import Path
import time
import json
import networkx as nx
import re
import logging as log
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from sklearn.cluster import KMeans

from src import vars
from src import topology
from src import log_parser
from src import analysis

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
    # lay off the permission checks; resolve them lazily with open
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


# Base class for plots and common helpers
class Plots(metaclass=Singleton):
    def __init__(self, log_dir, oprefix, jf, to_plot, cfile):
        self.log_dir, self.oprefix = log_dir, oprefix
        self.df, self.n, self.keys, self.cols = pd.DataFrame(), 0, [], []
        self.col2title, self.col2units, self.key2nodes = {}, {}, {}
        self.msg_settling_times, self.msg_injection_times = {}, {}
        self.grp2idx, self.idx2grp = {}, {}
        self.fig, self.axes = "", ""
        self.json_fname, self.G = jf, nx.empty_graph()
        self.to_plot, self.to_compare = to_plot, []
        self.run_summary, self.cfile = "", cfile

    # waku log processing
    def compute_msg_settling_times(self):
        ldir = str(self.log_dir)
        topology_info = topology.load_json(f'{ldir}/{vars.G_TOPOLOGY_FILE_NAME}')
        topology.load_topics_into_topology(topology_info, f'{ldir}/config/topology_generated/')
        injected_msgs_dict = log_parser.load_messages(ldir)
        node_logs, msgs_dict, min_tss, max_tss = analysis.analyze_containers(topology_info, ldir)
        simulation_time_ms = round((max_tss - min_tss) / 1000000)
        log.info((f'Simulation started at {min_tss}, ended at {max_tss}. '
                  f'Effective simulation time was {simulation_time_ms} ms.'))
        analysis.compute_message_delivery(msgs_dict, injected_msgs_dict)
        analysis.compute_message_latencies(msgs_dict)
        self.msg_settling_times = analysis.compute_propagation_times(msgs_dict)
        self.msg_injection_times = analysis.compute_injection_times(injected_msgs_dict)
        #print("message propagation_times: ", self.msg_settling_times)

    def get_key(self):
        return self.df.Key

    def set_keys(self):
        self.keys = self.df['Key'].unique()
        self.keys.sort()

    # set the summary for the run: to be used for plot title
    def set_summary(self):
        with open(self.cfile, 'r') as f:  # Load config file
            conf = json.load(f)
            minsize = int(conf["wls"]["min_packet_size"]/1024)
            maxsize = int(conf["wls"]["max_packet_size"]/1024)
            self.run_summary = (f'{conf["gennet"]["num_nodes"]}by'
                                f'{conf["gennet"]["container_size"]}fo'
                                f'{conf["gennet"]["fanout"]}-'
                                f'{conf["wls"]["message_rate"]}mps-'
                                f'({minsize}-{maxsize})KiB-'
                                f'{conf["wls"]["simulation_time"]}sec')
        print(f'summary: {self.run_summary} (from {self.cfile})')

    # set the fields that go into the comparison panel
    def set_compare(self, lst):
        self.to_compare = lst

    # extract the maximal complete sample set
    def remove_incomplete_samples(self, grp, err=''):
        #if not err:
        self.df, minRows = self.df[~self.df.isin([err]).any(axis=1)], sys.maxsize
        for cid in self.df[grp].unique():
            rows = self.df[self.df[grp] == cid].shape[0]
            minRows = rows if minRows > rows else minRows
        self.df = self.df.groupby(grp).head(minRows)

    # plot the settling times, both network- and node-wise
    def plot_msg_settling_times(self):
        self.set_panel_size(2, 1, False)
        nmsgs = len(self.msg_settling_times)
        self.fig.suptitle(f'Settling Time: {self.run_summary}, {nmsgs} msgs')
        self.fig.supylabel("msecs")
        self.axes[0].set_xticks([x + 1 for x in range(len(self.keys))])
        #axes[0].set_xticks(ticks=[x + 1 for x in range(len(self.waku_cids))], labels=self.df["ContainerID"].unique())
        self.axes[0].set_xlabel('TODO: revisit after Jordi added per-container settling times')

        self.axes[1].violinplot(self.msg_settling_times, showmedians=True)
        self.axes[1].axes.xaxis.set_visible(False)
        plt.savefig(f'{self.oprefix}-settling-time.pdf', format="pdf", bbox_inches="tight")
        #plt.show()

    # set the panel params
    def set_panel_size(self, m, n, shareY=False):
        self.fig, self.axes = plt.subplots(m, n, layout='constrained', sharey=shareY)
        self.fig.set_figwidth(12)
        self.fig.set_figheight(10)

    # plot col panels for selected columns
    def plot_col_panels(self, agg):
        for col in self.to_plot["ColPanel"]:
            if col not in self.df.columns:
                log.error(f"ColPanel: {col} is not in {self.df.columns}, skipping...")
                continue
            if col in ["CPUPerc", "MemUse"]:
                self.col_panel_helper(col)
            else:
                self.col_panel_helper(col, agg)

    # plot degree/col panels for the given set of columns
    def plot_deg_col_panels(self):
        for col in self.to_plot["DegColPanel"]:
            if col not in self.df.columns:
                log.error(f"DegColPanel: {col} is not in {self.df.columns}, skipping...")
                continue
            self.deg_col_panel_helper(col) # only agg for now 

    # plot the column panel
    def col_panel_helper(self, col, agg=True):
        self.set_panel_size(2, 2)
        self.fig.suptitle(f'{self.col2title[col]}: {self.run_summary}')
        self.fig.supylabel(self.col2units[col])

        per_key_arr = []

        # per docker violin plot
        self.axes[0,0].ticklabel_format(style='plain')
        self.axes[0,0].yaxis.grid(True)
        for key in self.keys:
            if agg:
                tmp = self.df[self.get_key() == key][col].values
            else:
                tmp = self.df[self.get_key() == key][col].diff().dropna().values
            per_key_arr.append(tmp)
            #all_arr = np.concatenate((all_arr, tmp), axis=0)

        #self.axes[0,0].set_xticks([x + 1 for x in range(len(self.keys))])
        labels = [ '{}{}'.format( ' ', k) for i, k in enumerate(self.keys)]
        #self.axes[0,0].set_xticklabels(labels)
        legends = self.axes[0,0].violinplot(dataset=per_key_arr, showmedians=True)
        #text = ""
        #for key, nodes in self.key2nodes.items():
        #    text += f'{key} {", ".join(nodes)}\n'
        #self.axes[0,0].text(0.675, 0.985, text, transform=self.axes[0,0].transAxes,
        #        fontsize=7, verticalalignment='top')

        # consolidated  violin plot
        self.axes[1,0].ticklabel_format(style='plain')
        self.axes[1,0].yaxis.grid(True)
        self.axes[1,0].set_xlabel('All Containers')
        self.axes[1,0].violinplot(self.df[col], showmedians=True)
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
        #self.axes[0,1].legend(legends, self.keys, scatterpoints=1,
         #               loc='upper left', ncol=3,
          #              fontsize=8)

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
        plt.savefig(f'{self.oprefix}-col-panel-{col}.pdf')
        #plt.show()

    # build the key2nodes: useful when $container_size$ > 1
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

    # export the df if needed
    def get_df(self):
        return self.df

    # build indices or cluster plots
    def build_cluster_index(self, grp):
        lst = self.df[grp].unique()
        self.grp2idx =  { val : i for i, val in enumerate(lst)}
        self.idx2grp =  { i : val for i, val in enumerate(lst)}
        self.df[f'{grp}_idx'] = self.df[grp].map(lambda x: self.grp2idx[x])

    # plot the cluster panel
    def cluster_plot_helper(self, grp, cols):
        self.build_cluster_index(grp)
        kmeans = KMeans(n_clusters=10, n_init='auto')

        groups = self.df[grp].unique()
        groups.sort()
        xpdf = pd.DataFrame()
        for g in groups:
            X =self.df.loc[self.df[grp] == g][cols]
            Xflat = X.values.flatten()
            xpdf[g] = Xflat
            labels = kmeans.fit_predict(X)
            #TODO: plot better. it is not very interpretable now
            self.axes[0,1].scatter(x=range(0, len(labels)), y=labels, marker='.')
            #self.axes[0,1].scatter(X.iloc[:, 0], X.iloc[:, 1], c=labels,  cmap='plasma')
        self.axes[0,1].set_xlabel('Time')
        #axis.set_yticks([x  for x in range(len(groups))])
        self.axes[0,1].set_yticks(range(len(groups)))
        labels = ['{}{}'.format( ' ', k) for i, k in enumerate(self.keys)]
        self.axes[0,1].set_yticklabels(labels)

        labels = kmeans.fit_predict(xpdf)
        self.axes[1,1].scatter(xpdf.iloc[:, 0], xpdf.iloc[:, 2], c=labels,  cmap='plasma')

    # plot the comparison panel
    def plot_compare_panel(self):
        self.set_panel_size(2, 3)
        self.fig.suptitle(f'{self.run_summary}')
        k = 0
        for i in [0,1]:
            for j in [0,1,2]:
                col = self.to_compare[k]
                #self.axes[i,j].ticklabel_format(style='plain')
                self.axes[i,j].yaxis.grid(True)
                pc = self.axes[i,j].violinplot(self.df[col], showmedians=True)
                self.axes[i,j].set_ylabel(self.col2units[col])
                self.axes[i,j].set_title(self.col2title[col])
                #for p in pc['bodies']:
                #    p.set_facecolor('green')
                #    p.set_edgecolor('k')
                #    p.set_alpha(0.5)
                k += 1
        plt.savefig(f'{self.oprefix}-compare.pdf', format="pdf", bbox_inches="tight")
        #plt.show()

    def phase_plots_helper(self, grp, col):
        pass

    # build the network from json
    def read_network(self):
        with open(self.json_fname) as f:
            js_graph = json.load(f)
            for src in js_graph['nodes'].keys():
                for dst  in js_graph['nodes'][src]['static_nodes']:
                    self.G.add_edge(src, dst)

    # plot the network and degree histogram
    def plot_network(self):
        self.set_panel_size(1, 2)
        self.fig.suptitle(f'Network & Degree Distribution:  {self.run_summary}')
        nx.draw(self.G, ax=self.axes[0], pos=nx.kamada_kawai_layout(self.G), with_labels=True)

        degree_sequence = sorted((d for n, d in self.G.degree()), reverse=True)
        w = np.ones(len(degree_sequence))/len(degree_sequence)
        hist, bin_edges = np.histogram(degree_sequence, weights=w, density=False)
        width = (bin_edges[1] - bin_edges[0])
        self.axes[1].bar(x=bin_edges[:-1], height=hist, align='center',
                width=width, edgecolor='k', facecolor='green', alpha=0.5)
        self.axes[1].set_xticks(range(max(degree_sequence)+1))
        self.axes[1].set_title("Normalised degree histogram")
        self.axes[1].set_xlabel("Degree")
        self.axes[1].set_ylabel("% of Nodes")
        plt.savefig(f'{self.oprefix}-network.pdf', format="pdf", bbox_inches="tight")
        #plt.show()

    # plot the degree col panel
    def deg_col_panel_helper(self, col):
        self.set_panel_size(1, 2, shareY=True)
        self.fig.suptitle(f'Conditional/Total Normalised Histograms for {self.col2title[col]} :  {self.run_summary}')
        self.fig.supylabel(self.col2units[col])
        degree_sequence = sorted((d for n, d in self.G.degree()), reverse=True)
        x, y = np.unique(degree_sequence, return_counts=True)
        by_degree = [[] for i in range(x[-1]+1)]
        for node, degree in self.G.degree():
            curr = self.df[self.df.NodeName == node][col].values
            if len(by_degree[degree]) == 0 :
                by_degree[degree]=self.df[self.df.NodeName == node][col].values
            else :
                np.append(by_degree[degree], self.df[self.df.NodeName == node][col].values)
        legends = []
        for d in by_degree:
            if len(d) == 0:
                continue
            w = np.ones(len(d))/len(d)
            hist, bin_edges = np.histogram(d, weights=w, density=False)
            width = (bin_edges[1] - bin_edges[0])
            legends.append(self.axes[0].bar(x=bin_edges[:-1], height=hist, align='center',
                width=width,  edgecolor='k', alpha=0.75))
        self.axes[0].legend(legends, x, scatterpoints=1,
                        loc='upper left', ncol=5,
                        fontsize=8)
        self.axes[0].set_title("Conditional Histogram (degree)")
        d = self.df[col]
        w = np.ones(len(d))/len(d)
        hist, bin_edges = np.histogram(d, weights=w, density=False)
        width = (bin_edges[1] - bin_edges[0])
        self.axes[1].bar(x=bin_edges[:-1], height=hist, align='center',
                width=width, edgecolor='k', facecolor='green', alpha=0.5)
        self.axes[1].set_title("Total Histogram")
        plt.savefig(f'{self.oprefix}-deg-col-panel-{col}.pdf')
        #plt.show()


# handle docker stats
class DStats(Plots, metaclass=Singleton):
    def __init__(self, log_dir, oprefix, jf, to_plot, cfile):
        Plots.__init__(self, log_dir, oprefix, jf, to_plot, cfile)
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
                            "CPIDS"          : "Docker PIDS"
                            }
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
                            "CPIDS"          : "PIDS"
                            }
        self.cols = ["CPUPerc", "MemUse","NetRecv", "NetSent", "BlockR", "BlockW"]

    # remove the formatting artefacts
    def pre_process(self):
        if not path_ok(Path(self.dstats_fname)):
            sys.exit(0)
        self.set_summary()
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
            self.df[size] = self.df[size].map(lambda x:h2b.convert(x.strip())/(1024*1024)) # MiB
        for size in ["NetRecv", "NetSent"]:
            self.df[size] = self.df[size].map(lambda x:h2b.convert(x.strip())/(1024*1024)) # MiB
        for size in ["BlockR", "BlockW"]:
            self.df[size] = self.df[size].map(lambda x:h2b.convert(x.strip())/(1024*1024)) # MiB
        self.df['Key'] = self.df['ContainerName'].map(lambda x: x.split("--")[0])
        self.build_key2nodes()
        self.df['NodeName'] = self.df['Key'].map(lambda x: self.key2nodes[x][0])
        self.set_keys()

    # build df from csv
    def process_data(self):
        log.info(f'processing {self.dstats_fname}...')
        self.pre_process()
        self.df = pd.read_csv(self.dstats_fname, header=0,  comment='#',
                            skipinitialspace = True, delimiter='/',
                            usecols=["ContainerID", "ContainerName",
                                    "CPUPerc", "MemUse", "MemTotal", "MemPerc",
                                    "NetRecv", "NetSent", "BlockR","BlockW",  "CPIDS"])
        self.post_process()
        self.remove_incomplete_samples(grp='Key', err='--')
        self.df.to_csv(f'{self.oprefix}-cleaned.csv', sep='/')


class HostProc(Plots, metaclass=Singleton):
    def __init__(self, log_dir, oprefix, jf, to_plot, cfile):
        Plots.__init__(self, log_dir, oprefix, jf, to_plot, cfile)
        self.fname = f'{log_dir}/host-proc-data/docker-proc.out'
        self.kinspect_fname = f'{log_dir}/host-proc-data/docker-kinspect.out'
        self.col2title = {  'CPUPerc'   : 'CPU Utilisation',
                            'VmPeak'    : 'Peak Virtual Memory Usage',
                            'MemUse'    : 'Peak Virtual Memory Usage',
                            'VmSize'    : 'Current Virtual Memory Usage',
                            'VmRSS'     : 'Peak Physical Memory Usage',
                            'VmData'    : 'Size of Data Segment',
                            'VmStk'     : 'Size of Stack Segment',
                            'NetRecv'   : 'Network1: Received Bytes',
                            'NetRecvPkts' : 'Network1: Received Packets',
                            'NetSent'   : 'Network1: Transmitted Bytes',
                            'NetSentPkts' : 'Network1: Transmitted Packets',
                            'NetRX'     : 'Network2: Received Bytes',
                            'NetWX'     : 'Network2: Transmitted Bytes',
                            'InOctets'  : 'Network3: InOctets',
                            'OutOctets' : 'Network3: OutOctets',
                            'BlockR'    : 'Block Reads',
                            'BlockW'    : 'Block Writes'
                        }
        self.col2units = {  'CPUPerc'   : '%',
                            'VmPeak'    : 'MiB',
                            'MemUse'    : 'MiB',
                            'VmSize'    : 'MiB',
                            'VmRSS'     : 'MiB',
                            'VmData'    : 'MiB',
                            'VmStk'     : 'MiB',
                            'NetRecv'   : 'MiB',
                            'NetRecvPkts' : 'Packets',
                            'NetSent'   : 'MiB',
                            'NetSentPkts' : 'Packets',
                            'NetRX'   : 'MiB',
                            'NetWX'   : 'MiB',
                            'InOctets'  : 'MiB',
                            'OutOctets' : 'MiB',
                            'BlockR'    : 'MiB',
                            'BlockW'    : 'MiB'
                        }
        self.cols = ['CPUPerc', 'VmPeak', 'MemUse', 'VmSize', 'VmRSS', 'VmData', 'VmStk',
                            'RxBytes', 'RxPackets', 'TxBytes', 'TxPackets', 'NetRecv', 'NetSent',
                            'InOctets', 'OutOctets', 'BlockR', 'BlockW']

    def process_data(self):
        if not path_ok(Path(self.fname)):
            sys.exit(0)
        self.set_summary()
        self.df = pd.read_csv(self.fname, header=0,  comment='#',
                skipinitialspace = True, delimiter=r"\s+",
                usecols= ['EpochId', 'PID', 'TimeStamp',
                    'ContainerName', 'ContainerID', 'NodeName',
                    'VmPeak', 'VmPeakUnit', 'VmSize', 'VmSizeUnit',
                    'VmRSS', 'VmRSSUnit', 'VmData','VmDataUnit', 'VmStk', 'VmStkUnit',
                    'HostVIF', 'NetSent', 'NetSentPkts', 'NetRecv', 'NetRecvPkts',
                    #'VETH', 'InOctets', 'OutOctets',
                    #'DockerVIF', 'NetRecv', 'NetSent',
                    #'VETH',  'InOctets', 'OutOctets',
                    'BlockR', 'BlockW',
                    'CPUPerc'])
        self.post_process()
        self.remove_incomplete_samples(grp='Key')
        self.df.to_csv(f'{self.oprefix}-cleaned.csv', sep='/')

    # normalise the units
    def post_process(self):
        #h2b = Human2BytesConverter()
        for size in ['VmPeak', 'VmSize','VmRSS', 'VmData','VmStk']:
            self.df[size] = self.df[size].map(lambda x: x/1024) # MiBs
        for size in ['NetRecv','NetSent']:
            self.df[size] = self.df[size].map(lambda x: x/(1024*1024)) # MiBs
        for size in ['BlockR', 'BlockW']:
            self.df[size] = self.df[size].map(lambda x: x/(1024*1024)) # MiBs
        #self.df['Key'] = self.df['ContainerName'].map(lambda x: x.split("--")[0])
        self.df['Key'] = self.df['NodeName']#.map(lambda x: x.split("--")[0])
        self.df['MemUse'] = self.df['VmPeak']
        self.build_key2nodes()
        #self.df.rename(columns={'NodeName': 'Key'}, inplace=True)
        self.set_keys()
        self.df.fillna(0)

    # not very helpful plots atm
    def plot_clusters(self, grp, agg, axes):
        self.cluster_plot_helper(col=['CPUPerc', 'VmPeak', 'VmRSS', 'MemUse', 'VmData'], grp=grp, axes=axes)


# sanity check config file
def _config_file_callback(ctx: typer.Context, param: typer.CallbackParam, cfile: str):
    if cfile:
        typer.echo(f"Loading config file: {os.path.basename(cfile)}")
        ctx.default_map = ctx.default_map or {}  # Init the default map
        try:
            with open(cfile, 'r') as f:  # Load config file
                conf = json.load(f)
                if "plotting" not in conf:
                    log.error(f"No plotting is requested in {cfile}. Skipping plotting.")
                    sys.exit(0)
                # Merge config and default_map
                if ctx.command.name in conf["plotting"]:
                    ctx.default_map.update(conf["plotting"][ctx.command.name])
                else:
                    if "hproc" in conf["plotting"]:
                        ctx.default_map.update(conf["plotting"]["hproc"])
                    else:
                        log.info(f"No dstats/host-proc params in config. Sticking to defaults")
            #ctx.default_map.update(conf["plotting"])  # Merge config and default_map
        except Exception as ex:
            raise typer.BadParameter(str(ex))
    return cfile


# instantiate typer and set the commands
app = typer.Typer()

# common cmd processor/plotter
def cmd_helper(metric_infra, to_plot, agg, to_compare):
    metric_infra.process_data()
    # always plot the compare plots; rest on demand
    metric_infra.set_compare(to_compare)
    metric_infra.plot_compare_panel()
    log.info(f'to_plot : {to_plot}')
    if "Network" in to_plot and to_plot["Network"]:
        metric_infra.read_network()
        metric_infra.plot_network()
    if "ColPanel" in to_plot and to_plot["ColPanel"]:
        metric_infra.plot_col_panels(agg)
    if "ValueCluster" in to_plot and to_plot["ValueCluster"]:
        # TODO: find interpretable cluster plot
        metric_infra.build_cluster_index('ContainerID')
    if "DegColPanel" in to_plot:
        metric_infra.plot_deg_col_panels()
    if "SettlingTime" in to_plot and to_plot["SettlingTime"]:
        metric_infra.compute_msg_settling_times()
        metric_infra.plot_msg_settling_times()
    #if "Compare" in to_plot and to_plot["Compare"]:


# process / plot docker-procfs.out
@app.command()
def host_proc(ctx: typer.Context, log_dir: Path, # <- mandatory path
            out_prefix: str = typer.Option("output", help="Specify the prefix for the plot pdfs"),
            aggregate: bool = typer.Option(True, help="Specify whether to aggregate"),
            config_file: str = typer.Option("", callback=_config_file_callback, is_eager=True,
                help="Set the input config file (JSON)")):
    if not path_ok(log_dir, True):
        sys.exit(0)

    to_plot = ctx.default_map["to_plot"] if ctx.default_map and "to_plot" in ctx.default_map else []
    jf = f'{os.path.abspath(log_dir)}/config/topology_generated/network_data.json'
    if  os.path.exists("plots"):
        os.system('rm -rf plots')
    os.makedirs("plots")
    host_proc = HostProc(log_dir, f'plots/{out_prefix}-host-proc', jf, to_plot, config_file)
    cmd_helper(host_proc, to_plot, agg=aggregate,
            to_compare=["CPUPerc", "MemUse", "NetRecv", "NetSent", "BlockR", "BlockW"])
    log.info(f'Done: {log_dir}')


# process / plot docker-dstats.out
@app.command()
def dstats(ctx: typer.Context, log_dir: Path, # <- mandatory path
            out_prefix: str = typer.Option("output", help="Specify the prefix for the plot pdfs"),
            aggregate: bool = typer.Option(True, help="Specify whether to aggregate"),
            config_file: str = typer.Option("", callback=_config_file_callback, is_eager=True,
             help="Set the input config file (JSON)")):
    if not path_ok(log_dir, True):
        sys.exit(0)

    to_plot = ctx.default_map["to_plot"] if ctx.default_map and "to_plot" in ctx.default_map else []
    jf = f'{os.path.abspath(log_dir)}/config/topology_generated/network_data.json'
    if  os.path.exists("plots"):
        os.system('rm -rf plots')
    os.makedirs("plots")
    dstats = DStats(log_dir, f'plots/{out_prefix}-dstats', jf, to_plot, config_file)
    cmd_helper(dstats, to_plot, agg=aggregate,
            to_compare=["CPUPerc", "MemUse", "NetRecv", "NetSent", "BlockR", "BlockW"])
    log.info(f'Done: {log_dir}')


if __name__ == "__main__":
    app()
