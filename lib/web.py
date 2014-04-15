# encoding: utf-8

from lib import config, probes

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
        self._create_env()
        logger.debug("Generating page %s" % filename)
        logger.debug("Options: %s" % (opts,))
        filename = os.path.join(config.html_dir, filename)
        f = open(filename, 'wb')
        tmpl = self.env.get_template(template)
        f.write(tmpl.render(**opts).encode("utf-8"))
        f.close()

webgenerator = LatenssiWeb()

def generate_pages():
    pages = []
    for probe in probes.probes:
        opts = {
            'host': {'name': probe.rrd.title,
                'probes': [
                 {
                    'img': os.path.join(config.relative_path, 'img/', os.path.basename(probe.rrd.graphfile)),
                    'name': str(probe.__class__.__name__)
                 },
                 ]
             }
        }
        filename = "%s.html" % probe.rrd.name.replace('.','_')
        webgenerator.generate(filename, 'host.html', opts)
        pages.append({'link': filename, 'name': probe.rrd.title, 'img': opts['host']['probes'][0]['img']})
    webgenerator.generate('index.html', 'index.html', {'pages': pages})
