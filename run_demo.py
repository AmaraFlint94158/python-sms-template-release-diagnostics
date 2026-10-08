import json
import os

from src.sms_template_service import InfraiClient, SmsTemplate, publish_and_send


def main() -> None:
    recipient = os.environ["SMS_DEMO_TO"]
    result = publish_and_send(
        InfraiClient(), recipient, "DevTools", SmsTemplate("devtools-login", "Your verification code is {code}."), "482913"
    )
    print(json.dumps({"message_id": result.message_id, "status": result.status, "events": result.events}, indent=2))


if __name__ == "__main__":
    main()
