from datetime import date, timedelta

import pytest

from reminder_service import PaymentEvent, ReminderRequest, schedule_reminder


class FakeClient:
    def __init__(self):
        self.calls = []

    def cron_create(self, **kwargs):
        self.calls.append(kwargs)
        return {"job_id": "job-test-1"}


def test_future_positive_payment_is_scheduled():
    client = FakeClient()
    event = PaymentEvent("pay-1", date.today() + timedelta(days=5), 9900, "Ledger Co")
    result = schedule_reminder(ReminderRequest(event, "https://example.test/remind"), client)
    assert result == "job-test-1"
    assert client.calls == [{"cron_expr": "0 9 * * *", "task": "https://example.test/remind"}]


def test_past_deadline_is_rejected_before_api_call():
    client = FakeClient()
    event = PaymentEvent("pay-2", date.today(), 9900, "Ledger Co")
    with pytest.raises(ValueError, match="future"):
        schedule_reminder(ReminderRequest(event, "https://example.test/remind"), client)
    assert client.calls == []
