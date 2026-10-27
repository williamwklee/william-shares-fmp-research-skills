import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'src'))
from fmp_skills.earnings import earnings

class Rules(unittest.TestCase):
 def call(self,period,text,**kw):return dict(symbol='TEST',year=2025,period=period,content=text,**kw)
 def test_late_guidance_and_original_spans_are_kept(self):
   text='CEO: '+('We expect growth. '*22)+'CFO: Our guidance is withdrawn.'
   r=earnings({'previous':[self.call('Q1','CEO: We expect stable demand for the following fiscal quarter.')],'current':[self.call('Q2',text)]})
   self.assertGreater(len(r['calls']['current']['passages']),18)
   self.assertTrue(any('withdrawn' in p['text'] for p in r['calls']['current']['passages']))
   for p in r['calls']['current']['all_passages']:self.assertEqual(text[p['start_character']:p['end_character']],p['text'])
 def test_no_numeric_guidance_is_not_invented(self):
   r=earnings({'previous':[self.call('Q1','CEO: Demand remains uncertain and we provide no numerical guidance.')],'current':[self.call('Q2','CEO: Demand is uncertain and we still provide no numerical guidance.')]})
   self.assertNotIn('guidance_change',r);self.assertIn('not a sentiment',r['warnings'][0])
 def test_same_period_and_cross_company_refused(self):
   a=self.call('Q1','CEO: Welcome to our earnings call, where we discuss our results.')
   for b in [a,dict(a,symbol='OTHER',period='Q2')]:
    with self.assertRaises(ValueError):earnings({'previous':[a],'current':[b]})
if __name__=='__main__':unittest.main()
