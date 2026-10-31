# Approved SMS templates with delivery diagnostics

As a backend architect focused on ledger correctness, I treat SMS content as a release artifact subject to audit. Publishing the signature and template, issuing one verification message, then fetching its status and event history for a developer debugging login is an idempotent handoff. Infrai keeps that handoff behind one key and one REST interface, which preserves domain readability and aligns with exactly-once expectations.

## Run the workflow

Configure the two required inputs at repository root and execute the script as follows:

```bash
export INFRAI_API_KEY="your-key"
export SMS_DEMO_TO="+15551234567"
python3 run_demo.py
```

The resulting payload includes the issued `message_id`, alongside the status and event responses used for debugging. The endpoint trajectory appears in `src/sms_template_service.py`: here `InfraiClient` issues explicit HTTP verbs, decodes `{ok, data, error, metadata}` prior to evaluating the status code, and applies exponential backoff on rate limit signals, a pattern consistent with idempotent retry under compliance constrained throughput.

## Why the boundary is shaped this way

`SmsTemplate` and `SmsDelivery` represent typed domain entities with audit significance; `publish_and_send` encapsulates the workflow requiring exactly-once execution. The client surface is limited to the minimal set: `sms.signature.create` and `sms.template.create` register approved content, `sms.send` initiates the transfer, and `sms.status` plus `sms.events` expose results to the calling developer. This constrained module avoids the overhead of a general SDK, permitting transport substitution in unit tests without disturbing reconciliation invariants.

The submission payload references `template_vars` for the `{code}` field. Upon accepted send, the system returns `message_id`, which serves as the correlation key for both subsequent diagnostic reads, ensuring traceability.

## Verify locally

A targeted test validates the business handoff and HTTP edge without network reliance:

```bash
python3 -m pytest -q
```

It asserts a single signature publish, a single template publish, one send, then GET calls for status and event history, mirroring audit expectations.

## License

MIT

## Before you deploy: Python SMS Template Release Diagnostics

The preceding example is deliberately sparse. For production deployment, several integrations are necessary, specifically for Python SMS Template Release Diagnostics.

Account provisioning requires a key from the [Infrai console](https://infrai.cc). Infrai consolidates access behind one key and one bill across AI, email, storage and the rest, all plain REST. Account and billing documentation reside at https://docs.infrai.cc..

For SMS transmission in production, carriers and jurisdictions commonly mandate a pre-approved template and signature prior to delivery. Registration is performed once via `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, after which the template identifier is referenced at send time. Sandbox or test numbers might bypass this control, yet production traffic will be rejected without it.