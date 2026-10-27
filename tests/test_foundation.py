import sys,unittest,tempfile,subprocess,json,io
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parents[1]/'src'))
from fmp_skills.api import fetch

class Foundation(unittest.TestCase):
 def test_http_success_error_envelope_is_failure(self):
  with patch.dict('os.environ',{'FMP_API_KEY':'TEST'}),patch('urllib.request.urlopen',return_value=io.BytesIO(b'{"Error Message":"Unavailable"}')):
   with self.assertRaises(RuntimeError):fetch('income-statement',{'symbol':'SYN'})
 def test_provenance_warning_and_json_collision_refusal(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);inp=root/'input.json';inp.write_text('{"value":1}')
   code="from fmp_skills.entry import run; run(lambda x:dict(kind='test',warnings=[],markdown='Test report'))"
   env=dict(__import__('os').environ,PYTHONPATH=str(Path(__file__).parents[1]/'src'))
   out=root/'report.md';p=subprocess.run([sys.executable,'-B','-c',code,'--input',str(inp),'--output',str(out)],capture_output=True,text=True,env=env)
   self.assertEqual(p.returncode,0,p.stderr);d=json.loads(out.with_suffix('.json').read_text());self.assertTrue(any('provenance incomplete' in w for w in d['warnings']))
   collision=root/'collision.json';p=subprocess.run([sys.executable,'-B','-c',code,'--input',str(inp),'--output',str(collision)],capture_output=True,text=True,env=env)
   self.assertEqual(p.returncode,2);self.assertFalse(collision.exists())
if __name__=='__main__':unittest.main()
