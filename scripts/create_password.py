#!/usr/bin/env python
# encoding: utf-8

import hashlib
import getpass
import string
import random


def create_hash(count=10):
     return ''.join(random.choice(string.ascii_letters + string.digits) for i in range(count))


def create_password(pw):
    hash_ = create_hash()
    return '{SHA256}%s|%s' % (hash_, hashlib.sha256("%s%s" % (hash_,pw)).hexdigest())


if __name__ == '__main__':
    pw = getpass.getpass()
    print(create_password(pw))
