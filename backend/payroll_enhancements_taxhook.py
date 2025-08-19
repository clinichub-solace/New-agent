from datetime import datetime
from typing import Any, Dict, List
from backend.payroll_tax import compute_taxes_for_record, get_applicable_tax_table

async def post_payroll_run_apply_taxes(db, run_id: str, user) -> Dict[str, Any]:
    # Find run by id or _id
    run = await db.payroll_runs.find_one({"id": run_id}) or await db.payroll_runs.find_one({"_id": run_id})
    if not run:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Run not found")

    # Resolve period
    period = await db.pay_periods.find_one({"id": run.get("period_id")}) or {}
    end_iso = (period.get("end_date") or period.get("start_date") or "")[:10]

    # Company-wide jurisdiction (can be extended per-employee/state)
    jurisdiction = "US-FED"
    tax_cfg = await get_applicable_tax_table(db, jurisdiction, end_iso)

    # Fetch payroll records for this period (async list)
    recs: List[Dict[str, Any]] = [r async for r in db.payroll_records.find({"payroll_period_id": run.get("period_id")})]

    gross_total = ded_total = tax_total = net_total = 0.0
    employees = 0
    posted_at = datetime.utcnow()

    for r in recs:
        gross = float(r.get("gross_pay") or r.get("gross") or 0.0)
        pretax = float(r.get("total_pre_tax_deductions") or r.get("pretax_deductions") or 0.0)
        posttax = float(r.get("total_post_tax_deductions") or r.get("posttax_deductions") or 0.0)
        deductions = pretax + posttax

        # Compute taxes if not already paid (idempotent)
        if not r.get("paid"):
            taxes_out = compute_taxes_for_record(
                gross=gross,
                pretax_deductions=pretax,
                config=tax_cfg
            )
            await db.payroll_records.update_one(
                {"id": r.get("id")},
                {"$set": {
                    "total_taxes": str(taxes_out["taxes"]),
                    "taxable_income": taxes_out["taxable_income"],
                    "tax_breakdown": taxes_out["breakdown"],
                }}
            )
            r["total_taxes"] = str(taxes_out["taxes"])

        taxes = float(r.get("total_taxes") or r.get("taxes") or 0.0)
        net = gross - deductions - taxes

        # Idempotent Finance EXPENSE posting if missing
        upd = {"status": "paid"}
        if not r.get("paid_at"):
            upd["paid_at"] = posted_at
        if not r.get("ledger_post_id"):
            fin = {
                "id": str(__import__("uuid").uuid4()),
                "direction": "EXPENSE",
                "category": "payroll",
                "amount": str(net),
                "source": {"kind": "payroll_record", "id": r.get("id")},
                "timestamp": posted_at,
            }
            await db.financial_transactions.insert_one(fin)
            upd["ledger_post_id"] = fin["id"]
        await db.payroll_records.update_one({"id": r.get("id")}, {"$set": upd})

        gross_total += gross
        ded_total += deductions
        tax_total += taxes
        net_total += net
        employees += 1

    totals = {
        "employees": employees,
        "gross": str(round(gross_total, 2)),
        "deductions": str(round(ded_total, 2)),
        "taxes": str(round(tax_total, 2)),
        "net": str(round(net_total, 2)),
        "count": employees,
    }

    await db.payroll_runs.update_one(
        {"id": run.get("id")},
        {"$set": {"totals": totals, "status": "POSTED", "posted_at": posted_at, "posted_by": getattr(user, "username", "system")}}
    )
    run.update({"totals": totals, "status": "POSTED", "posted_at": posted_at, "posted_by": getattr(user, "username", "system")})
    return run