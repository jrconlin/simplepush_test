import websocket
import json
import uuid
import httplib
import urlparse
import random
import logging

from nose.tools import eq_

log = logging.getLogger(__name__)


def quick_register(url, use_webpush=False):
    client = Client(url, use_webpush=use_webpush)
    client.connect()
    client.hello()
    client.register()
    return client


class Client(object):
    def __init__(self, url, use_webpush=False):
        self.url = url
        self.uaid = None
        self.ws = None
        self.use_webpush = use_webpush
        self.channels = {}
        self._crypto_key = 'keyid="http://example.org/bob/keys/123;salt="XZwpw6o37R-6qoZjw6KwAw"'

    def connect(self):
        self.ws = websocket.create_connection(self.url)
        return self.ws.connected

    def hello(self):
        if self.channels:
            chans = self.channels.keys()
        else:
            chans = []
        if self.use_webpush:
            msg = json.dumps(dict(messageType="hello", uaid=self.uaid or "",
                                  use_webpush=True, channelIDs=chans))
        else:
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
        return result

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

        if self.use_webpush:
            headers = {
                "Content-Type": "application/octet-stream",
                "Content-Encoding": "aesgcm-128",
                "Encryption": self._crypto_key,
            }
            body = data or ""
            method = "POST"
        else:
            if data:
                body = "version=%s&data=%s" % (version or "", data)
            else:
                body = "version=%s" % (version or "")
            if use_header:
                headers = {"Content-Type": "application/x-www-form-urlencoded"}
            else:
                headers = {}
            method = "PUT"

        log.debug("%s body: %s", method, body)
        http.request(method, url.path, body, headers)
        resp = http.getresponse()
        log.debug("%s Response: %s", method, resp.read())
        eq_(resp.status, status)

        # Pull the notification if connected
        if self.ws and self.ws.connected:
            result = json.loads(self.ws.recv())
            return result

    def get_notification(self, timeout=0.2):
        self.ws.settimeout(timeout)
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
