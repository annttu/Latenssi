# encoding: utf-8

from lib import config, probe as lib_probe, rrd

import os
from jinja2 import Environment, FileSystemLoader
import logging

logger = logging.getLogger("web")

class LatenssiWeb(object):
    def __init__(self):
        self.env = None

    def _create_env(self):
        if not self.env:
            self.env = Environment(loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), '../templates/')))

    def generate(self, filename, template, opts={}):
        opts['config'] = config
        self._create_env()
        logger.info("Generating page %s" % filename)
        logger.debug("Options: %s" % (opts,))
        filename = os.path.join(config.html_dir, filename)
        f = open(filename, 'wb')
        tmpl = self.env.get_template(template)
        f.write(tmpl.render(**opts).encode("utf-8"))
        f.close()

webgenerator = LatenssiWeb()

def generate_filename(name, interval=None):
    name = name.replace('.','_')
    if interval and interval != config.default_interval:
        interval = interval.replace('.','_')
        return "%s-%s.html" % (name, interval)
    return "%s.html" % name

def generate_intervals(name, current=None):
    ret = []
    for interval in config.intervals.keys():
        keys = {'active': False, 'link': generate_filename(name, interval), 'name': interval}
        if interval == current:
            keys['active'] = True
        ret.append(keys)
    return sorted(ret, key=lambda x: config.intervals[x['name']])

def generate_pages():
    for interval in config.intervals:
        pages = []
        for probe in lib_probe.probes:
            graphs = []
            for graph in probe.graphs():
                if not config.dynamic_graphs:
                    img = os.path.join(config.relative_path, 'img/', os.path.basename(rrd.RRD.get_graphfile(graph)))
                else:
                    img = os.path.join(config.relative_path, 'graph.fcgi?graph=%s&interval=%s&name=%s' % (graph, interval, probe.name))
                graphs.append({'img': img, 'name': graph})
            filename = generate_filename(probe.name, interval)
            opts = {
                'host': {'name': probe.title,
                    'probes': graphs,
                 },
                 'intervals': generate_intervals(probe.name, interval),
                 'index': generate_filename('index', interval),
            }
            if not graphs:
                continue
            webgenerator.generate(filename, 'host.html', opts)
            pages.append({'link': filename, 'name': probe.name ,'title': probe.title, 'img': "%s&width=800&height=400" % opts['host']['probes'][0]['img']})
        index_filename = generate_filename('index', interval)
        webgenerator.generate(index_filename, 'index.html', {'pages': pages, 'intervals': generate_intervals('index', interval)})
