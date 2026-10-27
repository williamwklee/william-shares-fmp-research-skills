"""Build standalone skill directories/ZIPs from an explicit source whitelist."""
from pathlib import Path
import json,hashlib,shutil,argparse,zipfile
ROOT=Path(__file__).resolve().parents[1]
SKILLS={'institutional-ownership-research':'institutional','earnings-call-comparison':'earnings','fund-exposure-analysis':'funds','company-research-brief':'company'}
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists(),'Choose a new candidate version';a.output.mkdir(parents=True)
 manifest=[]
 for name,module in SKILLS.items():
  folder=a.output/name;(folder/'scripts/fmp_skills').mkdir(parents=True);(folder/'examples').mkdir();(folder/'references').mkdir()
  for src,rel in [(ROOT/'skills'/name/'SKILL.md','SKILL.md'),(ROOT/'LICENSE','LICENSE'),(ROOT/'examples'/(module+'.json'),'examples/input.json')]:shutil.copy2(src,folder/rel)
  shutil.copy2(ROOT/'examples'/(module+'-failure.json'),folder/'examples/failure.json')
  shutil.copy2(ROOT/'skills'/name/'references/input-contract.md',folder/'references/input-contract.md')
  modules=['__init__','common','api','entry',module]+(['filings'] if module=='institutional' else [])
  for m in modules:shutil.copy2(ROOT/'src/fmp_skills'/(m+'.py'),folder/'scripts/fmp_skills'/(m+'.py'))
  runner='from fmp_skills.entry import run\nfrom fmp_skills.'+module+' import report\n'
  if module=='institutional':runner+='from fmp_skills.institutional import holders\nrun(report,{"holders":holders})\n'
  else:runner+='run(report)\n'
  (folder/'scripts/run.py').write_text(runner,encoding='utf-8',newline='\n')
  zip_path=a.output/(name+'.zip')
  with zipfile.ZipFile(zip_path,'x',zipfile.ZIP_DEFLATED) as z:
   for f in sorted(folder.rglob('*')):
    if f.is_file():z.write(f,name+'/'+f.relative_to(folder).as_posix())
  files=[{'path':f.relative_to(folder).as_posix(),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in sorted(folder.rglob('*')) if f.is_file()]
  manifest.append(dict(skill=name,module=module,files=files,zip_sha256=hashlib.sha256(zip_path.read_bytes()).hexdigest()))
 (a.output/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8');print(json.dumps({'skills':4,'self_contained':True,'folder':str(a.output)}))
if __name__=='__main__':main()
