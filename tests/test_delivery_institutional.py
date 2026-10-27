"""Independent counterexamples required by the objective/delivery audit."""
import sys,unittest,json,subprocess,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'src'))
from fmp_skills.institutional import institutional,holders

class Institutional(unittest.TestCase):
 def pos(self,n,**kw):return dict(symbol='A',securityCusip='123456789',shares=n,value=100,**kw)
 def test_split_classification_and_both_values(self):
  r=institutional(dict(previous=[self.pos(10)],current=[self.pos(20)],split_adjustments={'123456789':{'ratio':2,'source':'https://example.org/split'}}))
  self.assertEqual(r['positions'][0]['classification'],'unchanged (split-adjusted)');self.assertEqual(r['positions'][0]['share_change'],10)
  self.assertIn('Previous reported value',r['markdown']);self.assertIn('Split-adjusted change',r['markdown'])
 def test_limit_and_original_count_guard(self):
  for check in [dict(returned_rows=100,request_limit=100),dict(source_entry_total=900,reconciled_raw_rows=100)]:
   r=institutional(dict(current=[self.pos(1)],previous=[],coverage_complete=True,coverage_checks=[check]));self.assertFalse(r['metadata']['coverage_complete'])
 def test_holder_identity_missing_repeat_and_option(self):
  p=self.pos(10,cik='001',date='2026-06-30',filingDate='2026-09-22')
  for a in [[self.pos(10)],[p,p]]:
   with self.assertRaises(ValueError):holders({'holders':a})
  r=holders({'holders':[p,dict(p,putCallShare='Put')],'filing_checks':{'1':{'form':'13F-HR/A','source':'https://example.org/amendment','accepted_at':'2026-09-22'}}})
  self.assertEqual(len(r['holders']),2);self.assertTrue(r['holders'][0]['late_filing_flag']);self.assertIn('13F-HR/A',r['markdown']);self.assertIn('https://example.org/amendment',r['markdown'])
 def test_unresolved_holder_amendment_stops(self):
  with self.assertRaises(ValueError):holders({'holders':[],'amendments_unresolved':True})

if __name__=='__main__':unittest.main()
