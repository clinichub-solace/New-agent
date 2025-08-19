from __future__ import annotations
from typing import Optional

def _to_float(x, default=0.0):
    try:
        return float(x)
    except Exception:
        return default

def _progressive_tax(amount: float, brackets: list[dict]) -> float:
    tax = 0.0
    prev = 0.0
    for b in (brackets or []):
        up_to = b.get("up_to")
        rate = _to_float(b.get("rate"))
        if up_to is None:
            tax += max(0.0, amount - prev) * rate
            break
        slab = min(max(up_to - prev, 0.0), max(amount - prev, 0.0))
        if slab > 0:
            tax += slab * rate
        if amount <= up_to:
            break
        prev = up_to
    return max(tax, 0.0)

def compute_taxes_for_record(*, gross: float, pretax_deductions: float, config: dict | None) -> dict:
    """
    Returns {"taxes": float, "breakdown": {...}, "taxable_income": float}
    Supported components (config['components']):
      - {"type":"brackets","base":"taxable","brackets":[...]}
      - {"type":"flat","name":"X","base":"gross"|"taxable","rate":0.0145}
      - {"type":"flat_capped","name":"Y","base":"gross"|"taxable","rate":0.062,"cap":160200}
    """
    gross = _to_float(gross)
    pretax = _to_float(pretax_deductions)
    cfg = config or {}
    std_ded = _to_float(cfg.get("standard_deduction"))
    taxable_income = max(0.0, gross - pretax - std_ded)

    total = 0.0
    breakdown = {}

    for comp in (cfg.get("components") or []):
        ctype = comp.get("type")
        base = comp.get("base", "taxable")
        base_amt = taxable_income if base == "taxable" else gross

        if ctype == "brackets":
            t = _progressive_tax(base_amt, comp.get("brackets") or [])
            total += t
            breakdown["brackets"] = round(t, 2)

        elif ctype == "flat":
            rate = _to_float(comp.get("rate"))
            t = max(0.0, base_amt) * rate
            total += t
            name = comp.get("name", "flat")
            breakdown[name] = round(t, 2)

        elif ctype == "flat_capped":
            rate = _to_float(comp.get("rate"))
            cap = comp.get("cap")
            capf = _to_float(cap) if cap is not None else None
            amt = base_amt if capf is None else min(base_amt, capf)
            t = max(0.0, amt) * rate
            total += t
            name = comp.get("name", "flat_capped")
            breakdown[name] = round(t, 2)

    return {
        "taxes": round(total, 2),
        "breakdown": breakdown,
        "taxable_income": round(taxable_income, 2),
    }


def get_applicable_tax_table(db, jurisdiction: str, iso_date: str) -> Optional[dict]:
    # exact match or latest <= date
    coll = db["payroll_tax_tables"]
    exact = await coll.find_one({"jurisdiction": jurisdiction, "effective_date": iso_date})
    if exact:
        return exact
    # fetch all and choose latest <= iso_date
    tables = [t async for t in coll.find({"jurisdiction": jurisdiction})]
    if not tables:
        return None
    tables.sort(key=lambda d: d.get("effective_date", "0000-00-00"))
    chosen = None
    for t in tables:
        if t.get("effective_date", "9999-99-99") <= iso_date:
            chosen = t
    return chosen or tables[-1]