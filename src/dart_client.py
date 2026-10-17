import os
import requests

BASE = "https://opendart.fss.or.kr/api"


class DartError(RuntimeError):
    pass


class DartClient:
    def __init__(self, api_key=None, timeout=60):
        self.api_key = api_key or os.getenv("DART_API_KEY")
        if not self.api_key:
            raise DartError("DART_API_KEY가 설정되지 않았습니다.")
        self.timeout = timeout
        self.session = requests.Session()

    def get(self, endpoint, params):
        p = dict(params)
        p["crtfc_key"] = self.api_key
        response = self.session.get(f"{BASE}/{endpoint}", params=p, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        # DART status 013 means no matching data for the requested period.
        if data.get("status") == "013":
            return data
        if data.get("status") != "000":
            raise DartError(f"DART API 오류 {data.get('status')}: {data.get('message')}")
        return data

    def filings(self, corp_code, start="20100101", end=None, page_count=100):
        from datetime import date
        end = end or date.today().strftime("%Y%m%d")
        data = self.get("list.json", {
            "corp_code": corp_code,
            "bgn_de": start,
            "end_de": end,
            "pblntf_ty": "A",
            "sort": "date",
            "sort_mth": "desc",
            "page_no": 1,
            "page_count": page_count,
        })
        return data.get("list", []) or []

    def financials(self, corp_code, year, reprt_code="11011", fs_div="CFS"):
        data = self.get("fnlttSinglAcntAll.json", {
            "corp_code": corp_code,
            "bsns_year": str(year),
            "reprt_code": reprt_code,
            "fs_div": fs_div,
        })
        return data.get("list", []) or []
