# encoding: utf-8

from lib.web import webapp, generate_intervals


webapp.get("/")
def callback():
    return 'Hello, World!'