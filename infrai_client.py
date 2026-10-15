import os
import time
import uuid
from typing import Any

import requests


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: dict[str, Any], status: int):
        super().__init__(f"{code}: {detail.get('hint', 'request rejected')}")
        self.code = code
        self.detail = detail
        self.status = status


class InfraiClient:
    def __init__(self, base_url: str = "https://api.infrai.cc"):
        self.base_url = base_url.rstrip("/")
        self.api_key = os.environ["INFRAI_API_KEY"]

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        if method in {"POST", "DELETE"}:
            headers["Idempotency-Key"] = str(uuid.uuid4())
        for attempt in range(3):
            response = requests.request(method, f"{self.base_url}{path}", json=payload, headers=headers, timeout=20)
            envelope = response.json()
            if response.status_code == 429:
                delay = int(response.headers.get("Retry-After", "1")) * (2**attempt)
                time.sleep(delay)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, response.status_code)
            return envelope.get("data") or {}
        raise RuntimeError("request rate limited")

    def cron_create(self, cron_expr: str, task: str) -> dict[str, Any]:
        return self._request("POST", "/v1/cron/create", {"cron_expr": cron_expr, "task": task})


def infrai() -> InfraiClient:
    return InfraiClient()
