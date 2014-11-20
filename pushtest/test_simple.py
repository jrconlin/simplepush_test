import os

from nose.tools import eq_, ok_

from pushtest.client import (
    Client,
    quick_register
)

def check_environ():
    return os.environ.get("PUSH_SERVER")


def test_delivery_while_disconnected(url=None):
    url = url or check_environ()
    client = quick_register(url)
    client.disconnect()
    ok_(client.channels)
    chan = client.channels.keys()[0]
    client.send_notification()
    client.connect()
    client.hello()
    result = client.get_notification()
    ok_(result != {})
    ok_(result["updates"] > 0)
    eq_(result["updates"][0]["channelID"], chan)
