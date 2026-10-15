from dataclasses import dataclass
from datetime import date

from infrai_client import InfraiClient


@dataclass(frozen=True)
class PaymentEvent:
    reference: str
    due_date: date
    amount_cents: int
    counterparty: str


@dataclass(frozen=True)
class ReminderRequest:
    event: PaymentEvent
    notify_url: str
    days_before: int = 3


def schedule_reminder(request: ReminderRequest, client: InfraiClient) -> str:
    """Schedule only future, positive-value payments and return the job id."""
    today = date.today()
    if request.event.amount_cents <= 0:
        raise ValueError("payment amount must be positive")
    if request.event.due_date <= today:
        raise ValueError("payment deadline must be in the future")
    if request.days_before < 0 or request.days_before >= (request.event.due_date - today).days:
        raise ValueError("reminder window must precede the deadline")
    job = client.cron_create(
        cron_expr=f"0 9 * * *",
        task=request.notify_url,
    )
    return str(job["job_id"])


if __name__ == "__main__":
    event = PaymentEvent("invoice-204", date(2027, 1, 15), 125000, "Acme Treasury")
    job_id = schedule_reminder(ReminderRequest(event, "https://example.com/hooks/payment"), InfraiClient())
    print(f"scheduled payment reminder {event.reference}: {job_id}")
