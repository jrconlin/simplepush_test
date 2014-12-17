import os

from nose.tools import eq_, ok_

from pushtest.client import (
    Client,
    quick_register
)


def check_environ():
    return os.environ.get("PUSH_SERVER")


def test_data_delivery(url=None):
    url = url or check_environ()
    client = quick_register(url)
    result = client.send_notification(data="howdythere")
    ok_(result != None)
    eq_(result["updates"][0]["data"], "howdythere")


def test_data_delivery_without_header(url=None):
    url = url or check_environ()
    client = quick_register(url)
    result = client.send_notification(data="howdythere", use_header=False)
    ok_(result != None)
    eq_(result["updates"][0]["data"], "howdythere")
