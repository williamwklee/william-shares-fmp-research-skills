"""Explicit 13F filing selection, security identity and coverage rules."""
from decimal import Decimal,InvalidOperation
import re,json
from .common import rows

def identity(x):
    cusip=x.get('securityCusip') or x.get('cusip');symbol=x.get('symbol')
    if not cusip and not symbol:raise ValueError('Position has neither CUSIP nor symbol.')
    kind=str(x.get('sharesType') or 'SH').upper().strip();option=str(x.get('putCallShare') or x.get('putCall') or '').upper().strip()
    if option in ('SHARE','SHARES','SH'):option=''
    if kind not in ('SH','PRN') or option not in ('','PUT','CALL'):raise ValueError('Unknown share/principal or put/call type.')
    return (str(cusip or 'SYMBOL:'+str(symbol)).upper().strip(),re.sub(r'\s+','',str(x.get('titleOfClass',x.get('typeOfSecurity',''))).upper()),kind,option)

def quantity(value):
    if value is None or isinstance(value,bool):raise ValueError('Missing shares; no inferred zero.')
    try:d=Decimal(str(value))
    except InvalidOperation:raise ValueError('Invalid shares.') from None
    if not d.is_finite() or d<0:raise ValueError('Shares must be finite and nonnegative.')
    return int(d) if d==d.to_integral_value() else float(d)

def resolve_filings(filings):
    """Restatements replace; explicitly identified new-entry amendments add."""
    if not filings:raise ValueError('No filings supplied.')
    out=[];seen=set();base=False
    for f in sorted(filings,key=lambda x:(str(x.get('accepted_at',x.get('filing_date',''))),str(x.get('accession','')))):
        accession=f.get('accession')
        if not accession or accession in seen:raise ValueError('Missing or duplicate filing accession.')
        seen.add(accession);data=rows(f.get('holdings',[]));amend=f.get('is_amendment')
        if amend is False:
            if base:raise ValueError('Multiple original filings; reconcile before comparing.')
            out=list(data);base=True
        elif amend is True:
            kind=str(f.get('amendment_type','')).upper().strip()
            if kind=='RESTATEMENT':out=list(data);base=True
            elif kind in ('ADD NEW HOLDINGS','NEW HOLDINGS') and base:
                existing={json.dumps(x,sort_keys=True) for x in out}
                if any(json.dumps(x,sort_keys=True) in existing for x in data):raise ValueError('Amendment additions duplicate existing rows; unresolved.')
                out+=data
            else:raise ValueError('Unresolved amendment type/base; comparison stopped.')
        else:raise ValueError('Unknown amendment status; comparison stopped.')
    return out

def validate_quarters(current,previous):
    ciks=set();dates=[]
    for records in [previous,current]:
        ds={x['date'] for x in records if x.get('date')}
        ciks.update(str(x['cik']).lstrip('0') or '0' for x in records if x.get('cik'))
        if len(ds)>1:raise ValueError('Mixed reporting dates in one quarter extract.')
        dates.append(next(iter(ds)) if ds else None)
    if len(ciks)>1:raise ValueError('Mixed investment managers; comparison stopped.')
    if all(dates) and dates[0]>=dates[1]:raise ValueError('Current quarter must be later than previous quarter.')

def collect_pages(fetch_page,max_pages=20):
    """For documented paginated endpoints only. Refuse repeated pages or truncation."""
    out=[];seen=set();receipts=[]
    for page in range(max_pages):
        response=fetch_page(page);data=rows(response)
        receipt={'page':page,'records':len(data)};receipts.append(receipt)
        if not data:return out,receipts
        fingerprint=json.dumps(sorted(json.dumps(x,sort_keys=True) for x in data))
        if fingerprint in seen:raise ValueError('Repeated page; endpoint may ignore pagination. No completeness claim.')
        seen.add(fingerprint);out+=data
        if isinstance(response,dict) and response.get('isLast') is True:return out,receipts
    raise ValueError('Page limit reached without end marker; coverage incomplete.')
