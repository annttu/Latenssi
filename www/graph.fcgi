#!/usr/bin/env python
# encoding: utf-8

from cgi import escape
import sys, os
from flup.server.fcgi import WSGIServer
from urlparse import urlparse, parse_qs
import time
import tempfile

sys.path.insert(0, '/opt/latenssi/Latenssi')

from lib import config, latenssi, probes

intervals = {'hour': 3600, '2hour': 7200, '8hour': 8 * 3600, 'day': 24 * 3600, 'week': 7*24*3600, 'month': 30*24*3600, 'year': 365*24*3600}


def app(environ, start_response):
    def error(msg):
        start_response('400 Bad Request', [('Content-Type', 'text/plain')])
        return str(msg)

    params = parse_qs(environ['QUERY_STRING'])
    graph = None
    rrd = None
    interval = None
    if 'graph' in params:
        graph = params['graph'][0]
        if graph not in probes.probes_dict:
            yield error("Invalid probe")
            return
        else:
            rrd = probes.probes_dict[graph].rrd
    else:
        error("graph missing")
        return

    start = None
    end = None
    if 'start' in params:
        try:
            start = int(params['start'][0])
        except ValueError:
            yield error("Invalid start time")
            return
    else:
        start = time.time() - 3600 * 24
    if 'end' in params:
        try:
            end = int(params['end'][0])
        except ValueError:
            yield error("Invalid end time")
            return
    else:
        end = time.time()
    if 'interval' in params:
        interval = params['interval'][0]
        if interval not in intervals.keys():
            yield error("Invalid interval")
            return
        else:
            start = time.time() - intervals[interval]
    start_response('200 OK', [('Content-Type', 'image/png')])
    (tf, path) = tempfile.mkstemp()
    try:
        rrd.graph(path, start=start, end=end)
        f = os.fdopen(tf, 'rb')
        yield f.read()
        f.close()
    except Exception as e:
        pass
    os.remove(path)

WSGIServer(app).run()