# encoding: utf-8

import time

last_updated = time.time()

data_dir = "rrd_data"
graph_dir = "/var/www/latency/img"
html_dir = "/var/www/latency"
relative_path = "/latency/"

graph_width = 1100
graph_height = 500

upper_limit = 1000
lower_limit = 0

fping = "/usr/bin/fping"
fping6 = "/usr/bin/fping6"

mtr = "/usr/bin/mtr"

# Web application config

bind_address = 'localhost'
bind_port = 8080

# Graph intervals
intervals = {
   'hour': 3600,
   '2hour': 7200,
   '8hour': 8 * 3600,
   'day': 24 * 3600,
   'week': 7*24*3600,
   'month': 30*24*3600,
   'year': 365*24*3600
}

default_interval = 'day'

devel = False

# How often flush collected data to rrdfile
sync_interval = 59

hosts = {}
probes = {}
remotes = {}

api_keys = []

# Other probes
probe_addresses = []

# Address to master server and api key for it
master = None
master_api_key = None
