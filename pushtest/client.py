import websocket
import json
import uuid
import httplib
import urlparse
import random
import logging

from nose.tools import eq_

log = logging.getLogger(__name__)


def quick_register(url):
    client = Client(url)
    client.connect()
    client.hello()
    client.register()
    return client


class Client(object):
    def __init__(self, url):
        self.url = url
        self.uaid = None
        self.ws = None
        self.channels = {}

    def connect(self):
        self.ws = websocket.create_connection(self.url)
        return self.ws.connected

    def hello(self):
        if self.channels:
            chans = self.channels.keys()
        else:
            chans = []
        msg = json.dumps(dict(messageType="hello", uaid=self.uaid or "",
                              channelIDs=chans))
        log.debug("Send: %s", msg)
        self.ws.send(msg)
        result = json.loads(self.ws.recv())
        log.debug("Recv: %s", result)
        if self.uaid and self.uaid != result["uaid"]:
            log.debug("Mismatch on re-using uaid. Old: %s, New: %s",
                      self.uaid, result["uaid"])
            self.channels = {}
        self.uaid = result["uaid"]
        eq_(result["status"], 200)

    def register(self, chid=None):
        chid = chid or str(uuid.uuid4())
        msg = json.dumps(dict(messageType="register", channelID=chid))
        log.debug("Send: %s", msg)
        self.ws.send(msg)
        result = json.loads(self.ws.recv())
        log.debug("Recv: %s", result)
        eq_(result["status"], 200)
        eq_(result["channelID"], chid)
        self.channels[chid] = result["pushEndpoint"]
        return result

    def unregister(self, chid):
        msg = json.dumps(dict(messageType="unregister", channelID=chid))
        log.debug("Send: %s", msg)
        self.ws.send(msg)
        result = json.loads(self.ws.recv())
        log.debug("Recv: %s", result)
        return result

    def send_notification(self, channel=None, version=None, data=None,
                          use_header=True, status=200):
        if not self.channels:
            raise Exception("No channels registered.")

        if not channel:
            channel = random.choice(self.channels.keys())

        if channel not in self.channels:
            raise Exception("Channel not present.")

        endpoint = self.channels[channel]
        url = urlparse.urlparse(endpoint)
        http = None
        if url.scheme == "https":
            http = httplib.HTTPSConnection(url.netloc)
        else:
            http = httplib.HTTPConnection(url.netloc)
        if data:
            body = "version=%s&data=%s" % (version or "", data)
        else:
            body = "version=%s" % (version or "")
        log.debug("PUT body: %s", body)
        if use_header:
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
        else:
            headers = {}
        http.request("PUT", url.path, body, headers)
        resp = http.getresponse()
        log.debug("PUT Response: %s", resp.read())
        eq_(resp.status, status)

        # Pull the notification if connect
        if self.ws and self.ws.connected:
            result = json.loads(self.ws.recv())
            return result

    def get_notification(self):
        self.ws.settimeout(0.2)
        try:
            return json.loads(self.ws.recv())
        except:
            return None

    def ping(self):
        log.debug("Send: %s", "{}")
        self.ws.send("{}")
        result = self.ws.recv()
        log.debug("Recv: %s", result)
        eq_(result, "{}")
        return result

    def ack(self, channel, version):
        msg = json.dumps(dict(messageType="ack",
                              updates=[dict(channelID=channel,
                                            version=version)]))
        log.debug("Send: %s", msg)
        self.ws.send(msg)

    def disconnect(self):
        self.ws.send_close()
        self.ws.close()
        self.ws = None
