import os

from nose.tools import eq_, ok_

from pushtest.client import (
    Client,
    quick_register
)


def check_environ():
    return os.environ.get("PUSH_SERVER")


def test_basic_deliver(url=None):
    url = url or check_environ()
    client = quick_register(url)
    result = client.send_notification()
    ok_(result != {})


def test_uaid_resumption_on_reconnect(url=None):
    url = url or check_environ()
    client = quick_register(url)
    chan = client.channels.keys()[0]
    client.disconnect()
    client.connect()
    client.hello()
    result = client.send_notification()
    ok_(result != {})
    ok_(result["updates"] > 0)
    eq_(result["updates"][0]["channelID"], chan)
