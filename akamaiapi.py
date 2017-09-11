"""Implements Akamai Edgegrid API endpoints
"""
import json

from urllib.parse import urljoin

import requests

from akamai.edgegrid import EdgeGridAuth

class Session:
    """Sends authenticated to Akamai API endpoints"""
    def __init__(self, client_token, client_secret, access_token, base_url):
        session = requests.Session()
        session.auth = EdgeGridAuth(client_token, client_secret, access_token)
        self.session = session
        self.base_url = base_url

    def _url_for(self, path):
        return urljoin(self.base_url, path)

    def post_json(self, path, data, headers=None):
        """POST request to Akamai API"""
        default_headers = {
            "Content-Type": "application/json",
        }
        if headers:
            default_headers.update(headers)

        resp = self.session.post(
            self._url_for(path),
            data=json.dumps(data),
            headers=default_headers,
        )
        return resp


class API:
    """High level interface to Akamai API"""
    def __init__(self, akamai_session):
        self.session = akamai_session

    def cache_invalidate(self, hostname, paths, environment="production"):
        """Invalidates paths for hostname"""
        path = "/ccu/v3/invalidate/url/{}".format(environment)
        data = {
            'hostname': hostname,
            'objects': paths,
        }
        resp = self.session.post_json(path, data)
        return resp.json()
