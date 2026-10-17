import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.dart_client import DartClient
from src.parser import extract, to_num
from src.analysis import calculate, signals, safe_div

CORP = "00159193"
START_YEAR = 2010
# DART periodic report codes: annual, half-year, Q1, Q3.
REPORTS = [
    ("annual", "11011", "사업보고서"),
    ("half_year", "11012", "반기보고서"),
    ("quarterly", "11013", "1분기보고서"),
    ("quarterly", "11014", "3분기보고서"),
]


def save_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def account_amount(rows, names):
    target = {str(n).replace(" ", "") for n in names}
    for row in rows:
        name = str(row.get("account_nm", "")).replace(" ", "")
        if name in target:
            value = to_num(row.get("thstrm_amount"))
            if value is not None:
                return value
    return None


def enrich(rows, year, category, report_code, report_name, basis):
    data = extract(rows)
    data["current_assets"] = account_amount(rows, ["유동자산", "유동자산계"])
    data["current_liabilities"] = account_amount(rows, ["유동부채", "유동부채계"])
    data["year"] = int(year)
    data["report_code"] = report_code
    data["category"] = category
    data["period_name"] = f"{year}년 {report_name}"
    data["period_id"] = f"{year}-{report_code}"
    data["financial_basis"] = basis
    data["source_rows"] = len(rows)
    return data


def simple_period_ratios(row):
    row["gross_margin"] = safe_div(row.get("gross_profit"), row.get("revenue"))
    row["operating_margin"] = safe_div(row.get("operating_income"), row.get("revenue"))
    row["net_margin"] = safe_div(row.get("net_income"), row.get("revenue"))
    row["debt_ratio"] = safe_div(row.get("total_liabilities"), row.get("equity"))
    row["equity_ratio"] = safe_div(row.get("equity"), row.get("total_assets"))
    row["current_ratio"] = safe_div(row.get("current_assets"), row.get("current_liabilities"))
    row["net_debt"] = (
        None if row.get("interest_debt") is None or row.get("cash") is None
        else row["interest_debt"] - row["cash"]
    )
    row["fcf"] = (
        None if row.get("cfo") is None or row.get("capex") is None
        else row["cfo"] - row["capex"]
    )
    return row


def fetch_report(client, year, report_code):
    """Prefer consolidated statements; use separate statements only if CFS is unavailable."""
    rows = client.financials(CORP, year, report_code, fs_div="CFS")
    if rows:
        return rows, "CFS"
    rows = client.financials(CORP, year, report_code, fs_div="OFS")
    if rows:
        return rows, "OFS"
    return [], None


def main():
    if not os.getenv("DART_API_KEY"):
        raise RuntimeError("Repository secret DART_API_KEY가 설정되어 있지 않습니다.")

    client = DartClient()
    today = datetime.now(timezone.utc)
    this_year = today.year
    annual = {}
    annual_periods = []
    half_periods = []
    quarterly_periods = []
    failures = []

    # Keep filing metadata as provenance; avoid committing large ZIP copies of report attachments.
    filings = []
    try:
        filings = client.filings(CORP, start="20100101", end=today.strftime("%Y%m%d"), page_count=100)
        save_json(ROOT / "data" / "raw" / "filings.json", filings)
    except Exception as exc:
        print(f"[WARN] 공시 목록 조회 실패: {exc}")

    for year in range(START_YEAR, this_year + 1):
        for category, report_code, report_name in REPORTS:
            # The current-year annual report cannot normally exist until the following year.
            if category == "annual" and year == this_year:
                continue
            try:
                rows, basis = fetch_report(client, year, report_code)
                if not rows:
                    continue
                item = enrich(rows, year, category, report_code, report_name, basis)
                item = simple_period_ratios(item)
                if category == "annual":
                    annual[str(year)] = item
                elif category == "half_year":
                    half_periods.append(item)
                else:
                    quarterly_periods.append(item)
                print(f"[OK] {year} {report_name}: {len(rows)} accounts ({basis})")
            except Exception as exc:
                failures.append(f"{year}/{report_name}: {exc}")
                print(f"[WARN] {year} {report_name}: {exc}")

    if not annual and not half_periods and not quarterly_periods:
        raise RuntimeError(
            "OpenDART에서 재무 데이터를 하나도 수집하지 못했습니다. "
            "DART_API_KEY와 기업코드, API 사용 한도를 확인하세요."
        )

    # Calculate annual growth and average-balance ratios chronologically.
    annual = calculate(annual)
    for year, item in annual.items():
        item["year"] = int(year)
        item["period_id"] = str(year)
        item["period_name"] = f"{year}년 사업보고서"
        item["category"] = "annual"
        item["financial_basis"] = item.get("financial_basis") or "CFS/OFS"
        item["signals"] = signals(item)

    # Keep all tables chronologically ordered in JSON; the browser displays newest first.
    annual_periods = [annual[y] for y in sorted(annual)]
    half_periods.sort(key=lambda x: (x["year"], x["report_code"]))
    quarterly_periods.sort(key=lambda x: (x["year"], x["report_code"]))

    years = sorted(int(y) for y in annual.keys())
    output = {
        "company": {"name": "한국전력공사", "corp_code": CORP},
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "latest_year": max(years) if years else None,
        "data_coverage": {
            "requested_start_year": START_YEAR,
            "first_annual_year": min(years) if years else None,
            "last_annual_year": max(years) if years else None,
            "annual_records": len(annual_periods),
            "half_year_records": len(half_periods),
            "quarterly_records": len(quarterly_periods),
        },
        "years": annual,
        "periods": {
            "annual": annual_periods,
            "half_year": half_periods,
            "quarterly": quarterly_periods,
        },
        "filings": filings[:50],
        "methodology": {
            "basis": "연결(CFS) 우선, 불가능한 경우 별도(OFS) 대체",
            "notes": [
                "데이터는 OpenDART 재무제표 계정명을 기준으로 추출하며, 자료가 없는 항목은 null로 유지합니다.",
                "Annual ROA/ROE 및 자산회전율은 가용한 경우 기초·기말 평균 잔액을 사용합니다.",
                "분기보고서 값은 보고서 원문에서 추출한 당기금액 기준으로 제공하며, 누적 금액을 임의로 단일 분기 금액으로 환산하지 않습니다.",
                "한국전력공사 연결재무제표에 계열사 실적이 포함될 수 있으므로 계열사 수치와의 중복 합산에 유의해야 합니다.",
            ],
        },
        "collection_warnings": failures[-30:],
    }

    save_json(ROOT / "data" / "processed" / "latest.json", output)
    save_json(ROOT / "dashboard" / "data.json", output)
    print(
        "[DONE] Dashboard data written. "
        f"Annual={len(annual_periods)}, half-year={len(half_periods)}, "
        f"quarterly={len(quarterly_periods)}"
    )


if __name__ == "__main__":
    main()
