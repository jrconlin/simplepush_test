# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import string
import random
import time
import urllib2
import ConfigParser
import os

epoch = int(time.time())

def read_config(*filenames):
    config = ConfigParser.ConfigParser()
    config.read(*filenames)

    if not config.has_section('server'):
        config.add_section('server')

    default_url = config.get('server', 'url')
    config.set('server', 'url', os.getenv('TEST_URL', default_url))

    if not config.has_section('debug'):
        config.add_section('debug')

    default_trace = config.get('debug', 'trace')
    config.set('debug', 'trace', os.getenv('TEST_TRACE', default_trace))

    default_verbose = config.get('debug', 'verbose')
    config.set('debug', 'verbose', os.getenv('TEST_VERBOSE', default_verbose))

    return config


def str_gen(size=6, chars=string.ascii_uppercase + string.digits):
    #generate rand string
    return ''.join(random.choice(chars) for x in range(size))


def str2bool(v):
    return v.lower() in ("true", "1")


def log(prefix, msg):
    print "::%s: %s" % (prefix, msg)


def get_uaid(chan_str):
    """uniquify our channels so there's no collision"""
    return "%s%s" % (chan_str, str_gen(16))


def add_epoch(chan_str):
    """uniquify our channels so there's no collision"""
    return "%s%s" % (chan_str, epoch)


def send_http_put(update_path, args='version=123',
                  ct='application/x-www-form-urlencoded',
                  exit_on_assert=False):
    """ executes an HTTP PUT with version"""

    log('send_http_put', update_path)
    opener = urllib2.build_opener(urllib2.HTTPHandler)
    request = urllib2.Request(update_path, args)
    request.add_header('Content-Type', ct)
    request.get_method = lambda: 'PUT'
    try:
        url = opener.open(request)
    except Exception, e:
        if exit_on_assert:
            import pdb; pdb.set_trace()
            exit('Exception in HTTP PUT: %s' % (e))
        raise e
    url.close()
    return url.getcode()


def compare_dict(ret_data, exp_data):
    """ Util that compares dicts returns list of errors"""
    diff = {"errors": []}
    for key in exp_data:
        if key not in ret_data:
            diff["errors"].append("%s not in %s" % (key, ret_data))
            continue
        if ret_data[key] != exp_data[key]:
            diff["errors"].append("'%s:%s' not in '%s'" % (key,
                                                           exp_data[key],
                                                           ret_data))
    return diff


def get_endpoint(ws):
    """ takes a websocket and returns http path"""
    if ws.find('wss:'):
        return ws.replace('wss:', 'https:')
    else:
        return ws.replace('ws:', 'http:')
