"""Reconcile integer-cent payment entries against an invoice register."""
from __future__ import annotations

from typing import Any

from .common import ApplicationInputError, require_array, require_integer, require_object, require_text


def run(payload: dict[str, Any]) -> dict[str, Any]:
    invoices_raw = require_array(payload, "invoices")
    payments_raw = require_array(payload, "payments")
    invoices: dict[str, int] = {}
    for index, item in enumerate(invoices_raw):
        invoice = require_object(item, f"invoices[{index}]")
        invoice_id = require_text(invoice.get("id"), f"invoices[{index}].id")
        if invoice_id in invoices:
            raise ApplicationInputError(f"duplicate_invoice_id: {invoice_id}")
        invoices[invoice_id] = require_integer(invoice.get("total_cents"), f"invoices[{index}].total_cents", minimum=0)

    seen_transactions: set[str] = set()
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(payments_raw):
        payment = require_object(item, f"payments[{index}]")
        tx_id = require_text(payment.get("tx_id"), f"payments[{index}].tx_id")
        if tx_id in seen_transactions:
            raise ApplicationInputError(f"duplicate_transaction_id: {tx_id}")
        seen_transactions.add(tx_id)
        invoice_id = require_text(payment.get("invoice_id"), f"payments[{index}].invoice_id")
        paid = require_integer(payment.get("amount_cents"), f"payments[{index}].amount_cents", minimum=0)
        if invoice_id not in invoices:
            rows.append({"tx_id": tx_id, "status": "orphan_payment", "diff_cents": paid})
            continue
        expected = invoices[invoice_id]
        difference = paid - expected
        rows.append({
            "tx_id": tx_id,
            "invoice_id": invoice_id,
            "status": "matched" if difference == 0 else "mismatch",
            "paid_cents": paid,
            "invoice_cents": expected,
            "diff_cents": difference,
        })

    return {
        "reconciliation": rows,
        "counts": {
            "payments": len(payments_raw),
            "matched": sum(row["status"] == "matched" for row in rows),
            "mismatched": sum(row["status"] == "mismatch" for row in rows),
            "orphaned": sum(row["status"] == "orphan_payment" for row in rows),
        },
        "unit": "integer_cents",
    }
