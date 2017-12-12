# encoding: utf-8
import time

from lib import config, probe as lib_probe, rrd, sanitize

import os
from jinja2 import Environment, FileSystemLoader
import logging
from bottle import Bottle

webapp = Bottle()

logger = logging.getLogger("web")

class LatenssiTemplateGenerator(object):
    def __init__(self):
        self.env = None

    def _create_env(self):
        if not self.env:
            self.env = Environment(loader=FileSystemLoader(os.path.join(
                                    os.path.dirname(__file__),'../templates/')))

    def generate(self, filename, template, opts={}):
        filename = os.path.join(config.html_dir, filename)
        f = open(filename, 'wb')
        f.write(self.output(template, opts))
        f.close()

    def output(self, template, opts):
        opts['config'] = config
        self._create_env()
        logger.debug("Options: %s" % (opts,))
        tmpl = self.env.get_template(template)
        return tmpl.render(**opts).encode("utf-8")

webgenerator = LatenssiTemplateGenerator()


def generate_probename(name):
    return utils.sanitize(name)


class WebPage(object):
    def __init__(self, name, title):
        self.name = name
        self.title = title

    def get_path(self, interval=None):
        prefix="%s" % config.relative_path
        if self.name not in ['index']:
            prefix = "%s/%s" % (prefix, self.name)
        if interval and interval != config.default_interval:
            interval = utils.sanitize(interval)
            return "%s/%s" % (prefix, interval)
        return "/%s" % prefix.lstrip("/")

    def generate_intervals(self, current=None):
        ret = []
        for interval in config.intervals.keys():
            keys = { 'active': False,
                     'link': self.get_path(interval),
                     'name': interval
                   }
            if interval == current:
                keys['active'] = True
            ret.append(keys)
        return sorted(ret, key=lambda x: config.intervals[x['name']])


class ProbeWeb(WebPage):
    def __init__(self, probe):
        super(ProbeWeb, self).__init__(generate_probename(probe.name), probe.title)
        self.probe = probe

    def get_path(self, interval=None):
        prefix="%s" % config.relative_path
        if interval and interval != config.default_interval:
            interval = utils.sanitize(interval)
            return "/%s/probes/%s/%s" % (prefix.lstrip("/"), self.name, interval)
        return "/%s/probes/%s" % (prefix.lstrip("/"), self.name)

    def get_graphs(self):
        return self.probe.graphs()

    def get_data_names(self, interval=None):
        if not interval:
            interval = config.default_interval
        graphs = []
        for graph in self.get_graphs():
            graphs.append({'id': graph, 'name': graph})
        return graphs

    def get_graph_urls(self, interval=None):
        if not interval:
            interval = config.default_interval
        graphs = []
        for graph in self.get_graphs():
            if config.probe_addresses:
                for probe_address in config.probe_addresses:
                    img = '/'.join(['http:/', probe_address, 'graph/%s/?interval=%s&name=%s' % (graph, interval, self.name)])
                    graphs.append({'img': img, 'name': graph, 'title': probe_address.split("/")[0]})
            else:
                img = os.path.join([config.relative_path, 'graph/%s/?interval=%s&name=%s' % (graph, interval, self.name)])
        return graphs

    def get_index_graph(self, interval=None):
        return "%s&width=800&height=400" % self.get_graph_urls(interval)[0]['img']


class ProbeCache(object):
    def __init__(self):
        self._cache = {}
        self._last_updated = None
        self.update()

    def update(self):
        if self._cache and config.last_updated < self._last_updated:
            return
        self._cache = {}
        for probe in lib_probe.probes:
            p = ProbeWeb(probe)
            self._cache[p.name] = p
        self._last_updated = time.time()

    def get(self, name):
        self.update()
        if name in self._cache:
            return self._cache[name]
        return None

    def get_all(self):
        self.update()
        return self._cache

ProbeCache = ProbeCache()
