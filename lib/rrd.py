# encoding: utf-8

import rrdtool
import logging
from lib import config, utils
import os
from datetime import datetime
import time
from threading import Thread, Lock

logger = logging.getLogger("RRD")

ptime = time

class RRDFile(object):
    def __init__(self, name, title=None):
        self.name = name.replace('.','_')
        if title:
            self.title = title
        else:
            self.title = name
        self.filename = os.path.join(config.data_dir, '%s.rrd' % self.name)
        self.create()
        self.cache = []
        self._latest = 0

    def create(self):
        if os.path.exists(self.filename):
            return
        rrdtool.create(self.filename, '--step', '5', '--start', '%s' % (int(time.time()) - 60),
                       '--no-overwrite',
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
        if time == 'N':
            time = int(ptime.time())
        logger.debug("Adding datapoint %s,%s to %s @ %s" % (ping, miss, self.filename, time))
        self.cache.append((time, ping, miss))

    def sync(self):
        logger.debug("Syncing points to file %s" % self.filename)
        points = []
        for point in self.cache:
            if point[0] > self._latest:
                self._latest = int(point[0])
            elif point[0] == self._latest:
                # Duplicates not allowed
                logger.info("Ignoring duplicate point for time %s on %s" % (point[0], self.filename))
                continue
            if point[1] is None:
                points.append("%s:U:%f" % (int(point[0]), float(point[2])))
            else:
                points.append('%s:%f:%f' % (int(point[0]), point[1], point[2]))
        if len(points) == 0:
            logger.info("No points on cache for %s" % self.filename)
            return
        else:
            logger.debug("New points for %s: %s" % (self.filename, ', '.join(points)))
        try:
            #rrdtool.update(self.filename, *points)
            for point in points:
                logger.info("Updating point %s to %s" % (point, self.filename))
                rrdtool.update(self.filename, point)
            self.cache = []
        except Exception as e:
            logger.error("Cannot save points to file %s" % self.filename)
            logger.exception(e)
        if len(self.cache) > 500:
            # don't cache forever, drop from begin
            while len(self.cache) < 500:
                self.cache.pop(0)

    def graphfile(self, interval=None):
        if interval:
            return os.path.join(config.graph_dir, '%s-%s.png' % (self.name, interval))
        return os.path.join(config.graph_dir, '%s.png' % self.name)

    def graph(self, graphfile=None, width=None, height=None, start=None, end=None, interval=None):
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
        if interval:
            if not interval in config.intervals:
                raise RuntimeError("Unknown interval")
            if not end:
                end = str(int(time.time()))
            start = str(int(end) - config.intervals[interval])
            if not graphfile:
                graphfile = self.graphfile(interval=interval)
        if not graphfile:
            graphfile = self.graphfile()


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
        logger.debug("rrdtool graph %s" % ' \\\n'.join(["'%s'" % x for x in opts]))
        out = rrdtool.graph(*opts)
        logger.debug("%s updated" % graphfile)
        return out


class RRDManager(Thread):
    def __init__(self):
        Thread.__init__(self)
        self._stop = False
        self.rrds = {}
        self._lock = Lock()
        self._name_cache = {}

    def stop(self):
        self._stop = True
        self.sync()

    def register(self, name, title=None):
        name = utils.sanitize(name)
        if name not in self.rrds:
            self.rrds[name] = RRDFile(name, title=title)

    def update(self, name, ping, miss=0, time='N'):
        self.register(name)
        self.rrds[name].update(ping=ping, miss=miss, time=time)

    def search(self, prefix):
        return [o.rstrip('.rrd') for o in os.listdir(config.data_dir) if o.startswith(prefix)]

    def exists(self, name):
        if name not in self._name_cache:
            self._name_cache[name] = os.path.isfile(os.path.join(config.data_dir, '%s.rrd' % name))
        return self._name_cache[name]

    def graph(self, name, *args, **kwargs):
        """
        Graph rrd by name `name'
        """
        name = utils.sanitize(name)

        if not self.exists(name):
            raise RuntimeError("RRD by name %s not found" % name)

        if name not in self.rrds:
            self.rrds[name] = RRDFile(name)

        return self.rrds[name].graph(*args, **kwargs)

    def sync(self):
        for rrd in self.rrds.values():
            rrd.sync()

    def run(self):
        prev = time.time()
        while not self._stop:
            time.sleep(0.5)
            if (time.time() - config.sync_interval) > prev:
                prev = time.time()
                self.sync()

RRD = RRDManager()
