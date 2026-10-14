"""Optional READ-ONLY Adobe client scaffold; demo never requires API credentials.

Validate base URL, entitlement, request headers, authentication, pagination and
response shapes against your Adobe VIP Marketplace contract before enabling.
"""
import requests

class AdobeClient:
    def __init__(self, base_url, access_token, api_key):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {access_token}",
            "x-api-key": api_key,
            "Accept": "application/json",
        })

    def get(self, path, params=None):
        response = self.session.get(self.base_url + path, params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    def get_resellers(self):
        return self.get("/v3/resellers")

    def get_customers(self, reseller_id):
        return self.get(f"/v3/resellers/{reseller_id}/customers")

    def get_subscriptions(self, customer_id):
        return self.get(f"/v3/customers/{customer_id}/subscriptions")

    def get_orders(self, customer_id):
        return self.get(f"/v3/customers/{customer_id}/orders")

    def get_open_acquisitions(self, customer_id):
        return self.get(f"/v3/customers/{customer_id}/open-acquisitions")
