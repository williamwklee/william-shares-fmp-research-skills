import re,hashlib
from .common import number,fmt,rows,cell,table

def passages(text):
    return [x.strip() for x in re.split(r"(?<=[.!?])\s+|\n+",text) if x.strip()]

def earnings(data):
    output={};warnings=[]
    for label in ("previous","current"):
        records=rows(data[label])
        if len(records)!=1: raise ValueError("Supply exactly one transcript for each requested fiscal period.")
        x=records[0]
        if not isinstance(x.get("content"),str) or len(x["content"])<40: raise ValueError("Missing or insufficient transcript text.")
        selected=[];all_passages=[];cursor=0;speaker=None;section='prepared/unknown'
        for i,p in enumerate(passages(x["content"]),1):
            start=x['content'].find(p,cursor);cursor=start+len(p)
            match=re.match(r'^([A-Za-z][A-Za-z .\-\'’]{1,90}):\s*',p)
            if match:speaker=match.group(1)
            if re.search(r'question.and.answer|first question|next question|take questions',p,re.I):section='Q&A'
            passage={'locator':f'{label}:P{i:04}','text':p,'speaker':speaker,'section':section,'start_character':start,'end_character':cursor}
            all_passages.append(passage)
            if re.search(r"\bguidance\b|\boutlook\b|\bexpect\b|\bexpected\b|\bforecast\b|\bmargin\b|\bdemand\b|\brevenue\b|\bEPS\b|\btariff\b|\brefund\b|foreign.exchange|\bsupply\b|\bmemory\b|\brisk\b",p,re.I):
                selected.append(passage)
        output[label]={"symbol":x.get("symbol"),"period":x.get("period",x.get("quarter")),"year":x.get("year",x.get("fiscalYear")),
                       "date":x.get("date"),"passages":selected,"all_passages":all_passages,"full_characters":len(x["content"]),'content_sha256':hashlib.sha256(x['content'].encode()).hexdigest(),'speaker_parsing':'speaker labels carried when recognised; unknown remains unknown','source_complete':bool(x.get('source_complete',False))}
        unknown=sum(p['speaker'] is None for p in all_passages);output[label]['unlabelled_passages']=unknown
        if not x.get('source_complete'):warnings.append(label+': PARTIAL — source completeness not established; length alone cannot detect truncation.')
        if unknown:warnings.append(label+': PARTIAL — '+str(unknown)+' passage(s) have no recognised speaker; attribution is uncertain.')
        if x.get('truncated'):warnings.append(label+': PARTIAL — input is explicitly marked truncated.')
    if output['current']['symbol'] and output['previous']['symbol'] and output['current']['symbol']!=output['previous']['symbol']:raise ValueError('Calls refer to different companies.')
    periods=[(v['year'],str(v['period'])) for v in output.values()]
    if all(x[0] is not None and x[1]!='None' for x in periods) and periods[0]==periods[1] and not data.get('allow_same_period_comparison'):raise ValueError('Same fiscal call period supplied twice; select distinct calls or explicitly compare versions.')
    before=output['previous']['date'];after=output['current']['date']
    if before and after and before>=after and not data.get('allow_same_period_comparison'):raise ValueError('Current call date must be later than previous call date.')
    body=table(["Call","Fiscal period","Date","Relevant passage locators"],
               [[k,f'{v["year"]} {v["period"]}',v["date"],", ".join(p["locator"] for p in v["passages"])] for k,v in output.items()])
    return {"kind":"earnings","calls":output,
            "status":"PARTIAL" if warnings else "source-complete input; parsing still requires review",
            "warnings":["Passage selection is deterministic retrieval, not a sentiment verdict or verified guidance change.",
                        "The skill must compare meanings, horizons, units and qualifications and cite the source passages; absent guidance is not inferred.",
                        "Current analyst estimates do not establish historical consensus.",*warnings],
            "markdown":"# Earnings-call comparison evidence\n\n"+('PARTIAL\n\n' if warnings else '')+'\n'.join('- '+w for w in warnings)+'\n\n'+body+"\n\n## Located evidence\n\n"+'\n\n'.join('### '+label+' '+p['locator']+'\n\n'+p['text'] for label,v in output.items() for p in v['passages'])+"\n\nThe companion JSON retains all passage spans and source hashes. The assistant compares meaning, fiscal horizon, units, GAAP/non-GAAP definitions and qualifications, citing before/after locators. Retrieval tags do not establish raised/lowered guidance. Missing or ambiguous source/speaker coverage must be disclosed.\n"}

report = earnings
