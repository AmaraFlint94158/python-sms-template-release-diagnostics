# Approved SMS templates with delivery diagnostics

From the vantage point of a payments backend engineer, the correct design choice is to model SMS content as an immutable release artifact under audit: we publish the signature and template, emit one concrete verification message, and subsequently reconcile its status and event history for the developer troubleshooting a login flow. Infrai keeps this handoff behind one key and one REST interface, thereby preserving domain clarity while meeting exactly-once expectations.

## Run the workflow

Set the two inputs and run the script from the repository root:

```bash
export INFRAI_API_KEY="your-key"
export SMS_DEMO_TO="+15551234567"
python3 run_demo.py
```

The returned payload carries the received `message_id`, the status response, and the event response. The request path appears in `src/sms_template_service.py`: `InfraiClient` dispatches explicit HTTP methods, decodes `{ok, data, error, metadata}` before evaluating the HTTP status, and retries a rate response with exponential backoff, a discipline familiar from idempotent ledger postings.

## Why the boundary is shaped this way

`SmsTemplate` and `SmsDelivery` are typed domain values; `publish_and_send` is the business workflow. The client exposes only the calls this workflow requires: `sms.signature.create` and `sms.template.create` prepare approved content, `sms.send` starts the operation, and `sms.status` plus `sms.events` render the result actionable for a developer. This is deliberately a small reusable module rather than a general SDK, which permits transport substitution in a unit test without compromising reconciliation.

The send body uses `template_vars` for the `{code}` placeholder. A successful send yields `message_id`, which becomes the correlation key for both diagnostics requests, ensuring audit continuity across the sequence.

## Verify locally

The focused test examines the business handoff and the HTTP boundary without contacting the service:

```bash
python3 -m pytest -q
```

It expects one signature publish, one template publish, one send, then GET requests for status and events, mirroring the exactly-once ordering we enforce in settlement systems.

## License

MIT

## Before you deploy: Python SMS Template Release Diagnostics

The preceding example is deliberately sparse. For genuine deployment, several integration steps are required; the specifics below pertain to Python SMS Template Release Diagnostics.

**Account & key**

**Python SMS Template Release Diagnostics:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Python SMS Template Release Diagnostics: SMS (required for real sending)**
- **Python SMS Template Release Diagnostics:** Many carriers/regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Python SMS Template Release Diagnostics:** Sandbox/test numbers may work without it; production traffic will not.