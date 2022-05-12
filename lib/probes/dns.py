#!/usr/bin/env python
# encoding: utf-8

"""
DNS probe for latenssi
"""

from __future__ import absolute_import
import socket

from lib.rrd import RRD
from lib import config
from lib.probe import register_single_probe
from lib.probes import probe
from lib import utils

import subprocess



import logging
import dns.resolver
import time

logger = logging.getLogger("dns")


class Dns(probe.Probe):
    def __init__(self, target, method="A", query="a.fi", protocol="udp", interval=5, name=None):
        self.method = method
        self.query = query
        self.protocol = protocol
        self._interval = interval
        self.tcp = protocol.lower() == "tcp"
        self._probe_name = 'DNS'
        super(Dns, self).__init__(target, name=name)
        self.name = "%s-%s-%s-%s-%s" % (self._probe_name.lower(), utils.sanitize(self.target),
                                        self.method.upper(),
                                        utils.sanitize(self.query), protocol.lower())
        self._count = 3
        self._timeout = 5
        self.resolver = dns.resolver.Resolver()
        self.resolver.nameservers = [self.target]
        self.resolver.timeout = 5 # Set 5 second timeout
        self.resolver.lifetime = 5 # Set 5 second lifetime

    def _kill(self):
        return None

    def do_round(self):
        rtime = 0
        miss = 0

        # Set resolver address if address is name


        if self.target[-1].isalpha():
            address = []
            a = utils.get_ipv6_by_name(self.target)
            if a:
                address.append(a)
            a = utils.get_ipv4_by_name(self.target)
            address.append(a)
            if not address:
                logger.error("Cannot resolve address for server %s" % self.target)
                return
            self.resolver.nameservers = address

        measurement_time = int(time.time())
        for i in range(3):
            if self._stop:
                return
            try:
                x = time.time()
                self.resolver.query(self.query, self.method, tcp=self.tcp)
                y = time.time()
                rtime += (y-x)*1000.0
            except dns.exception.Timeout:
                miss += 1
                continue
            except dns.exception.DNSException:
                logging.error("Got NXDOMAIN from %s, suspending for a moment" % self.target)
                time.sleep(30)
            except Exception:
                logging.exception("Got unexpected error from %s" % self.target)
                time.sleep(30)
            time.sleep(self._interval)
        if self._count > miss:
            rtime = rtime / float(self._count - miss)
        else:
            rtime = 0.0
        logging.debug("%s, time: %s, miss: %s, time: %s" % (self.name, rtime, miss, measurement_time))
        RRD.update(self.name, time=measurement_time, ping=float(rtime), miss=miss)

    def main(self):
        logger.debug("Starting dns to %s %s IN %s @%s %s" % (self._probe_name, self.query, self.method, self.target, self.protocol))

        RRD.register(self.name, '%s %s IN %s @%s %s' % (self._probe_name, self.query, self.method, self.target, self.protocol),
                     step=self._interval*self._count, field_name="query time")

        while not self._stop:
            try:
                self.do_round()
            except Exception as e:
                logger.exception(e)
                break
        if self._stop:
            return


register_single_probe('dns', Dns)
