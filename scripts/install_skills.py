"""Install an already built candidate into a chosen isolated project scope."""
from pathlib import Path
import argparse,shutil,json
def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--project',type=Path,required=True);p.add_argument('--platform',choices=['claude','codex','chatgpt'],required=True);a=p.parse_args()
 manifest=json.loads((a.candidate/'manifest.json').read_text(encoding='utf-8'));target=a.project/('.claude/skills' if a.platform=='claude' else '.agents/skills');target.mkdir(parents=True,exist_ok=True)
 for entry in manifest:
  dest=target/entry['skill']
  if dest.exists():raise SystemExit('Existing installation: choose another project; no overwrite.')
  shutil.copytree(a.candidate/entry['skill'],dest)
 print(json.dumps({'platform':a.platform,'skills':len(manifest),'path':str(target)}))
if __name__=='__main__':main()
