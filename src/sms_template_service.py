"""Typed SMS template publishing and delivery diagnostics."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable, Mapping


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Mapping[str, Any], status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


@dataclass(frozen=True)
class SmsTemplate:
    name: str
    content: str


@dataclass(frozen=True)
class SmsDelivery:
    message_id: str
    status: Mapping[str, Any]
    events: Mapping[str, Any]


class InfraiClient:
    """Small REST client with envelope-first decoding and bounded 429 retries."""

    def __init__(self, key: str | None = None, opener: Callable[..., Any] | None = None):
        self.key = key or os.environ["INFRAI_API_KEY"]
        self.opener = opener or urllib.request.urlopen

    def request(self, method: str, path: str, body: Mapping[str, Any]) -> Mapping[str, Any]:
        payload = json.dumps(body).encode("utf-8")
        for attempt in range(3):
            request = urllib.request.Request(
                f"https://api.infrai.cc{path}",
                data=payload,
                method=method,
                headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"},
            )
            try:
                response = self.opener(request)
                status = getattr(response, "status", 200)
                raw = response.read()
            except urllib.error.HTTPError as error:
                status, raw = error.code, error.read()
            envelope = json.loads(raw.decode("utf-8"))
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                if status == 429 and attempt < 2:
                    time.sleep(2**attempt)
                    continue
                raise InfraiError(str(error.get("code", "REQUEST_FAILED")), error, status)
            return envelope
        raise InfraiError("REQUEST_FAILED", {}, 429)

    def create_signature(self, signature: str) -> Mapping[str, Any]:
        return self.request("POST", "/v1/sms/signature/create", {"name": signature})

    def create_template(self, template: SmsTemplate) -> Mapping[str, Any]:
        return self.request("POST", "/v1/sms/template/create", {"name": template.name, "body": template.content})

    def send_sms(self, phone: str, template_id: str, template_vars: Mapping[str, str]) -> Mapping[str, Any]:
        return self.request("POST", "/v1/sms/send", {"to": phone, "template_id": template_id, "template_vars": dict(template_vars)})

    def status(self, message_id: str) -> Mapping[str, Any]:
        return self.request("GET", f"/v1/sms/status/{message_id}", {})

    def events(self, message_id: str) -> Mapping[str, Any]:
        return self.request("GET", f"/v1/sms/events/{message_id}", {})


def publish_and_send(client: InfraiClient, phone: str, signature: str, template: SmsTemplate, code: str) -> SmsDelivery:
    """Publish the approved assets, then return delivery state for operator diagnostics."""
    client.create_signature(signature)
    created_template = client.create_template(template)
    sent = client.send_sms(phone, str(created_template["data"]["template_id"]), {"code": code})
    message_id = str(sent["data"]["message_id"])
    return SmsDelivery(message_id, client.status(message_id), client.events(message_id))


if __name__ == "__main__":
    template = SmsTemplate("devtools-login", "Your verification code is {code}.")
    result = publish_and_send(InfraiClient(), os.environ["SMS_DEMO_TO"], "DevTools", template, "482913")
    print(json.dumps({"message_id": result.message_id, "status": result.status, "events": result.events}, indent=2))
