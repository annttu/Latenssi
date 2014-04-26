#!/usr/bin/env python
# encoding: utf-8

from lib.rrd import RRD
from lib import config, utils
from lib.probe import register_probe
from lib.probes import probe

import subprocess
import logging
import re
import time

logger = logging.getLogger("mtr")

class Hop(object):
    def __init__(self, address, index, parent):
        self.hop_id = index
        self.parent = parent
        self.address = address
        self.index = index
        self.name = "%s-%s-%s-%s" % (self.parent._name, utils.sanitize(self.parent.target), index, utils.sanitize(self.address))
        self.cache = []
        self._loss = 0
        self.latest = None

    def update(self, ping):
        if ping is None:
            self._loss+=1
            return
        self.cache.append(float(ping))
        if not self.latest:
            self.latest = time.time()
        elif self.latest < (time.time() - self.parent.interval  + 0.5):
            logger.info("Flushing points %s (%s, %s), %s second average" % (self.name, self.avg(), self.loss(), (time.time() - self.latest)))
            RRD.update(self.name, self.avg(), self.loss(), time=int(time.time()))
            self.latest = time.time()
            self.cache = []
            self._loss = 0

    def loss(self):
        return self._loss

    def avg(self):
        if not self.cache:
            return None
        return float(sum(self.cache)) / float(len(self.cache))


class MTR(probe.Probe):
    def __init__(self, target, protocol=4, interval=5):
        self.protocol = protocol
        self.interval = int(interval)
        self._name = 'MTR%s' % self.protocol
        super(MTR, self).__init__(target)
        self.p = None
        self._count = 5
        self.opts = [config.mtr]
        if self.protocol == 6:
            self.opts.append('-6')
        else:
            self.opts.append('-4')
        self.opts.append('-n')
        self.opts.append('-l')
        #self.opts.append('--interval')
        #self.opts.append('%s' % self.interval)
        self.opts.append('-c')
        self.opts.append('360')
        self.opts.append(str(self.target))
        self.hops = {}
        self.latest_index = 0

    def graphs(self):
        return RRD.search('%s-%s' % (self._name, utils.sanitize(self.target)))

    def _kill(self):
        if self.p and self.p.returncode is not None:
            self.p.terminate()
            self.p.stdout.close()
            self.p.stderr.close()
            self.p = None

    def handle_missing(self, index):
        index = int(index)
        if index == self.latest_index or index == (self.latest_index + 1):
            self.latest_index = index
            return
        elif index < self.latest_index:
            for i, hop in self.hops.items():
                if int(i) > self.latest_index:
                    logger.info("Packetloss for node %s, (%s after %s)" % (hop.index, index, self.latest_index))
                    hop.update(None)
        else:
            for i, hop in self.hops.items():
                i = int(i)
                if i > self.latest_index and i < index:
                    hop.update(None)
        self.latest_index = index

    def handle_line(self, line):
        if not line:
            return
        if line.startswith('h '):
            (crap, index, address) = line.split()
            index = int(index)
            logger.debug("New hop %s %s for target %s" % (index, address, self.target))
            if address not in self.hops:
                self.hops[str(index)] = Hop(address, index, self)
                RRD.register(self.hops[str(index)].name, '%s %s hop %s' % (self._name, self.target, address))
        elif line.startswith('p '):
            (crap, index, ping) = line.split()
            index = int(index)
            ping = float(ping) / 1000.0
            logger.debug("ping response %s ms for hop %s on target %s" % (ping, index, self.target))
            self.handle_missing(index)
            if str(index) in self.hops:
                self.hops[str(index)].update(ping)
            else:
                logger.error("Ping packet for unknown index %s" % index)
        else:
            logger.info("Unknown line %s" % line.strip())


    def run_proc(self, opts, stderr=False):
        logger.debug("Starting %s to %s" % (opts[0], self.target))
        self.p = subprocess.Popen(opts, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while not self._stop:
            try:
                if stderr:
                    line = self.p.stderr.readline()
                else:
                    line = self.p.stdout.readline()
                if not line:
                    if self.p.poll() is not None:
                        break
                    else:
                        continue
                self.handle_line(line.strip())
            except Exception as e:
                logger.exception(e)
                break
        if self._stop:
            return
        if self.p.poll() is None:
            self.p.terminate()
        stderr = self.p.stderr.readlines()
        if self.p.returncode != 0:
            logger.error("Got non zero return value from %s" % self._name)
            logger.error("Suspending for 5 seconds")
            t = time.time()
            while not self._stop:
                if t < (time.time() - 5):
                    break
                time.sleep(0.3)
            return

    def main(self):
        self.run_proc(self.opts, stderr=False)

register_probe('mtr',MTR)
