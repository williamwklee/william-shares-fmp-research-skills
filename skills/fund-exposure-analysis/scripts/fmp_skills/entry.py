"""Small standalone skill runner, using only Python's standard library."""
from pathlib import Path
import argparse,json,sys,datetime
from .api import fetch

def write_new(path,text):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as f:f.write(text)

def run(report,extra_modes=None):
    p=argparse.ArgumentParser(description='FMP research: connector snapshot or explicit direct API fetch.')
    source=p.add_mutually_exclusive_group(required=True);source.add_argument('--input',type=Path);source.add_argument('--fetch',help='Exact stable REST path; requires your own FMP_API_KEY environment variable')
    p.add_argument('--params',default='{}');p.add_argument('--output',type=Path,required=True);p.add_argument('--mode',choices=['report',*(extra_modes or {})],default='report');a=p.parse_args()
    if a.output.exists() or (not a.fetch and a.output.with_suffix('.json').exists()):p.error('Output already exists; choose a new filename.')
    if not a.fetch and a.output.suffix.lower()=='.json':p.error('Use a Markdown output filename; .json is reserved for the companion data.')
    try:
        if a.fetch:
            params=json.loads(a.params)
            if not isinstance(params,dict) or any(str(k).lower().strip() in {'apikey','api_key','token','authorization'} for k in params):raise ValueError('Parameters must be an object without credentials.')
            result=dict(provider='FMP',endpoint=a.fetch,parameters=params,retrieved_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),data=fetch(a.fetch,params))
            write_new(a.output,json.dumps(result,ensure_ascii=False,indent=2));print('Saved read-only FMP response; no credential metadata.');return
        data=json.loads(a.input.read_text(encoding='utf-8-sig'));fn=(extra_modes or {}).get(a.mode,report);result=fn(data);result['provenance']=data.get('provenance',{'status':'Source provenance not provided.'})
        missing=[k for k in ['provider','endpoint','parameters','retrieved_at'] if k not in result['provenance']]
        if missing:
            warning='Source provenance incomplete: missing '+', '.join(missing)+'. This report cannot establish a complete live retrieval trail.'
            result.setdefault('warnings',[]).append(warning);result['markdown']+='\n\n- '+warning+'\n'
        write_new(a.output.with_suffix('.json'),json.dumps(result,ensure_ascii=False,indent=2));write_new(a.output,result['markdown']);print(json.dumps({'kind':result['kind'],'output':str(a.output),'warnings':len(result.get('warnings',[]))}))
    except KeyError as e:
        print('FMP research failed: Required input field missing: '+str(e.args[0]),file=sys.stderr);raise SystemExit(2)
    except (ValueError,RuntimeError,TypeError,OSError) as e:
        print('FMP research failed: '+str(e),file=sys.stderr);raise SystemExit(2)
