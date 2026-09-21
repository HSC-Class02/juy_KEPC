import json, os, sys
from pathlib import Path
from datetime import datetime, timedelta

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.dart_client import DartClient
from src.parser import extract

CORP="00159193"
RAW=ROOT/"data/raw"; PROC=ROOT/"data/processed"
RAW.mkdir(parents=True,exist_ok=True); PROC.mkdir(parents=True,exist_ok=True)

def save_json(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding="utf-8")

def main():
    c=DartClient()
    # Preserve the company RSS feed supplied by the user as a source archive.
    (RAW/"companyRSS.xml").write_bytes(c.rss(CORP))
    filings=c.filings(CORP)
    # Keep only 사업보고서 filings. DART may return amendments; latest filing date wins.
    filings=[f for f in filings if f.get("report_nm") and "사업보고서" in f.get("report_nm","")]
    save_json(RAW/"filings.json", filings)

    state_path=PROC/"state.json"
    state=json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {"rcept_no":[]}
    known=set(state.get("rcept_no",[]))
    for f in filings:
        r=f.get("rcept_no")
        if not r or r in known: continue
        out=RAW/f"{f.get('bsns_year','unknown')}_{r}.zip"
        try:
            c.download_document(r,out)
            known.add(r)
        except Exception as e:
            print(f"[WARN] 원문 다운로드 실패 {r}: {e}")

    # Financial data for up to 5 latest business-report years available.
    years=sorted({int(f["bsns_year"]) for f in filings if str(f.get("bsns_year","")).isdigit()}, reverse=True)[:5]
    series={}
    for y in years:
        try:
            rows=c.financials(CORP,y,"11011")
            save_json(RAW/f"financials_{y}.json",rows)
            data=extract(rows)
            # Derive current assets/liabilities and quick assets from account names.
            data["current_assets"]=sum(v or 0 for v,_ in [next(((float(r["thstrm_amount"].replace(",","")),r) for r in rows if r.get("account_nm") in ["유동자산","유동자산계"]), (0,None))])
            # Safer explicit scan:
            for r in rows:
                n=str(r.get("account_nm","")).replace(" ","")
                if n in ("유동자산","유동자산계"): data["current_assets"]=float(r["thstrm_amount"].replace(",",""))
                if n in ("유동부채","유동부채계"): data["current_liabilities"]=float(r["thstrm_amount"].replace(",",""))
            data["quick_assets"] = None
            if data.get("current_assets") is not None and data.get("inventory") is not None:
                data["quick_assets"]=data["current_assets"]-data["inventory"]
            data["year"]=y
            series[str(y)]=data
        except Exception as e:
            print(f"[WARN] 재무데이터 {y}: {e}")

    from src.analysis import calculate, signals
    series=calculate(series)
    for y,x in series.items(): x["signals"]=signals(x)

    latest_year=max(map(int,series)) if series else None
    output={
        "company":{"name":"한국전력공사","corp_code":CORP},
        "updated_at":datetime.utcnow().isoformat()+"Z",
        "latest_year":latest_year,
        "years":series,
        "filings":filings[:20],
        "methodology":{
            "basis":"연결(CFS) 우선",
            "guide":"첨부 재무제표 및 재무비율 실무 가이드",
            "notes":["ROA/ROE/회전율은 평균 자산·자본을 사용","단일 비율보다 성장→마진→현금흐름→차입→투자수익률 순으로 연결 분석"]
        }
    }
    save_json(PROC/"latest.json",output)
    state["rcept_no"]=sorted(known)
    save_json(state_path,state)

if __name__=="__main__": main()
