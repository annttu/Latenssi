#!/usr/bin/env python
# encoding: utf-8

from lib.rrd import RRD
from lib import config, utils
from lib.probe import register_multi_probe
from lib.multi_probes import multi_probe

import subprocess
import logging
import re
import time
import os.path

# kapsi.fi : xmt/rcv/%loss = 5/5/0%, min/avg/max = 0.00/0.91/1.40

fping_success = re.compile("^(?P<dest>[\w\d:\.-]+)\s+: xmt/rcv/%loss = (?P<xmt>\d+)/(?P<rcv>\d+)/(?P<loss>\d+)%, min/avg/max = (?P<min>\d+.\d+)/(?P<avg>\d+.\d+)/(?P<max>\d+.\d+)$")
fping_dups = re.compile("^(?P<dest>[\w\d:\.-]+)\s+: xmt/rcv/%return = (?P<xmt>\d+)/(?P<rcv>\d+)/(?P<return>\d+)%, min/avg/max = (?P<min>\d+.\d+)/(?P<avg>\d+.\d+)/(?P<max>\d+.\d+)$")
fping_failed = re.compile("^(?P<dest>[\w\d:\.-]+)\s+: xmt/rcv/%loss = (?P<xmt>\d+)/(?P<rcv>\d+)/(?P<loss>\d+)%$")

logger = logging.getLogger("multiping")


class MultiPing(multi_probe.MultiProbe):
    def __init__(self, protocol=4):
        self.protocol = protocol
        self._name = 'Ping%s' % self.protocol
        super(MultiPing, self).__init__()
        self.p = None
        self._count = 5

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
        target = "%s-%s" % (self._name.lower(), utils.sanitize(out['dest']))
        RRD.update(target, time=out['timestamp'], ping=float(out['avg']),
                   miss=(int(out['xmt']) - int(out['rcv'])))

    def _add_host_local(self, target, name):
        name = "%s-%s" % (self._name.lower(), utils.sanitize(target))
        RRD.register(name, '%s %s' % (name, target))

    def main(self):
        logger.debug("Starting fping to %s" % ','.join(self.targets.keys()))
        if self.protocol == 6:
            ping = config.fping6
        else:
            ping = config.fping
        if not os.path.isfile(ping):
            logger.error("fping program %s missing, cannot start probe" % ping)
            return

        command = [ping, '-Q%s' % self._count, '-c60']  # Run 60sec reporting per 5 sec
        logger.debug("Command: %s" % (' '.join(command)))
        self.p = subprocess.Popen(command, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, stdin=subprocess.PIPE, encoding="utf-8")
        # Send hosts
        logger.debug("Sending hosts %s", '\n'.join(self.targets.keys()))
        self.p.stdin.write('\n'.join(self.targets.keys()))
        self.p.stdin.close()
        while not self._stop:
            try:
                if self.p.poll() is not None:
                    logger.error("%s terminated unexpectedly", ping)
                    break
                line = self.p.stderr.readline()
                logger.debug("line: %s", line)
                if not line:
                    logger.debug("Didn't get line")
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
            logger.error("Terminating process %s" % ping)
            self.p.terminate()
            stdout = ""
            stderr = ""
        else:
            stderr = self.p.stderr.readlines()
            stdout = self.p.stdout.readlines()
        if self.p.returncode != 0:
            if self.p.returncode <= 2:
                logger.info("Some of the hosts are unreachable")
            else:
                logger.error("Got non zero return value '%s' from fping to %s" % (self.p.returncode, self.targets.keys(),))
                logger.debug('\n'.join(stderr))
                logger.error('\n'.join(stdout))
                logger.error("Suspending for 5 seconds")
                time.sleep(5)
            return


register_multi_probe('multiping', MultiPing)
