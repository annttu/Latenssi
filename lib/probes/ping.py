#!/usr/bin/env python
# encoding: utf-8

from lib.rrd import RRD
from lib import config
from lib.probe import register_probe
from lib.probes import probe

import subprocess
import logging
import re
import time

# kapsi.fi : xmt/rcv/%loss = 5/5/0%, min/avg/max = 0.00/0.91/1.40

fping_success = re.compile("^(?P<dest>[\w\d:\.-]+) : xmt/rcv/%loss = (?P<xmt>\d+)/(?P<rcv>\d+)/(?P<loss>\d+)%, min/avg/max = (?P<min>\d+.\d+)/(?P<avg>\d+.\d+)/(?P<max>\d+.\d+)$")
fping_dups = re.compile("^(?P<dest>[\w\d:\.-]+) : xmt/rcv/%return = (?P<xmt>\d+)/(?P<rcv>\d+)/(?P<return>\d+)%, min/avg/max = (?P<min>\d+.\d+)/(?P<avg>\d+.\d+)/(?P<max>\d+.\d+)$")
fping_failed = re.compile("^(?P<dest>[\w\d:\.-]+) : xmt/rcv/%loss = (?P<xmt>\d+)/(?P<rcv>\d+)/(?P<loss>\d+)%$")

logger = logging.getLogger("ping")

class Ping(probe.Probe):
    def __init__(self, target, protocol=4, name=None):
        self.protocol = protocol
        self._name = 'Ping%s' % self.protocol
        super(Ping, self).__init__(target, name=name)
        self.p = None
        self._count = 5
        RRD.register(self.name, '%s %s' % (self._name, self.target))

    def _kill(self):
        if self.p and self.p.returncode is not None:
            self.p.terminate()
            self.p.stdout.close()
            self.p.stderr.close()
            self.p = None

    def handle_line(self, line):
        if line.startswith('[') or not line:
            return
        out = None
        m = fping_success.match(line.strip())
        if m:
            out = m.groupdict()
        if not out:
            m = fping_dups.match(line.strip())
            if m:
                out = m.groupdict()
                out['loss'] = 0.0
                out['rvc'] = out['xmt']
        if not out:
            m = fping_failed.match(line.strip())
            if m:
                out = m.groupdict()
                out['avg'] = 0.0
        if not out:
            logger.error("Invalid line %s" % line)
            return
        out['timestamp'] = int(time.time() - 2.5) # timestamp at center of metering time
        if int(out['rcv']) > self._count:
            logger.debug("Totals %s" % (out, ))
            return
        logger.debug(out)
        RRD.update(self.name, time=out['timestamp'], ping=float(out['avg']), miss=( int(out['xmt']) - int(out['rcv'])))

    def main(self):
        logger.debug("Starting fping to %s" % self.target)
        if self.protocol == 6:
            ping = config.fping6
        else:
            ping = config.fping
        self.p = subprocess.Popen([ping, '-Q%s' % self._count,'-c60', self.target],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE) # Run 60sec reporting per 5 sec
        while not self._stop:
            try:
                line = self.p.stderr.readline()
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
            logger.error("Got non zero return value from fping to %s" % (self.target,))
            logger.error("Suspending for 5 seconds")
            time.sleep(5)
            return


register_probe('ping',Ping)
