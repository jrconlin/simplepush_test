# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import binascii
import string
import random
import time
import urllib2
import ConfigParser
import os

epoch = int(time.time())


def env_override(config, env_name, section, name):
    default = None
    if config.has_section(section):
        default = config.get(section, name)
    else:
        config.add_section(section)
    config.set(section, name, os.getenv(env_name, default))

def read_config(*filenames):
    config = ConfigParser.ConfigParser()
    config.read(*filenames)

    env_override(config, 'TEST_URL', 'server', 'url')
    env_override(config, 'TEST_DUPES', 'server', 'allow_dupes')
    env_override(config, 'TEST_CASE_SENSITIVE', 'server', 'case_sensitive_keys')

    env_override(config, 'TEST_TRACE', 'debug', 'trace')
    env_override(config, 'TEST_VERBOSE', 'debug', 'verbose')

    return config


def str_gen(size=6, chars=string.ascii_uppercase + string.digits):
    #generate rand string
    return ''.join(random.choice(chars) for x in range(size))


def str2bool(v):
    return v in ("1", "t", "T", "true", "TRUE", "True")


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
