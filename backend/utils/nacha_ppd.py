from datetime import datetime

def _digits(val, length): return "".join(ch for ch in str(val) if ch.isdigit()).rjust(length, "0")[:length]

def _text(val, length, align="left"):
    s = "".join(ch for ch in str(val or "") if ch.isalnum() or ch == " ")
    return (s[:length].ljust(length) if align=="left" else s[:length].rjust(length))

def _to_cents(x): return int(round(float(x) * 100))

def _routing_pair(r9): r = _digits(r9, 9); return r[:8], r[-1]

def _entry_hash(rdfi8s):
    total = sum(int(x) for x in rdfi8s) if rdfi8s else 0
    return str(total)[-10:].rjust(10, "0")

def _pad10(lines):
    rem = len(lines) % 10
    return lines if rem == 0 else lines + ["9" * 94] * (10 - rem)

def build_nacha_ppd(run: dict, entries: list[dict], cfg: dict, mode: str = "test") -> str:
    now = datetime.utcnow()
    yymmdd = now.strftime("%y%m%d"); hhmm = now.strftime("%H%M")
    file_id_mod = "A" if mode == "prod" else "T"

    # effective date from period end if present (YYYYMMDD -> yymmdd)
    eff_raw = (run.get("period", {}) or {}).get("end_date", "")[:8]
    eff_yymmdd = yymmdd
    if len(eff_raw) == 8:
        eff_yymmdd = datetime.strptime(eff_raw, "%Y%m%d").strftime("%y%m%d")

    idst = cfg["immediate_destination"];   idst_name = cfg["immediate_destination_name"]
    iori = cfg["immediate_origin"];        iori_name = cfg["immediate_origin_name"]
    odfi8 = cfg["originating_dfi_identification"]
    comp_id = cfg["company_id"];           comp_name = cfg["company_name"]
    entry_desc = (cfg.get("entry_description") or "PAYROLL")[:10]

    records = []
    # 1 File Header
    r1 = ("1" "01"
          f"{_text(idst,10,align='right')}{_text(iori,10,align='right')}"
          f"{yymmdd}{hhmm}{file_id_mod}094101"
          f"{_text(idst_name,23)}{_text(iori_name,23)}{_text('',8)}")
    records.append(r1[:94].ljust(94))

    # 5 Batch Header
    batch_no = int(run.get("batch_number", 1))
    r5 = ("5" "220"
          f"{_text(comp_name,16)}{_text('',20)}{_text(comp_id,10,align='right')}"
          "PPD"
          f"{_text(entry_desc,10)}{_text('',6)}{eff_yymmdd}{'':3}1"
          f"{_digits(odfi8,8)}{str(batch_no).rjust(7,'0')}")
    records.append(r5[:94].ljust(94))

    # 6 Entries
    rdfi8s = []; entry_count = 0; total_credits = 0; seq = 1
    for e in entries:
        amt = _to_cents(e["amount"])
        if amt <= 0: continue
        tx_code = "22" if (e.get("account_type") or "checking").lower() == "checking" else "32"
        rdfi8, cd = _routing_pair(e["routing_number"]); rdfi8s.append(rdfi8)
        acct = _text(e["account_number"], 17)
        indiv_id = _text(e.get("employee_id",""), 15)
        indiv_nm = _text(e.get("employee_name",""), 22)
        trace = f"{_digits(odfi8,8)}{str(seq).rjust(7,'0')}"; seq += 1
        r6 = ("6" f"{tx_code}{rdfi8}{cd}{acct}{str(amt).rjust(10,'0')}{indiv_id}{indiv_nm}{'':2}0{trace}")
        records.append(r6[:94].ljust(94))
        entry_count += 1; total_credits += amt

    # 8 Batch Control
    entry_hash = _entry_hash(rdfi8s)
    r8 = ("8" "220"
          f"{str(entry_count).rjust(6,'0')}{entry_hash}{'0'.rjust(12,'0')}{str(total_credits).rjust(12,'0')}"
          f"{_text(comp_id,10,align='right')}{_text('',19)}{_text('',6)}{_digits(odfi8,8)}{str(batch_no).rjust(7,'0')}")
    records.append(r8[:94].ljust(94))

    # 9 File Control
    batch_count = 1; entry_addenda_count = entry_count
    block_count = ((len(records) + 9) // 10)
    r9 = ("9"
          f"{str(batch_count).rjust(6,'0')}{str(block_count).rjust(6,'0')}{str(entry_addenda_count).rjust(8,'0')}"
          f"{entry_hash}{'0'.rjust(12,'0')}{str(total_credits).rjust(12,'0')}"
          f"{_text('',39)}")
    records.append(r9[:94].ljust(94))

    records = _pad10(records)
    return "\n".join(records) + "\n"