# encoding: utf-8

from lib import web, rrd
from lib import config
import tempfile
import os
import time
import json

from bottle import abort, request, response, redirect

import logging

logger = logging.getLogger("pages")

indexpage = web.WebPage("index", "Index")

def index(interval):
    if interval not in config.intervals.keys():
        abort(404, "Invalid interval")

    pages = []
    for probename, probe in web.get_probes().items():
        pages.append({
            "title": probe.name,
            "name": probe.title,
            "img": probe.get_index_graph(interval),
            "link": probe.get_path(interval)
        })


    return web.webgenerator.output("index.html", {'pages': pages, 'intervals': indexpage.generate_intervals()})

def probepage(probe, interval):
    if interval not in config.intervals.keys():
        abort(404, "Invalid interval")
    p = web.get_probe(probe)
    if not p:
        abort(404, "Not such probe")

    return web.webgenerator.output("host.html", {'host': {'name': p.title, 'probes': p.get_graph_urls(interval)},
                                                 'intervals': p.generate_intervals(),
                                                 'index': indexpage.get_path(interval)})

def full_path(x):
    return "%s%s" % (config.relative_path.rstrip("/"), x)

if config.relative_path.lstrip("/") != "":
    @web.webapp.get("/")
    @web.webapp.get("")
    def callback():
        return redirect(full_path("/"))


@web.webapp.get(full_path(""))
@web.webapp.get(full_path("/"))
def callback():
    return index(config.default_interval)

@web.webapp.get(full_path( "/<interval>"))
def callback(interval):
    return index(interval)

@web.webapp.get(full_path("/probes/<probe>/"))
@web.webapp.get(full_path("/probes/<probe>"))
def callback(probe):
    interval = config.default_interval
    return probepage(probe, interval)

@web.webapp.get(full_path("/probes/<probe>/<interval>"))
@web.webapp.get(full_path("/probes/<probe>/<interval>/"))
def callback(probe, interval):
    return probepage(probe, interval)

@web.webapp.get(full_path('/graph/<graph>/'))
def callback(graph):
    if not rrd.RRD.exists(graph):
        return abort(404, "No such graph")
    response.set_header('Content-Type', 'image/png')
    params = dict(request.GET)

    start = None
    end = None
    if 'start' in params:
        try:
            start = int(params['start'])
        except ValueError:
            abort(400, "Invalid start time")
            return
    else:
        start = time.time() - 3600 * 24
    if 'end' in params:
        try:
            end = int(params['end'])
        except ValueError:
            abort(400, "Invalid end time")
            return
    else:
        end = time.time()
    if 'interval' in params:
        interval = params['interval']
        if interval not in config.intervals.keys():
            abort(400, "Invalid interval")
            return
        else:
            start = time.time() - config.intervals[interval]
    width = None
    height = None
    if 'width' in params:
        try:
            width = int(params['width'])
        except ValueError:
            abort(400, "Invalid width")
            return
    if 'height' in params:
        try:
            height = int(params['height'])
        except ValueError:
            abort(400, "Invalid height")
            return
    (tf, path) = tempfile.mkstemp()
    retval = None
    try:
        rrd.RRD.graph(graph, path, start=start, end=end, width=width, height=height)
        f = os.fdopen(tf, 'rb')
        retval = f.read()
        f.close()
    except Exception as e:
        logging.exception("Got unknown error")
    return retval

@web.webapp.get(full_path('/rrd/<graph>/'))
def callback(graph):
    if not rrd.RRD.exists(graph):
        return abort(404, "No such graph")
    params = dict(request.GET)
    start = None
    end = None
    if 'start' in params:
        try:
            start = int(params['start'])
        except ValueError:
            abort(400, "Invalid start time")
            return
    else:
        start = int(time.time() - 3600 * 24)
    if 'end' in params:
        try:
            end = int(params['end'])
        except ValueError:
            abort(400, "Invalid end time")
            return
    else:
        end = int(time.time())
    if 'interval' in params:
        interval = params['interval']
        if interval not in config.intervals.keys():
            abort(400, "Invalid interval")
            return
        else:
            start = int(time.time() - config.intervals[interval])

    g = rrd.RRD.get_graph(graph)

    response.set_header('Content-Type', 'application/json')

    return json.dumps(g.fetch(start=int(start), end=int(end)))