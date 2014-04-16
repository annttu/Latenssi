# encoding: utf-8

import rrdtool
import logging
from lib import config
import os
from datetime import datetime

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
                       'RRA:LAST:0.0:1:535680', # Save one month data with 5 sec resolution
                       'RRA:LAST:0.0:1:535680', # Save one month data with 5 sec resolution
                       'RRA:AVERAGE:0.5:1:535680', # Save one month data with 5 sec resolution
                       'RRA:AVERAGE:0.5:12:525600', # Save one year data with 60 sec resolution
                       'RRA:AVERAGE:0.5:60:525600', # Save 5 years data with 5min resolution
                       'RRA:AVERAGE:0.5:360:525600', # Save 30 year data with 30min resolution
                       'RRA:MAX:0.5:1:535680', 
                       'RRA:MAX:0.5:12:525600',
                       'RRA:MIN:0.5:1:535680',
                       'RRA:MIN:0.5:12:525600',
                       )

    def update(self, ping, miss=0, time="N"):
        rrdtool.update(self.filename, '%s:%f:%f' % (time, ping, miss))


    def graph(self, graphfile=None, width=None, height=None, start=None, end=None):
        if not graphfile:
            graphfile = self.graphfile
        if not width:
            width = str(config.graph_width)
        else:
            width = str(int(width))
        if not height:
            height = str(config.graph_height)
        else:
            height = str(int(height))
        if start:
            start = str(int(start))
        if end:
            end = str(int(end))
        logger.debug("Graphing %s to file %s" % (self.filename, graphfile))
        opts = [graphfile,
                '-t', str(self.title),
                '-w', width,
                '-h', height,
                '-X', '0',
                '-v', 'ms']
        if start:
            opts += ['-s', start]
        if end:
            opts += ['-e', end]
        opts += [
                'DEF:ping=%s:ping:AVERAGE' % self.filename,
                'DEF:ping_max=%s:ping:MAX' % self.filename,
                'DEF:ping_min=%s:ping:MIN' % self.filename,
                'DEF:ping_shortterm_min=%s:ping:MIN:step=10' % self.filename,
                'DEF:ping_shortterm_max=%s:ping:MAX:step=10' % self.filename,
                'DEF:ping_midterm_min=%s:ping:MIN:step=60' % self.filename,
                'DEF:ping_midterm_max=%s:ping:MAX:step=60' % self.filename,
                'DEF:ping_longterm_min=%s:ping:MIN:step=360' % self.filename,
                'DEF:ping_longterm_max=%s:ping:MAX:step=360' % self.filename,
                'DEF:miss=%s:miss:AVERAGE' % self.filename,
                'DEF:miss_max=%s:miss:MAX' % self.filename,
                'DEF:miss_min=%s:miss:MIN' % self.filename,
                'CDEF:lost_1=miss,0.05,GE,1,0,IF',
                'CDEF:lost_2=miss,0.08,GE,1,0,IF',
                'CDEF:lost_3=miss,0.12,GE,1,0,IF',
                'CDEF:lost_4=miss,0.16,GE,1,0,IF',
                'CDEF:lost_5=miss,0.25,GE,1,0,IF',
                'AREA:ping_longterm_max#c0c0c0',
                'AREA:ping_longterm_min#FFFFFF',
                'AREA:ping_midterm_max#808080',
                'AREA:ping_midterm_min#FFFFFF',
                'AREA:ping_midterm_max#404040',
                'AREA:ping_midterm_min#FFFFFF',
                'AREA:ping_max#202020',
                'AREA:ping_min#FFFFFF',
                #'LINE1:ping_longterm#909090',
                #'LINE1:ping_midterm#606060',
                'LINE2:ping#7FFF00:Ping',
                'GPRINT:ping:AVERAGE:\t\tAvg\: %6.2lf ms\t',
                'GPRINT:ping:MIN:\tMin\: %6.2lf ms\t',
                'GPRINT:ping:MAX:\tMax\: %6.2lf ms\\n',
                #'AREA:loss#FF3030:"Loss":1:1',
                'TICK:lost_1#FF404060:1.0:Loss 1/5',
                'TICK:lost_2#FF606080:1.0:Loss 2/5',
                'TICK:lost_3#FF3030a0:1.0:Loss 3/5',
                'TICK:lost_4#FF3030c0:1.0:Loss 4/5',
                'TICK:lost_5#FF3030e0:1.0:Loss 5/5',
                #'GPRINT:loss:AVERAGE:\t\tAvg\: %6.0lf %%\t',
                #'GPRINT:loss:MIN:\tMin\: %6.2lf %%\t',
                #'GPRINT:loss:MAX:\tMax\: %6.2lf %%\\n',
                'COMMENT:\\n',
                'COMMENT:%s\\r' % datetime.now().strftime("%d.%m.%Y %H\:%M\:%S"),
                ]
        rrdtool.graph(*opts)
        logger.debug("%s updated" % graphfile)
