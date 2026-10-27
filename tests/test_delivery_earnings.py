"""Independent counterexamples required by the objective/delivery audit."""
import sys,unittest,json,subprocess,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'src'))
from fmp_skills.earnings import earnings

class Earnings(unittest.TestCase):
 def call(self,date,quarter,text,**kw):return dict(symbol='SYN',year=2025,period=quarter,date=date,content=text,**kw)
 def compare(self,a,b):return earnings({'previous':[self.call('2025-04-24','Q1',a)],'current':[self.call('2025-07-24','Q2',b)]})
 def test_guidance_semantics_fixtures(self):
  base='CFO: We expect revenue of USD 5 to 7 billion for the June quarter.'
  cases=[('unchanged',base),('raised','CFO: We now expect revenue of USD 8 to 10 billion for the same June quarter.'),('lowered','CFO: We now expect revenue of USD 3 to 4 billion for the same June quarter.'),('withdrawn','CFO: We withdraw our June quarter guidance because demand is uncertain.'),('mixed units','CFO: We expect revenue of USD 5000 to 7000 million for the June quarter.')]
  for label,text in cases:
   r=self.compare(base,text);self.assertTrue(r['calls']['current']['passages'],label);self.assertEqual(r['calls']['current']['all_passages'][0]['text'],text);self.assertNotIn('guidance_change',r)
 def test_fiscal_period_not_calendar_and_partiality(self):
  r=self.compare('Management has not supplied speaker labels in this partial transcript.','CFO: We expect stable demand next fiscal quarter, with no numeric guidance.')
  self.assertEqual(r['calls']['previous']['period'],'Q1');self.assertEqual(r['status'],'PARTIAL');self.assertTrue(any('no recognised speaker' in x for x in r['warnings']))
 def test_truncation_reverse_and_missing_quarter(self):
  a=self.call('2025-07-24','Q1','CFO: We expect steady demand and revenue growth next quarter.',truncated=True)
  b=self.call('2025-04-24','Q2',a['content'])
  with self.assertRaises(ValueError):earnings({'previous':[a],'current':[b]})
  with self.assertRaises(ValueError):earnings({'previous':[a],'current':[]})
  r=earnings({'previous':[b],'current':[dict(a,period='Q3')]});self.assertTrue(any('marked truncated' in x for x in r['warnings']))

if __name__=='__main__':unittest.main()
