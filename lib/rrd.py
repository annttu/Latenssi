# encoding: utf-8

import rrdtool
import logging
from lib import config
import os

logger = logging.getLogger("RRD")

class RRD(object):
    def __init__(self, name, title=None):
        self.name = name
        if not title:
            self.title = self.name
        else:
            self.title = title
        self.filename = os.path.join(config.data_dir, '%s.rrd' % self.name)
        self.graphfile = os.path.join(config.graph_dir, '%s.png' % self.name)
        self.create()

    def create(self):
        if os.path.exists(self.filename):
            return
        rrdtool.create(self.filename, '--step', '5', '--start', '0',
                       'DS:ping:GAUGE:5:0:30000',
                       'DS:miss:GAUGE:5:0:5',
                       'RRA:AVERAGE:0.5:1:535680', # Save one month data with 5 sec resolution
                       'RRA:AVERAGE:0.5:12:525600', # Save one year data with 60 sec resolution
                       'RRA:MAX:0.5:1:535680',
                       'RRA:MAX:0.5:12:525600',
                       'RRA:MIN:0.5:1:535680',
                       'RRA:MIN:0.5:12:525600',
                       )

    def update(self, ping, miss=0, time="N"):
        rrdtool.update(self.filename, '%s:%f:%f' % (time, ping, miss))


    def graph(self, graphfile=None):
        if not graphfile:
            graphfile = self.graphfile
        logger.debug("Graphing %s to file %s" % (self.filename, graphfile))
        opts = [graphfile,
                '-t', str(self.name),
                '-w', str(config.graph_width),
                '-h', str(config.graph_height),
                'DEF:ping=%s:ping:AVERAGE' % self.filename,
                'DEF:ping_max=%s:ping:MAX' % self.filename,
                'DEF:ping_min=%s:ping:MIN' % self.filename,
                'DEF:ping_longterm=%s:ping:AVERAGE:step=360' % self.filename,
                'DEF:miss=%s:miss:AVERAGE' % self.filename,
                'DEF:miss_max=%s:miss:MAX' % self.filename,
                'DEF:miss_min=%s:miss:MIN' % self.filename,
                'DEF:miss_longterm=%s:miss:AVERAGE:step=360' % self.filename,
                'CDEF:loss=miss,20,*',
                'CDEF:loss_longterm=miss_longterm,20,*',
                'AREA:ping_max#50FFFF',
                'AREA:ping_min#FFFFFF',
                'LINE1:ping_longterm#9090f0',
                'LINE1:ping#0000FF:Ping',
                'GPRINT:ping:AVERAGE:\t\tAvg\: %6.2lf ms\t',
                'GPRINT:ping:MIN:\tMin\: %6.2lf ms\t',
                'GPRINT:ping:MAX:\tMax\: %6.2lf ms\\n',
                'LINE1:loss_longterm#F09090',
                'LINE1:loss#FF3030:Loss',
                'GPRINT:loss:AVERAGE:\t\tAvg\: %6.0lf %%\t',
                'GPRINT:loss:MIN:\tMin\: %6.2lf %%\t',
                'GPRINT:loss:MAX:\tMax\: %6.2lf %%\\n',
                ]
        rrdtool.graph(*opts)
        logger.debug("%s updated" % graphfile)
