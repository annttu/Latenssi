# encoding: utf-8

data_dir = "rrd_data"
graph_dir = "/var/www/latency/img"
html_dir = "/var/www/latency"
relative_path = "/latency/"

dynamic_graphs = True

graph_width = 1100
graph_height = 500

fping = "/usr/bin/fping"
fping6 = "/usr/bin/fping6"

hosts = {}
probes = {}


def load_config(config):
    global_vars = globals()
    for k, v in config.items():
        if k.startswith('_'):
            continue
        global_vars[k] = v
