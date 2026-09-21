def safe_div(a,b):
    return None if a is None or b in (None,0) else a/b

def avg(a,b):
    return None if a is None or b is None else (a+b)/2

def calculate(series):
    years=sorted(series)
    for i,y in enumerate(years):
        x=series[y]
        prev=series[years[i-1]] if i else None
        x["gross_margin"]=safe_div(x.get("gross_profit"),x.get("revenue"))
        x["operating_margin"]=safe_div(x.get("operating_income"),x.get("revenue"))
        x["net_margin"]=safe_div(x.get("net_income"),x.get("revenue"))
        x["ebitda_margin"]=safe_div(x.get("ebitda"),x.get("revenue"))
        x["roa"]=safe_div(x.get("net_income"),avg(x.get("total_assets"),prev.get("total_assets") if prev else None))
        x["roe"]=safe_div(x.get("net_income"),avg(x.get("equity"),prev.get("equity") if prev else None))
        x["current_ratio"]=safe_div(x.get("current_assets"),x.get("current_liabilities"))
        x["quick_ratio"]=safe_div(x.get("quick_assets"),x.get("current_liabilities"))
        x["debt_ratio"]=safe_div(x.get("total_liabilities"),x.get("equity"))
        x["equity_ratio"]=safe_div(x.get("equity"),x.get("total_assets"))
        x["debt_to_assets"]=safe_div(x.get("interest_debt"),x.get("total_assets"))
        x["interest_coverage"]=safe_div(x.get("operating_income"),x.get("interest_expense"))
        x["net_debt"]=None if x.get("interest_debt") is None or x.get("cash") is None else x["interest_debt"]-x["cash"]
        x["net_debt_ebitda"]=safe_div(x.get("net_debt"),x.get("ebitda"))
        x["asset_turnover"]=safe_div(x.get("revenue"),avg(x.get("total_assets"),prev.get("total_assets") if prev else None))
        x["revenue_growth"]=safe_div(x.get("revenue"),prev.get("revenue"))-1 if prev and x.get("revenue") is not None and prev.get("revenue") not in (None,0) else None
        x["cfo_to_net_income"]=safe_div(x.get("cfo"),x.get("net_income"))
        x["fcf"]=None if x.get("cfo") is None or x.get("capex") is None else x["cfo"]-x["capex"]
    return series

def signals(x):
    s=[]
    if x.get("revenue_growth") is not None and x.get("operating_margin") is not None:
        if x["revenue_growth"]>0 and x["operating_margin"]<0:
            s.append("매출 증가에도 영업이익률이 음수: 성장의 질과 원가/고정비를 확인")
    if x.get("net_income") is not None and x.get("cfo") is not None and x["net_income"]>0 and x["cfo"]<0:
        s.append("순이익은 양수지만 CFO는 음수: 이익의 현금 전환과 운전자본을 확인")
    if x.get("roe") is not None and x.get("debt_ratio") is not None:
        s.append("ROE와 부채비율을 함께 확인: 레버리지 영향을 분리")
    if x.get("fcf") is not None and x["fcf"]<0 and x.get("capex") not in (None,0):
        s.append("FCF 적자: CAPEX 목적과 조달 부담을 확인")
    return s
