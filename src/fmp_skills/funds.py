import re
from collections import defaultdict
from .common import number,fmt,rows,cell,table

def fund_index(records):
    weights=defaultdict(float);excluded=[];total=0.0;symbol_fallbacks=[];securities={};updates=set()
    for x in rows(records):
        if x.get('updatedAt'):updates.add(x['updatedAt'])
        w=number(x.get("weightPercentage"))
        if w is None: excluded.append({"name":x.get("name"),"weight":None,"reason":"missing weight"});continue
        total+=w;name=str(x.get("name",""));isin=str(x.get('isin') or '').strip().upper();cusip=str(x.get('securityCusip') or x.get('cusip') or '').strip().upper()
        if isin and cusip and isin[:2] in ('US','CA') and len(isin)==12 and isin[2:11]!=cusip:raise ValueError('ISIN and CUSIP disagree; do not match this security.')
        ident='CUSIP:'+cusip if cusip else 'CUSIP:'+isin[2:11] if len(isin)==12 and isin[:2] in ('US','CA') else 'ISIN:'+isin if isin else None
        if not ident and x.get('asset') and x.get('exchange') and x.get('currency'):
            ident='SYMBOL:'+str(x['exchange'])+':'+str(x['currency'])+':'+str(x['asset']);symbol_fallbacks.append(ident)
        kind=str(x.get('assetType','')).upper()
        derivative=kind in ('ETF','FUND','MUTUAL_FUND','OPTION','FUTURE','FUTURES','CASH','COLLATERAL') or (kind not in ('EQUITY','STOCK','COMMON_STOCK') and bool(re.search(r"\bfuture\b|\bfutures\b|\boption\b|\bcollateral\b|\bcash\b|\bpending dividend|\bETF\b|\bFUND\b|MONEY MKT|MONEY MARKET",name,re.I)))
        if not ident or w<0 or derivative:
            excluded.append({"name":name,"weight":w,"reason":"unidentified, negative, cash/derivative or nested-fund position"});continue
        weights[str(ident)]+=w
        securities[str(ident)]={'name':name,'symbol':x.get('asset'),'issuer_id':x.get('issuerCik'),'isin':isin or None,'cusip':cusip or None}
        if x.get('updatedAt'):updates.add(x['updatedAt'])
    return {"weights":dict(weights),"excluded":excluded,"total_weight":total,
            "comparable_weight":sum(weights.values()),
            "symbol_fallbacks":symbol_fallbacks,
            "securities":securities,'provider_update_timestamps':sorted(updates),
            "excluded_net_weight":sum(x['weight'] for x in excluded if x['weight'] is not None),
            "excluded_gross_weight":sum(abs(x["weight"]) for x in excluded if x["weight"] is not None)}

def funds(data):
    a,b=fund_index(data["fund_a"]),fund_index(data["fund_b"])
    common=sorted(set(a["weights"])&set(b["weights"]))
    overlap=sum(min(a["weights"][k],b["weights"][k]) for k in common)
    warnings=["Overlap is sum of the minimum original percentage weights over comparable identified positive holdings; no renormalisation.",
              "Cash, negative, unidentified and derivative entries are separately excluded; this is not full economic exposure.",
              "Provider updatedAt is not assumed to be the holdings effective date; snapshots may differ."]
    for label,item in [('A',a),('B',b)]:
        if abs(item['total_weight']-100)>2:warnings.append('Fund '+label+': supplied weights are not near100%; coverage, leverage or units require review.')
        if any(x['weight'] is None for x in item['excluded']):warnings.append('Fund '+label+': some excluded weights are unknown; gross excluded weight is incomplete.')
        if item['symbol_fallbacks']:warnings.append('Fund '+label+': exchange/currency-qualified symbol fallback used; ISIN/CUSIP matches preferred.')
    if not data.get('effective_date_a') or not data.get('effective_date_b'):warnings.append('One or both holdings effective dates are unknown; overlap compares supplied snapshots only.')
    elif data['effective_date_a']!=data['effective_date_b']:warnings.append('Holdings effective dates differ; not a same-date comparison.')
    contributions=sorted([{'security':k,'fund_a_weight':a['weights'][k],'fund_b_weight':b['weights'][k],'overlap':min(a['weights'][k],b['weights'][k])} for k in common],key=lambda x:(-x['overlap'],x['security']))
    for x in contributions:x.update(a['securities'][x['security']])
    combined=None
    if data.get('allocation_pct') is not None:
        allocation=data['allocation_pct'];pa=number(allocation.get('fund_a'));pb=number(allocation.get('fund_b'))
        if pa is None or pb is None or min(pa,pb)<0 or pa+pb>100.000001:raise ValueError('Allocations must be nonnegative percentage points summing to at most100.')
        combined={k:(a['weights'].get(k,0)*pa+b['weights'].get(k,0)*pb)/100 for k in sorted(set(a['weights'])|set(b['weights']))}
        warnings.append('Allocation look-through covers identified direct securities only; residual allocation and excluded exposures remain separate.')
    body=table(["Measure","Fund A","Fund B"],[
        ["Supplied total weight (%)",fmt(a["total_weight"]),fmt(b["total_weight"])],
        ["Comparable identified weight (%)",fmt(a["comparable_weight"]),fmt(b["comparable_weight"])],
        ["Excluded gross weight (%)",fmt(a["excluded_gross_weight"]),fmt(b["excluded_gross_weight"])],
        ["Excluded net weight (%)",fmt(a["excluded_net_weight"]),fmt(b["excluded_net_weight"])]])
    concentration={label:sum(sorted(item['weights'].values(),reverse=True)[:10]) for label,item in [('fund_a',a),('fund_b',b)]}
    labels={'fund_a':data.get('fund_a_label','Fund A'),'fund_b':data.get('fund_b_label','Fund B')}
    dates=table(['Fund','Label','Effective date','Provider updates'],[[k,labels[k],data.get('effective_date_a' if k=='fund_a' else 'effective_date_b'),', '.join(item['provider_update_timestamps']) or None] for k,item in [('fund_a',a),('fund_b',b)]])
    exclusions=table(['Fund','Position','Original weight (%)','Reason'],[[labels[k],x['name'],fmt(x['weight']),x['reason']] for k,item in [('fund_a',a),('fund_b',b)] for x in item['excluded']])
    allocation='' if combined is None else '\n\n## Allocation-weighted identified direct holdings\n\n'+table(['Identifier','Name','Symbol','Portfolio weight (%)'],[[k,(a['securities'].get(k) or b['securities'][k])['name'],(a['securities'].get(k) or b['securities'][k])['symbol'],fmt(v)] for k,v in sorted(combined.items(),key=lambda x:-x[1])])
    detail=table(['Identifier','Name','Symbol','Fund A (%)','Fund B (%)','Overlap (pp)'],[[x['security'],x['name'],x['symbol'],fmt(x['fund_a_weight']),fmt(x['fund_b_weight']),fmt(x['overlap'])] for x in contributions[:20]])
    return {"kind":"funds","fund_a":a,"fund_b":b,'fund_labels':labels,'top_10_identified_concentration_pct':concentration,"shared_securities":len(common),"overlap_percentage_points":overlap,'contributions':contributions,'combined_direct_security_weight_pct':combined,'effective_dates':{'fund_a':data.get('effective_date_a'),'fund_b':data.get('effective_date_b')},"warnings":warnings,
        "markdown":f"# Supplied fund snapshot overlap\n\nComparable overlap: **{overlap:.2f} percentage points**, {len(common)} shared identifiers.\n\n"+dates+'\n\n'+body+'\n\nTop10 identified concentration (original weights): Fund A '+fmt(concentration['fund_a'])+'%; Fund B '+fmt(concentration['fund_b'])+'%. Exclusions are outside this measure.\n\n## Largest comparable overlaps\n\n'+detail+'\n\n## Excluded positions\n\n'+exclusions+allocation+"\n\n"+"\n".join("- "+w for w in warnings)}

report = funds
