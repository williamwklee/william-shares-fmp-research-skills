import datetime as dt
from .common import number,fmt,rows,cell,table

def latest(records):
    a=rows(records)
    if not a: return None
    return sorted(a,key=lambda x:str(x.get("date","")),reverse=True)[0]

def company(data):
    inc=latest(data.get("income",[]));bal=latest(data.get("balance",[]));cash=latest(data.get("cashflow",[]))
    if inc is None: raise ValueError("Income statement is required; cannot invent financials.")
    symbol=inc.get('symbol',data.get('symbol'))
    for group in ['income','balance','cashflow','segments','estimates']:
        if any(r.get('symbol') and symbol and r['symbol']!=symbol for r in rows(data.get(group,[]))):raise ValueError('Financial source belongs to a different company: '+group)
    curr=inc.get("reportedCurrency");period=inc.get("period");date=inc.get("date")
    if not date:raise ValueError('Income statement date is required; cannot select reporting or forecast periods.')
    warnings=[];metrics={"revenue":number(inc.get("revenue")),"net_income":number(inc.get("netIncome"))}
    if not curr:warnings.append('Reported currency missing; cross-statement combination is unavailable.')
    revenue=metrics["revenue"];ni=metrics["net_income"]
    metrics["net_margin_pct"]=100*ni/revenue if revenue not in (None,0) and ni is not None else None
    selected_statements={}
    for label,record,fields in [
        ("balance",bal,["totalDebt","cashAndCashEquivalents"]),("cashflow",cash,["operatingCashFlow","freeCashFlow"])]:
        if record is None: warnings.append(f"{label} data missing; brief is partial.");continue
        candidates=rows(data.get('balance' if label=='balance' else 'cashflow',[]))
        record=next((r for r in candidates if (r.get('date'),r.get('period'),r.get('reportedCurrency'))==(date,period,curr)),record)
        if not curr or (record.get("date"),record.get("period"),record.get("reportedCurrency"))!=(date,period,curr):
            warnings.append(f"{label} period/currency differs; its values are not combined.");continue
        metrics.update({k:number(record.get(k)) for k in fields})
        selected_statements[label]=record
    asof=data.get("as_of",dt.date.today().isoformat())
    if date and date>asof:raise ValueError('Latest financial period is after the requested as-of date; do not backdate current data.')
    for record in [inc,*selected_statements.values()]:
        filed=str(record.get('filingDate') or record.get('acceptedDate') or '')[:10]
        if filed and filed>asof:raise ValueError('Statement was filed after the requested as-of date; do not backdate later information.')
    prior=[r for r in rows(data['income']) if r.get('reportedCurrency')==curr and r.get('date','')<date and r.get('period')==period]
    if not prior:prior=[r for r in rows(data['income']) if r.get('reportedCurrency')==curr and r.get('date','')<date and r.get('period')!='FY' and period!='FY']
    prior=sorted(prior,key=lambda r:r['date'],reverse=True)
    if not curr or not period or not date:prior=[]
    trend=None
    if prior:
        baseline=prior[0];base_revenue=number(baseline.get('revenue'));base_income=number(baseline.get('netIncome'))
        trend={'comparison_date':baseline.get('date'),'comparison_period':baseline.get('period'),'revenue_change_pct':100*(revenue-base_revenue)/base_revenue if revenue is not None and base_revenue else None,'net_income_change_pct':100*(ni-base_income)/base_income if ni is not None and base_income else None,'comparison_label':'Same reported fiscal period in earlier year' if baseline.get('period')==period else 'Prior available quarter; seasonal effects may matter'}
    else:warnings.append('No compatible earlier income period supplied; no financial trend is inferred.')
    annual=str(data.get('estimates_period','')).lower() in ('annual','fy')
    cutoff=max(date,(data.get('latest_reported_annual_date') if annual else None) or date)
    if data.get('latest_reported_annual_date') and not annual:warnings.append('Annual reporting cutoff ignored for non-annual estimates; quarterly horizons use the latest supplied reported statement date.')
    forecasts=sorted([x for x in rows(data.get('estimates',[])) if str(x.get('date',''))>cutoff],key=lambda x:x['date'])
    ended=[x for x in forecasts if x['date']<=asof]
    quarterly=str(data.get('estimates_period','')).lower() in ('quarter','quarterly','q1','q2','q3','q4')
    frequency_conflict=quarterly and str(period).upper() not in ('Q1','Q2','Q3','Q4')
    unknown_frequency=not annual and not quarterly
    ambiguous=len(ended)>1 or frequency_conflict or (bool(ended) and unknown_frequency)
    pending=ended[0] if len(ended)==1 and not ambiguous else None
    if ambiguous:warnings.append('Pending estimate period unresolved: multiple ended horizons or incompatible/unknown statement-estimate frequency. No ended period is labelled pending; request current comparable statements and verify publication status.')
    future=next((x for x in forecasts if x['date']>asof),None)
    forecast=pending or future
    segment=latest(data.get("segments",[]));segment_sum=None
    if segment and (segment.get("date"),segment.get("period"),segment.get("reportedCurrency"))==(date,period,curr):
        vals=[number(v) for v in segment.get("data",{}).values()]
        if all(v is not None for v in vals): segment_sum=sum(vals)
        if segment_sum is not None and revenue is not None and abs(segment_sum-revenue)>max(1,abs(revenue)*0.001):
            warnings.append("Segment sum does not reconcile to revenue; investigate definitions and omitted segments.")
    else:warnings.append('Segments absent or incompatible with selected statement period/currency; no segment reconciliation is inferred.')
    modules=data.get("modules",{})
    symbol=inc.get('symbol',data.get('symbol'))
    if modules.get('earnings') and symbol:
        symbols={x.get('symbol') for x in modules['earnings'].get('calls',{}).values() if x.get('symbol')}
        if symbols and symbols!={symbol}:raise ValueError('Earnings module belongs to a different company.')
    for key in ["institutional","earnings","funds"]:
        if not modules.get(key): warnings.append(key+" analysis absent; this is a partial company brief.")
    warnings+=["Facts, derived metrics and AI interpretation must be separated; no unexplained buy/sell score.",
               "Provider attribution follows the supplied provenance; synthetic examples are invented. Original-source checks and platform support require separate evidence."]
    body=table(["Metric",f"{curr or 'currency unknown'} / {period or 'period unknown'} / {date or 'date unknown'}"],
               [[k,fmt(v)] for k,v in metrics.items()])
    if trend:body+='\n\n## Financial trend\n\n'+trend['comparison_label']+' ('+str(trend['comparison_date'])+').\n\n'+table(['Change','Percent'],[['Revenue',fmt(trend['revenue_change_pct'])],['Net income',fmt(trend['net_income_change_pct'])]])
    source_periods=[dict(module=key,date=record.get('date'),period=record.get('period'),currency=record.get('reportedCurrency'),filing_date=record.get('filingDate'),accepted_at=record.get('acceptedDate'),source=record.get('finalLink') or record.get('link') or record.get('url')) for key,record in [('income',inc),*selected_statements.items()]]
    matrix=[[x['module'],x['date'],x['period'],x['currency'],x['filing_date'],x['accepted_at'],x['source']] for x in source_periods]
    contexts=[]
    if modules.get('institutional'):
        sym=inc.get('symbol',data.get('symbol'));positions=modules['institutional'].get('positions',[])
        selected=[x for x in positions if x['security']==sym] if sym else []
        contexts.append('Institutional evidence: '+str(len(selected))+' matching manager-position comparison(s). Manager: '+str(modules['institutional'].get('metadata',{}).get('manager','not supplied'))+'. This is not the company\'s complete owner register.')
        contexts+=['Reported '+x['security']+' shares: '+fmt(x['previous_shares'],0)+' to '+fmt(x['current_shares'],0)+'. Reporting dates: '+str(x.get('previous_reporting_date'))+' to '+str(x.get('current_reporting_date'))+'. '+x['classification']+'.' for x in selected]
        if modules['institutional'].get('holders'):contexts.append('Reported institutional holders supplied: '+str(len(modules['institutional']['holders']))+'. These records are not added to indirect fund exposure.')
    if modules.get('earnings'):
        calls=modules['earnings'].get('calls',{});contexts.append('Earnings evidence: '+', '.join(k+' '+str(v.get('year'))+' '+str(v.get('period'))+' / '+str(len(v.get('passages',[])))+' located passages' for k,v in calls.items())+'. Interpretations must cite before/after passages.')
    fund_company=[]
    if modules.get('funds'):
        f=modules['funds'];contexts.append('Fund comparison overlap: '+fmt(f.get('overlap_percentage_points'))+' percentage points of identified original weights. It is not added to institutional shares.')
        for key in ['fund_a','fund_b']:
            item=f.get(key,{})
            for ident,security in item.get('securities',{}).items():
                if security.get('symbol')==symbol:fund_company.append(dict(fund=f.get('fund_labels',{}).get(key,key),weight_pct=item['weights'][ident],effective_date=f.get('effective_dates',{}).get(key),provider_updates=item.get('provider_update_timestamps',[])))
        contexts.append('Company-specific fund weights (original snapshot weights, not summed ownership): '+str(fund_company) if fund_company else 'No company-specific fund identity matched; do not substitute overall fund overlap for company exposure.')
    news=[]
    for x in rows(data.get('news',[])):
        published=str(x.get('publishedDate',x.get('date','')))[:10]
        if published and published<=asof:news.append(dict(date=published,title=x.get('title'),url=x.get('url')))
        elif published:warnings.append('News published after as-of excluded; current records cannot recreate historical context.')
    insiders=[]
    kinds={'P':'open-market/private purchase','S':'sale','A':'award/grant','M':'exercise/conversion','F':'tax/withholding disposition'}
    for x in rows(data.get('insiders',[])):
        txdate=x.get('transactionDate');code=str(x.get('transactionType','')).split('-')[0]
        if txdate and txdate<=asof:insiders.append(dict(date=txdate,type=kinds.get(code,'other/unknown transaction'),raw_type=x.get('transactionType'),shares=x.get('securitiesTransacted'),source=x.get('link') or x.get('url')))
        elif txdate:warnings.append('Insider transaction after as-of excluded; current snapshots do not reconstruct historical filing availability.')
    if not news:warnings.append('No eligible dated news supplied; no claim of complete current-news coverage.')
    if not insiders:warnings.append('No eligible insider records supplied; no insider-buying/selling verdict.')
    forecast_text='No eligible forecast horizon available.'
    if forecast:
        forecast_text='Selected eligible forecast horizon: '+str(forecast['date'])+'. '
        for label,row in [('Ended period pending in supplied reporting evidence',pending),('Next future-dated fiscal period',future)]:
            if row:forecast_text+=label+': '+str(row['date'])+'; EPS '+fmt(row.get('epsAvg'))+', revenue '+fmt(row.get('revenueAvg'))+'; EPS analysts '+cell(row.get('numAnalystsEps'))+', revenue analysts '+cell(row.get('numAnalystsRevenue'))+'. '
        forecast_text+='Period frequency: '+cell(data.get('estimates_period'))+'. Pending status is inferred from supplied reports, not independently verified publication status. Current consensus is not historical point-in-time evidence.'
        estimate_currency=forecast.get('reportedCurrency') or forecast.get('currency') or data.get('estimates_currency')
        forecast_text+=' Estimate currency: '+cell(estimate_currency)+'.'
        if not estimate_currency:warnings.append('Estimate currency is not supplied; verify source units before comparing estimates with statement currency.')
    if forecast:
        coverage={k:forecast.get(k) for k in ['numAnalystsRevenue','numAnalystsEps']};forecast_text+=' Analyst counts: '+', '.join(k+'='+cell(v) for k,v in coverage.items())+'.'
        if (dt.date.fromisoformat(forecast['date'])-dt.date.fromisoformat(asof)).days>550:warnings.append('Nearest returned forecast is distant; near-term horizons may be missing. Request more available periods before treating it as next-year consensus.')
    profile=data.get('profile',{})
    if isinstance(profile,list):profile=profile[0] if profile else {}
    if profile.get('symbol') and symbol and profile['symbol']!=symbol:raise ValueError('Profile and financial statements refer to different companies.')
    business=profile.get('description','Business description not supplied; see reported segment and source notes.')
    return {"kind":"company","symbol":symbol,'profile':profile,"date":date,"period":period,"currency":curr,"metrics":metrics,'financial_trend':trend,'source_periods':source_periods,"segment_sum":segment_sum,
            "next_available_forecast":forecast,'pending_report_estimate':pending,'unresolved_ended_estimates':ended if ambiguous else [],'next_future_estimate':future,'company_fund_exposure':fund_company,"modules":modules,'news':news,'insiders':insiders,'as_of':asof,"warnings":warnings,
            "markdown":"# Company research brief\n\nAs of "+asof+'\n\n## Business\n\n'+business+'\n\n'+body+'\n\n## Source periods\n\n'+table(['Module','Date','Period','Currency','Filed','Accepted','Source'],matrix)+'\n\n## Segment reconciliation\n\nSegment sum: '+fmt(segment_sum)+'; reported revenue: '+fmt(revenue)+'.\n\n## Forecast context\n\n'+forecast_text+'\n\n## Research context\n\n'+'\n\n'.join(contexts)+'\n\n## Dated news\n\n'+table(['Date','Title','Source'],[[x['date'],x['title'],x['url']] for x in news[:10]])+'\n\n## Insider transaction types\n\n'+table(['Date','Classification','Provider type','Shares','Source'],[[x['date'],x['type'],x['raw_type'],x['shares'],x['source']] for x in insiders[:10]])+"\n\n## Coverage and interpretation limits\n\n"+"\n".join("- "+w for w in warnings)+'\n\nConclusions should separate cited evidence, counterevidence and unresolved gaps, and explain what would change the interpretation. No composite buy/sell score.\n'}

report = company
