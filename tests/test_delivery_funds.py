"""Independent counterexamples required by the objective/delivery audit."""
import sys,unittest,json,subprocess,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'src'))
from fmp_skills.funds import funds

class Funds(unittest.TestCase):
 def row(self,key,w,**kw):return dict(securityCusip=key,asset=key,name='Example',weightPercentage=w,**kw)
 def test_identical_funds_and_different_dates(self):
  a=[self.row('123456789',60),self.row('987654321',40)]
  r=funds(dict(fund_a=a,fund_b=a,effective_date_a='2025-03-31',effective_date_b='2025-06-30'))
  self.assertEqual(r['overlap_percentage_points'],100);self.assertEqual(r['shared_securities'],2);self.assertTrue(any('dates differ' in w for w in r['warnings']))
 def test_distinct_share_classes_and_duplicate_rows(self):
  a=[self.row('123456789',20),self.row('123456789',10),self.row('987654321',70)]
  a[0]['asset']=a[1]['asset']='GOOG';a[2]['asset']='GOOGL'
  b=[self.row('123456789',5),self.row('987654321',95)]
  r=funds(dict(fund_a=a,fund_b=b));self.assertEqual(r['shared_securities'],2);self.assertEqual(r['fund_a']['weights']['CUSIP:123456789'],30);self.assertEqual(r['overlap_percentage_points'],75)
 def test_symbol_fallback_and_bad_allocation(self):
  a=[dict(asset='SYN',exchange='XNYS',currency='USD',name='Example',weightPercentage=100)]
  self.assertEqual(funds(dict(fund_a=a,fund_b=a))['overlap_percentage_points'],100)
  with self.assertRaises(ValueError):funds(dict(fund_a=a,fund_b=a,allocation_pct=dict(fund_a=70,fund_b=40)))
 def test_coverage_and_typed_cash_named_equity(self):
  r=funds(dict(fund_a=[self.row('123456789',30,assetType='EQUITY')],fund_b=[]))
  self.assertTrue(any('not near100' in w for w in r['warnings']))
  a=self.row('123456789',100,assetType='EQUITY');a['name']='Cash Technology Company'
  self.assertEqual(funds(dict(fund_a=[a],fund_b=[a]))['overlap_percentage_points'],100)

if __name__=='__main__':unittest.main()
