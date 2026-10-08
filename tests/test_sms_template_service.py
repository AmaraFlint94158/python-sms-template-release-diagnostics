import json

from src.sms_template_service import InfraiClient, SmsTemplate, publish_and_send


class FakeResponse:
    status = 200

    def __init__(self, value):
        self.value = value

    def read(self):
        import json
        return json.dumps(self.value).encode()


def test_publish_then_send_returns_diagnostics():
    calls = []

    def opener(request):
        calls.append((request.method, request.full_url, request.data))
        if request.full_url.endswith("/v1/sms/send"):
            return FakeResponse({"ok": True, "data": {"message_id": "m-42"}})
        if request.full_url.endswith("/v1/sms/template/create"):
            return FakeResponse({"ok": True, "data": {"template_id": "tpl-42"}})
        if "/status/" in request.full_url:
            return FakeResponse({"ok": True, "data": {"state": "delivered"}})
        if "/events/" in request.full_url:
            return FakeResponse({"ok": True, "data": {"items": []}})
        return FakeResponse({"ok": True, "data": {"accepted": True}})

    result = publish_and_send(InfraiClient("test-key", opener), "+15551234567", "DevTools", SmsTemplate("login", "Code {code}"), "123456")
    assert result.message_id == "m-42"
    assert [method for method, _, _ in calls] == ["POST", "POST", "POST", "GET", "GET"]
    assert [json.loads(body) for _, _, body in calls[:3]] == [
        {"name": "DevTools"},
        {"name": "login", "body": "Code {code}"},
        {"to": "+15551234567", "template_id": "tpl-42", "template_vars": {"code": "123456"}},
    ]
