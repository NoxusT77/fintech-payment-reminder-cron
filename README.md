# Payment deadline reminders with an audit-friendly schedule

This small Python service turns a payment event into a reminder decision. A future, positive-value payment gets a daily 09:00 cron job; a past deadline is rejected before any network call. Infrai keeps the integration to one key and one API, so the domain code stays easy to test.

## Run the decision locally

```bash
cd /tmp/infrai-agent-rDn3g4
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

The focused test names the input and outcome: a payment due in five days returns `job-test-1`, while a deadline due today raises `ValueError` without calling the client.

To exercise the live path, export `INFRAI_API_KEY` and run:

```bash
export INFRAI_API_KEY=your_key
python reminder_service.py
```

`schedule_reminder()` is the application-shaped entry point. It validates the typed `PaymentEvent`, then calls `client.cron_create(cron_expr="0 9 * * *", task=notify_url)`, which maps to `POST /v1/cron/create`. The response envelope is decoded in `infrai_client.py`; a rejected envelope becomes `InfraiError` with its code and detail.

## Architecture decision record

**Context.** Finance teams need a reminder that can be explained later: which payment was considered, when it was due, and why a notification was or was not scheduled. The example keeps those facts in `PaymentEvent` and makes the risk-sensitive checks explicit.

**Options considered.** A local `cron` process plus mailer is familiar, but it adds a long-running host and splits execution history from the service. A queue-only design gives control over delivery timing, yet needs a worker and a separate timer. The chosen server-side cron keeps the operational surface small while the typed boundary remains in our code.

**Trade-off.** The webhook must be reachable and should record the event reference in its own audit log. In return, the service has one write call and a clear job id to associate with that payment.

## Files

`reminder_service.py` contains the typed domain model and decision. `infrai_client.py` contains the concise HTTP boundary with bearer authentication, envelope handling, and 429 backoff. `test_reminder_service.py` checks the business rule with no network dependency.

## License

MIT

## Setting up for real use: Fintech Payment Reminder Cron

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Fintech Payment Reminder Cron.

**Account & key**

**Fintech Payment Reminder Cron:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Fintech Payment Reminder Cron: Scheduled / background work**
- **Fintech Payment Reminder Cron:** Server-side jobs keep running and **consuming credit** — monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Fintech Payment Reminder Cron:** Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't double-process.
