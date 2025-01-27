from __future__ import annotations

from datetime import timedelta as td

from hc.api.models import Check, Ping
from hc.test import BaseTestCase


class GetPingsTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()

        self.a1 = Check(project=self.project, name="Alice 1")
        self.a1.timeout = td(seconds=3600)
        self.a1.grace = td(seconds=900)
        self.a1.n_pings = 1
        self.a1.status = "new"
        self.a1.tags = "a1-tag a1-additional-tag"
        self.a1.desc = "This is description"
        self.a1.save()

        self.ping = Ping(owner=self.a1)
        self.ping.n = 1
        self.ping.remote_addr = "1.2.3.4"
        self.ping.scheme = "https"
        self.ping.method = "get"
        self.ping.ua = "foo-agent"
        self.ping.save()

        self.url = "/api/v1/checks/%s/pings/" % self.a1.code

    def get(self, api_key="X" * 32):
        return self.csrf_client.get(self.url, HTTP_X_API_KEY=api_key)

    def test_it_works(self):
        r = self.get()
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["Access-Control-Allow-Origin"], "*")

        doc = r.json()
        self.assertEqual(len(doc["pings"]), 1)

        ping = doc["pings"][0]
        self.assertEqual(ping["n"], 1)
        self.assertEqual(ping["remote_addr"], "1.2.3.4")
        self.assertEqual(ping["scheme"], "https")
        self.assertEqual(ping["method"], "get")
        self.assertEqual(ping["ua"], "foo-agent")

    def test_readonly_key_is_not_allowed(self):
        self.project.api_key_readonly = "R" * 32
        self.project.save()

        r = self.get(api_key=self.project.api_key_readonly)
        self.assertEqual(r.status_code, 401)

    def test_it_rejects_post(self):
        r = self.csrf_client.post(self.url, HTTP_X_API_KEY="X" * 32)
        self.assertEqual(r.status_code, 405)

    def test_it_handles_missing_api_key(self):
        r = self.client.get(self.url)
        self.assertContains(r, "missing api key", status_code=401)
