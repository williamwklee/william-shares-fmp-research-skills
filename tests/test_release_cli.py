"""Observable command behavior at the repository/install entry points."""
import unittest,subprocess,sys,tempfile,json
from pathlib import Path
ROOT=Path(__file__).parents[1]

class ReleaseCommands(unittest.TestCase):
 def cli(self,*args):
  return subprocess.run([sys.executable,'-B',str(ROOT/'scripts/fmp_research.py'),*map(str,args)],cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
 def test_repository_and_standalone_reports_agree(self):
  with tempfile.TemporaryDirectory() as d:
   a=Path(d)/'repository.md';b=Path(d)/'skill.md';inp=ROOT/'examples/company.json'
   p=self.cli('company','--input',inp,'--output',a);self.assertEqual(p.returncode,0,p.stderr)
   p=subprocess.run([sys.executable,'-B',str(ROOT/'skills/company-research-brief/scripts/run.py'),'--input',str(inp),'--output',str(b)],capture_output=True,text=True)
   self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(a.with_suffix('.json').read_bytes(),b.with_suffix('.json').read_bytes())
 def test_refused_inputs_write_nothing(self):
  with tempfile.TemporaryDirectory() as d:
   base=Path(d);inp=base/'empty.json';inp.write_text('{}');out=base/'missing.md'
   p=self.cli('company','--input',inp,'--output',out);self.assertEqual(p.returncode,2);self.assertFalse(out.exists());self.assertFalse(out.with_suffix('.json').exists())
   out=base/'collision.json';p=self.cli('company','--input',ROOT/'examples/company.json','--output',out);self.assertEqual(p.returncode,2);self.assertFalse(out.exists())
   out=base/'fetch.json';p=self.cli('fetch','--endpoint','income-statement','--params','{"authorization":"do-not-send"}','--output',out)
   self.assertEqual(p.returncode,2);self.assertFalse(out.exists());self.assertNotIn('do-not-send',p.stderr)
 def test_existing_output_is_preserved(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d)/'keep.md';out.write_text('preserve this')
   p=self.cli('company','--input',ROOT/'examples/company.json','--output',out)
   self.assertEqual(p.returncode,2);self.assertEqual(out.read_text(),'preserve this');self.assertFalse(out.with_suffix('.json').exists())
 def test_codex_install_alias_and_existing_install_refusal(self):
  with tempfile.TemporaryDirectory() as d:
   base=Path(d);candidate=base/'candidate';candidate.mkdir();(candidate/'example').mkdir();(candidate/'example/SKILL.md').write_text('Example')
   (candidate/'manifest.json').write_text('[{"skill":"example"}]')
   cmd=[sys.executable,'-B',str(ROOT/'scripts/install_skills.py'),'--candidate',str(candidate),'--project',str(base/'project'),'--platform','codex']
   p=subprocess.run(cmd,capture_output=True,text=True);self.assertEqual(p.returncode,0,p.stderr)
   installed=base/'project/.agents/skills/example/SKILL.md';self.assertEqual(installed.read_text(),'Example')
   p=subprocess.run(cmd,capture_output=True,text=True);self.assertNotEqual(p.returncode,0);self.assertEqual(installed.read_text(),'Example')

if __name__=='__main__':unittest.main()
