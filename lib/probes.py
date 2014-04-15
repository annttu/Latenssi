# encoding: utf-8

from lib import config, ping, exceptions

probe_types = {'ping': ping.Ping}

probes = []

probe_cache = {}

def create_probe(host, probe):
    """
    Initialize probe class
    host = hostname
    name = probe name
    """
    if probe not in probe_cache:
        if probe not in config.probes:
            raise exceptions.ConfigError("No probe named %s" % probe)
        if 'type' not in config.probes[probe]:
            raise exceptions.ConfigError("Error parsing probe %s, type is mandatory variable for probe" % probe)
        if config.probes[probe]['type'] not in probe_types:
            raise exceptions.ConfigError("Invalid probe type %s" % config.probe[name]['type'])
        opts = {}
        for k,v in config.probes[probe].items():
            if k not in ['type']:
                opts[k] = v
        # Create anonymous wrapper for probe
        probe_cache[probe] = lambda x: probe_types[config.probes[probe]['type']](x, **opts)
    probes.append(probe_cache[probe](host))

def populate():
    """
    Initialize configured probes
    """
    if probes:
        # Populate only once
        return
    for hostname, host in config.hosts.items():
        for p in host['probes']:
            create_probe(hostname, p)

