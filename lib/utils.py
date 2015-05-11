# encoding: utf-8
import socket


def sanitize(n):
    return n.replace('.', '_').replace(':', '_')


def get_ipv6_by_name(name):
    try:
        return socket.getaddrinfo(name, 0, socket.AF_INET6)[0][4][0]
    except socket.gaierror:
        return None


def get_ipv4_by_name(name):
    try:
        return socket.gethostbyname(name)
    except socket.gaierror:
        return None
