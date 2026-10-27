import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'src'))
from fmp_skills.filings import resolve_filings,collect_pages,identity,quantity
from fmp_skills.institutional import institutional
from fmp_skills.common import fmt

class FilingRules(unittest.TestCase):
 def pos(self,n,**kw):return dict(securityCusip='037833100',symbol='AAPL',titleOfClass='COM',sharesType='SH',shares=n,value=n*10,**kw)
 def filing(self,key,shares,amend=False,kind=None):return dict(accession=key,accepted_at=key,is_amendment=amend,amendment_type=kind,holdings=[self.pos(shares)])
 def test_restatement_replaces_original(self):
  r=resolve_filings([self.filing('1',100),self.filing('2',120,True,'RESTATEMENT')]);self.assertEqual(sum(x['shares'] for x in r),120)
 def test_new_holdings_adds_without_replaying_original(self):
  b=self.filing('2',25,True,'ADD NEW HOLDINGS');b['holdings'][0]['securityCusip']='OTHER'
  self.assertEqual(sum(x['shares'] for x in resolve_filings([self.filing('1',100),b])),125)
 def test_unknown_amendment_stops(self):
  with self.assertRaisesRegex(ValueError,'Unresolved'):resolve_filings([self.filing('1',100),self.filing('2',120,True,None)])
 def test_duplicate_amendment_rows_stops(self):
  with self.assertRaisesRegex(ValueError,'duplicate'):resolve_filings([self.filing('1',100),self.filing('2',100,True,'ADD NEW HOLDINGS')])
 def test_split_adjustment_preserves_reported_counts(self):
  r=institutional(dict(previous=[self.pos(100)],current=[self.pos(200)],split_adjustments={'037833100':{'ratio':2,'source':'https://example.org/split'}}))['positions'][0]
  self.assertEqual(r['share_change'],100);self.assertEqual(r['split_adjusted_share_change'],0)
 def test_page_end_and_repeated_page_are_distinct(self):
  data,receipt=collect_pages(lambda p:[self.pos(100)] if p==0 else []);self.assertEqual(len(data),1);self.assertEqual(len(receipt),2)
  with self.assertRaisesRegex(ValueError,'Repeated page'):collect_pages(lambda p:[self.pos(100)])
 def test_page_cap_is_not_completeness(self):
  with self.assertRaisesRegex(ValueError,'limit'):collect_pages(lambda p:[self.pos(p+1)],max_pages=2)
 def test_security_types_are_distinct(self):
  a=self.pos(1);b=dict(a,putCallShare='Put');self.assertNotEqual(identity(a),identity(b))
  with self.assertRaises(ValueError):identity(dict(a,sharesType='USD'))
 def test_negative_or_missing_shares_refused(self):
  for v in [-1,None,True,'NaN']:
   with self.assertRaises(ValueError):quantity(v)
 def test_large_share_counts_remain_exact(self):
  self.assertEqual(quantity('9007199254740993'),9007199254740993);self.assertEqual(fmt(9007199254740993,0),'9,007,199,254,740,993')
 def test_mixed_managers_and_reversed_periods_refused(self):
  for a,b in [(self.pos(1,cik='1'),self.pos(1,cik='2')),(self.pos(1,date='2026-03-31'),self.pos(1,date='2026-06-30'))]:
   with self.assertRaises(ValueError):institutional({'current':[a],'previous':[b]})
 def test_weights_use_supplied_13f_value(self):
  a=self.pos(10);b=dict(self.pos(30),securityCusip='OTHER',symbol='OTHER')
  r=institutional({'current':[a,b],'previous':[]});weights={x['security']:x['current_reported_value_weight_pct'] for x in r['positions']}
  self.assertEqual(weights['AAPL'],25);self.assertEqual(weights['OTHER'],75)
if __name__=='__main__':unittest.main()
