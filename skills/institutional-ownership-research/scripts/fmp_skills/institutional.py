
import datetime as dt
from .common import number,fmt,rows,cell,table
from .filings import identity,quantity,resolve_filings,validate_quarters

def changes(current,previous):
    def index(a):
        result={}
        for x in rows(a):
            ident=identity(x)
            if not ident[0]: raise ValueError("A position has no CUSIP or symbol.")
            shares=quantity(x.get("shares",x.get("sharesNumber")))
            value=number(x.get("value",x.get("marketValue")))
            if value is not None and value<0:raise ValueError('Negative reported13Fvalue; verify units/schema before comparison.')
            if shares is None: raise ValueError(f"Missing shares for {ident[0]}; no inferred zero.")
            if ident in result:
                old=result[ident]
                old["shares"]+=shares
                old["value"]=None if old["value"] is None or value is None else old["value"]+value
            else: result[ident]={"symbol":x.get("symbol") or ident[0],"shares":shares,"value":value,
                                 "date":x.get("date"),"filing_date":x.get("filingDate"),'accepted_date':x.get('acceptedDate'),
                                 "source":x.get("link") or x.get("finalLink")}
        return result
    a,b=index(current),index(previous);out=[]
    for ident in sorted(set(a)|set(b),key=str):
        x,y=a.get(ident),b.get(ident)
        state="first observed" if y is None else "not in current supplied data" if x is None else (
              "shares increased" if x["shares"]>y["shares"] else "shares decreased" if x["shares"]<y["shares"] else "shares unchanged")
        old=y["shares"] if y else None;new=x["shares"] if x else None
        out.append({"security":(x or y)["symbol"],"identity":list(ident),"previous_shares":old,
                    "current_shares":new,"share_change":new-old if new is not None and old is not None else None,
                    "previous_value":y["value"] if y else None,"current_value":x["value"] if x else None,
                    "classification":state,
                    "previous_reporting_date":y.get("date") if y else None,
                    "current_reporting_date":x.get("date") if x else None,
                    "previous_filing_date":y.get("filing_date") if y else None,
                    "current_filing_date":x.get("filing_date") if x else None,
                    "previous_accepted_date":y.get('accepted_date') if y else None,
                    "current_accepted_date":x.get('accepted_date') if x else None,
                    "previous_source":y.get("source") if y else None,
                    "current_source":x.get("source") if x else None,
                    "previous_symbol":y.get("symbol") if y else None,
                    "current_symbol":x.get("symbol") if x else None})
    return out

def institutional(data):
    data=dict(data)
    if data.get('amendments_unresolved'):raise ValueError('Unresolved amendments; comparison stopped.')
    for label in ['current','previous']:
        if label+'_filings' in data:data[label]=resolve_filings(data[label+'_filings'])
    validate_quarters(rows(data['current']),rows(data['previous']))
    result=changes(data["current"],data["previous"])
    warnings=["Changes describe the supplied reported positions, not exact trades or current holdings.",
              "Market-value changes do not establish share purchases, trade dates, cost basis or motives."]
    if not data.get("source_checks_complete",False): warnings.append("Independent original-filing validation is pending.")
    if not data.get("coverage_complete",False): warnings.append("Full filing coverage/amendment reconciliation is unverified; first/missing observations are not asserted buys or exits.")
    if data.get("corporate_actions_unresolved"): warnings.append("Corporate-action effects unresolved: "+cell(data["corporate_actions_unresolved"]))
    warnings.append('Weights use supplied reported 13F value, not the manager\'s total assets.')
    coverage_complete=bool(data.get('coverage_complete',False))
    for check in data.get('coverage_checks',[]):
        returned=check.get('returned_rows');limit=check.get('request_limit')
        if returned is not None and limit is not None and returned==limit:
            coverage_complete=False;warnings.append('Returned rows equal the request limit; possible truncation, coverage is not complete.')
        if check.get('source_entry_total') is not None and check.get('reconciled_raw_rows')!=check['source_entry_total']:
            coverage_complete=False;warnings.append('Original SEC entry total is not reconciled to original raw rows; normalized provider row counts alone cannot establish coverage.')
    if any(p['identity'][3] for p in result):warnings.append('Option rows use reported underlying values, not option market values; reported-value weights are not economic exposure weights.')
    for label in ['current','previous']:
        values=[p[label+'_value'] for p in result if p[label+'_shares'] is not None]
        total=sum(values) if values and all(v is not None and v>=0 for v in values) else None
        for p in result:
            v=p[label+'_value'];p[label+'_reported_value_weight_pct']=100*v/total if total and v is not None else None
    for p in result:
        old=p['previous_shares'];delta=p['share_change'];p['share_change_pct']=100*delta/old if old and delta is not None else None
        pv=p['previous_value'];cv=p['current_value'];p['reported_value_change_pct']=100*(cv-pv)/pv if pv and cv is not None else None
        action=data.get('split_adjustments',{}).get(p['identity'][0])
        if action:
            ratio=number(action.get('ratio'))
            if ratio is None or ratio<=0 or not action.get('source'):raise ValueError('Split adjustment needs positive ratio and source.')
            p['split_adjustment']=action;p['split_adjusted_share_change']=p['current_shares']-old*ratio if old is not None and p['current_shares'] is not None else None
            adjusted=p['split_adjusted_share_change']
            if adjusted is not None:p['classification']=('unchanged' if adjusted==0 else 'increased' if adjusted>0 else 'decreased')+' (split-adjusted)'
            warnings.append('Split-adjusted change for '+p['security']+' uses an explicitly sourced ratio; raw reported shares retained.')
    for label in ("previous","current"):
        for record in rows(data[label]):
            if not (record.get("securityCusip") or record.get("cusip")):
                warnings.append(f"{label}: CUSIP missing for {cell(record.get('symbol'))}; symbol fallback is provisional and cannot establish an identifier match.")
    for position in result:
        if position['previous_symbol'] and position['current_symbol'] and position['previous_symbol']!=position['current_symbol']:
            warnings.append(f"Symbol changed for matched identity {cell(position['identity'][0])}: {cell(position['previous_symbol'])} to {cell(position['current_symbol'])}; review corporate actions and identifier continuity.")
    provenance=data.get('provenance',{})
    metadata={"manager":data.get('manager',provenance.get('manager')),
              "provenance_status":provenance.get('status'),
              "retrieved_at":provenance.get('retrieved_at',data.get('retrieved_at')),
              "retrieved_date":provenance.get('retrieved_date'),
              "coverage_complete":coverage_complete,
              "source_checks_complete":data.get('source_checks_complete',False)}
    header=table(['Source / coverage','Value'],[[k,cell(v)] for k,v in metadata.items()])
    body=table(["Security","Previous shares","Current shares","Change","Change (%)","Current reported-value weight (%)","Observation"],
               [[x["security"],fmt(x["previous_shares"],0),fmt(x["current_shares"],0),fmt(x["share_change"],0),fmt(x['share_change_pct']),fmt(x['current_reported_value_weight_pct']),x["classification"]] for x in result])
    dates=table(['Security','Previous reporting date','Current reporting date','Previous filing date','Current filing date','Previous accepted','Current accepted'],
                [[x['security'],x['previous_reporting_date'],x['current_reporting_date'],x['previous_filing_date'],x['current_filing_date'],x['previous_accepted_date'],x['current_accepted_date']] for x in result])
    sources=table(['Security','Previous source','Current source'],[[x['security'],x['previous_source'],x['current_source']] for x in result])
    values=table(['Security','Previous reported value','Current reported value','Value change (%)','Previous weight (%)','Current weight (%)'],[[x['security'],fmt(x['previous_value']),fmt(x['current_value']),fmt(x['reported_value_change_pct']),fmt(x['previous_reported_value_weight_pct']),fmt(x['current_reported_value_weight_pct'])] for x in result])
    splits=table(['Security','Raw share change','Split-adjusted change','Ratio','Source'],[[x['security'],fmt(x['share_change'],0),fmt(x['split_adjusted_share_change'],0),x['split_adjustment']['ratio'],x['split_adjustment']['source']] for x in result if x.get('split_adjustment')])
    return {"kind":"institutional","positions":result,"metadata":metadata,"source_checks":data.get('source_checks',[]),"warnings":warnings,
            "markdown":"# Institutional ownership research\n\n"+header+"\n\n"+body+'\n\n## Reported values (separate from share changes)\n\n'+values+'\n\n## Sourced corporate-action adjustments\n\n'+splits+"\n\n## Dates and original-source locators\n\n"+dates+"\n\n"+sources+"\n\n## Interpretation limits\n\n"+"\n".join("- "+w for w in warnings)}

report = institutional

def holders(data):
    if data.get('amendments_unresolved'):raise ValueError('Unresolved holder amendments; comparison stopped.')
    seen=set();output=[]
    for x in rows(data['holders']):
        cik=x.get('cik') or x.get('holderCik')
        if not cik:raise ValueError('Holder CIK missing; cannot distinguish managers.')
        key=(str(cik).lstrip('0'),identity(x))
        if key in seen:raise ValueError('Repeated holder/security; reconcile pages and filings first.')
        seen.add(key);shares=quantity(x.get('sharesNumber',x.get('shares')));old=x.get('lastSharesNumber');old=quantity(old) if old is not None else None
        check=data.get('filing_checks',{}).get(str(cik).lstrip('0'),{})
        filed=x.get('filingDate');date=x.get('date');late=bool(filed and date and (dt.date.fromisoformat(filed[:10])-dt.date.fromisoformat(date[:10])).days>60)
        output.append(dict(cik=str(cik),manager=x.get('investorName',x.get('name')),identity=list(key[1]),shares=shares,previous_shares=old,share_change=shares-old if old is not None else None,date=date,filing_date=filed,accepted_at=x.get('acceptedDate') or check.get('accepted_at'),source=x.get('link') or x.get('finalLink') or check.get('source'),form=check.get('form',x.get('form')),late_filing_flag=late,market_value=number(x.get('marketValue',x.get('value')))))
    warnings=['Reported holder observations, not a complete real-time ownership register.','Vendor average-price/performance fields are estimates; no disclosed cost basis or audited returns are inferred.']
    if not data.get('coverage_complete'):warnings.append('Holder pagination and complete investor coverage remain unverified.')
    if any(not x['form'] for x in output):warnings.append('Some holder form types/amendments remain unknown; do not infer trades from current/prior analytics.')
    if any(x['late_filing_flag'] or x['form']=='13F-HR/A' for x in output):warnings.append('Late-dated or amended holder filing present; inspect original amendment scope before interpreting changes. A timing flag is not a legal deadline determination.')
    markdown='# Reported institutional holders\n\n'+table(['Manager','CIK','Reporting date','Filing date','Shares','Reported change'],[[x['manager'],x['cik'],x['date'],x['filing_date'],fmt(x['shares'],0),fmt(x['share_change'],0)] for x in output])+'\n\n'+'\n'.join('- '+w for w in warnings)+'\n'
    markdown+='\n\n## Filing evidence\n\n'+table(['Manager','Security class / share type / option','Accepted','Form','Late-dated flag','Source'],[[x['manager'],' / '.join(x['identity'][1:]),x['accepted_at'],x['form'],x['late_filing_flag'],x['source']] for x in output])
    summary=data.get('positions_summary')
    if summary:markdown+='\n\n## Provider stock-wide summary (separate scope)\n\n'+table(['Field','Value'],[[k,v] for k,v in summary.items()])+ '\n\nProvider aggregates may count options and amended/overlapping managers differently. Do not sum this sample into the aggregate or treat ownershipPercent as independently reconciled beneficial ownership.\n'
    return dict(kind='holders',holders=output,positions_summary=summary,warnings=warnings,markdown=markdown)
