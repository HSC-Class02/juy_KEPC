import io, os, zipfile
from pathlib import Path
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

    def get(self, endpoint, params):
        p = dict(params)
        p["crtfc_key"] = self.api_key
        r = requests.get(f"{BASE}/{endpoint}", params=p, timeout=self.timeout)
        r.raise_for_status()
        data = r.json()
        if data.get("status") != "000":
            raise DartError(f"DART API 오류 {data.get('status')}: {data.get('message')}")
        return data

    def rss(self, crp_cd="00159193"):
        url = "https://dart.fss.or.kr/api/companyRSS.xml"
        r = requests.get(url, params={"crpCd": crp_cd}, timeout=self.timeout)
        r.raise_for_status()
        return r.content

    def filings(self, corp_code, start="20150101", end=None, page_count=100):
        import datetime
        end = end or datetime.date.today().strftime("%Y%m%d")
        return self.get("list.json", {
            "corp_code": corp_code, "bgn_de": start, "end_de": end,
            "pblntf_ty": "A", "pblntf_detail_ty": "A001",
            "sort": "date", "sort_mth": "desc",
            "page_no": 1, "page_count": page_count
        }).get("list", [])

    def financials(self, corp_code, year, reprt_code="11011"):
        return self.get("fnlttSinglAcntAll.json", {
            "corp_code": corp_code, "bsns_year": str(year),
            "reprt_code": reprt_code, "fs_div": "CFS"
        }).get("list", [])

    def download_document(self, rcept_no, output_path):
        p = {"crtfc_key": self.api_key, "rcept_no": rcept_no}
        r = requests.get(f"{BASE}/document.xml", params=p, timeout=120)
        r.raise_for_status()
        # DART document API returns a binary ZIP.
        Path(output_path).write_bytes(r.content)
        try:
            with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                if z.testzip() is not None:
                    raise DartError("다운로드된 DART 원문 ZIP 검증 실패")
        except zipfile.BadZipFile:
            # Preserve the response for diagnosis; it may be a JSON error response.
            try:
                msg = r.content.decode("utf-8", errors="ignore")[:500]
            except Exception:
                msg = "binary response"
            raise DartError(f"DART 원문 다운로드 실패: {msg}")
