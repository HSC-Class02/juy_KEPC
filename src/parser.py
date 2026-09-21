import re

ALIASES = {
    "total_assets": ["자산총계", "총자산"],
    "cash": ["현금및현금성자산", "현금및현금성자산과현금성자산"],
    "receivables": ["매출채권", "매출채권및기타채권"],
    "inventory": ["재고자산"],
    "ppe": ["유형자산"],
    "total_liabilities": ["부채총계", "총부채"],
    "interest_debt": ["단기차입금", "장기차입금", "유동성장기차입금", "사채", "유동성사채"],
    "equity": ["자본총계", "총자본"],
    "revenue": ["매출액", "수익(매출액)", "영업수익"],
    "gross_profit": ["매출총이익"],
    "sga": ["판매비와관리비", "판매비와관리비용"],
    "operating_income": ["영업이익", "영업이익(손실)"],
    "pretax_income": ["법인세비용차감전순이익", "세전이익"],
    "net_income": ["당기순이익", "당기순이익(손실)"],
    "controlling_net_income": ["지배기업의 소유주에게 귀속되는 당기순이익", "지배기업 소유주지분 순이익"],
    "interest_expense": ["이자비용", "금융비용"],
    "depreciation": ["감가상각비"],
    "amortization": ["무형자산상각비", "상각비"],
    "cfo": ["영업활동으로 인한 현금흐름", "영업활동현금흐름"],
    "cfi": ["투자활동으로 인한 현금흐름", "투자활동현금흐름"],
    "cff": ["재무활동으로 인한 현금흐름", "재무활동현금흐름"],
    "capex_ppe": ["유형자산의 취득", "유형자산 취득"],
    "capex_intangible": ["무형자산의 취득", "무형자산 취득"],
}

def norm(s):
    return re.sub(r"[\s·\u00a0]", "", str(s or "")).replace("(손실)","").replace("(수익)","")

def to_num(v):
    if v is None or v == "" or v == "-": return None
    try:
        return float(str(v).replace(",", ""))
    except ValueError:
        return None

def pick(rows, aliases):
    # Prefer exact/normalized account matches. Sum debt components separately elsewhere.
    for a in aliases:
        na = norm(a)
        for row in rows:
            if norm(row.get("account_nm")) == na:
                return to_num(row.get("thstrm_amount")), row
    for row in rows:
        n = norm(row.get("account_nm"))
        for a in aliases:
            if norm(a) in n:
                v=to_num(row.get("thstrm_amount"))
                if v is not None: return v, row
    return None, None

def extract(rows):
    out={}
    # statement-specific candidates
    for key, aliases in ALIASES.items():
        v, row = pick(rows, aliases)
        if key == "interest_debt":
            # handled below
            continue
        out[key]=v
    # interest-bearing debt: add matching balance-sheet accounts, avoiding total rows.
    debt_terms=["차입금","사채"]
    debt=0.0; found=False
    for row in rows:
        name=norm(row.get("account_nm"))
        if any(t in name for t in debt_terms) and "비용" not in name and "현금흐름" not in name:
            v=to_num(row.get("thstrm_amount"))
            if v is not None and "총계" not in name:
                debt += v; found=True
    out["interest_debt"] = debt if found else None

    # EBITDA: operating income + depreciation + amortization when available.
    if out.get("operating_income") is not None:
        dep = out.get("depreciation") or 0
        amort = out.get("amortization") or 0
        out["ebitda"] = out["operating_income"] + dep + amort
    else:
        out["ebitda"] = None

    # CAPEX is cash outflow, represented by positive magnitude here.
    capex=0
    any_capex=False
    for k in ["capex_ppe","capex_intangible"]:
        if out.get(k) is not None:
            capex += abs(out[k]); any_capex=True
    out["capex"] = capex if any_capex else None
    return out
