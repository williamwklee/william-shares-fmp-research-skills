import importlib.util,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location("fmp",Path(__file__).parents[1]/"scripts/fmp_research.py")
fmp=importlib.util.module_from_spec(spec);spec.loader.exec_module(fmp)

class Reports(unittest.TestCase):
 def pos(self,s,v=100,**kw):return {"symbol":"A","securityCusip":"X","titleOfClass":"COM","sharesType":"SH","shares":s,"value":v,**kw}
 def test_value_is_not_buying(self):
  a=fmp.institutional({"current":[self.pos(10,120)],"previous":[self.pos(10,100)]})
  self.assertEqual(a["positions"][0]["classification"],"shares unchanged")
  self.assertEqual(a["positions"][0]["share_change"],0)
 def test_missing_is_not_zero(self):
  with self.assertRaises(ValueError):fmp.changes([self.pos(None)],[self.pos(10)])
 def test_duplicates_and_options_are_separate(self):
  r=fmp.changes([self.pos(7),self.pos(3),self.pos(2,putCallShare="Put")],[self.pos(10)])
  self.assertEqual(len(r),2);self.assertEqual(sum(x["current_shares"] or 0 for x in r),12)
 def test_new_is_observation_not_trade(self):
  r=fmp.institutional({"current":[self.pos(10)],"previous":[]})
  self.assertEqual(r["positions"][0]["classification"],"first observed")
  self.assertTrue(any("unverified" in w for w in r["warnings"]))
 def test_dates_source_and_unknown_are_preserved(self):
  r=fmp.institutional({'current':[self.pos(10,date='2025-06-30',filingDate='2025-08-14',acceptedDate='2025-08-14T16:05:04',link='https://example.org/filing')],'previous':[self.pos(10)],'provenance':{'retrieved_at':'2025-09-01'}})
  self.assertEqual(r['positions'][0]['current_reporting_date'],'2025-06-30')
  self.assertEqual(r['positions'][0]['current_filing_date'],'2025-08-14')
  self.assertEqual(r['positions'][0]['current_accepted_date'],'2025-08-14T16:05:04');self.assertEqual(r['positions'][0]['current_source'],'https://example.org/filing')
  self.assertIsNone(r['positions'][0]['previous_reporting_date'])
  self.assertIn('not available',r['markdown'])
  self.assertEqual(r['metadata']['retrieved_at'],'2025-09-01')
 def test_identifier_fallback_and_symbol_change_are_visible(self):
  a=fmp.institutional({'current':[{'symbol':'NEW','securityCusip':'X','shares':10},{'symbol':'ONLY','shares':2}],'previous':[{'symbol':'OLD','securityCusip':'X','shares':10}]})
  self.assertTrue(any('CUSIP missing' in w for w in a['warnings']))
  self.assertTrue(any('Symbol changed' in w for w in a['warnings']))
 def holdings(self,x,w,name="Stock"):return {"asset":x,"securityCusip":x,"weightPercentage":w,"name":name}
 def test_overlap_independent_expected_value(self):
  r=fmp.funds({"fund_a":[self.holdings("A",60),self.holdings("B",40)],
               "fund_b":[self.holdings("A",25),self.holdings("C",75)]})
  self.assertEqual(r["overlap_percentage_points"],25)
 def test_disjoint_zero(self):
  self.assertEqual(fmp.funds({"fund_a":[self.holdings("A",100)],"fund_b":[self.holdings("B",100)]})["overlap_percentage_points"],0)
 def test_cash_and_negative_exclusions_are_gross(self):
  r=fmp.fund_index([self.holdings("",3,"CASH COLLATERAL"),self.holdings("",-3,"CONTRA FUTURE"),self.holdings("A",100)])
  self.assertEqual(r["excluded_gross_weight"],6);self.assertEqual(r["comparable_weight"],100)
 def test_zero_baseline_and_currency_mismatch(self):
  r=fmp.company({"income":[{"date":"2025-06-30","period":"Q2","reportedCurrency":"USD","revenue":0,"netIncome":5}],
                 "balance":[{"date":"2025-06-30","period":"Q2","reportedCurrency":"EUR","totalDebt":9}]})
  self.assertIsNone(r["metrics"]["net_margin_pct"]);self.assertNotIn("totalDebt",r["metrics"])
 def test_forecast_sorted_nearest_not_provider_order(self):
  r=fmp.company({"income":[{"date":"2025-06-30","revenue":100}],"as_of":"2026-01-01",
                "estimates":[{"date":"2030-01-01"},{"date":"2027-01-01"}]})
  self.assertEqual(r["next_available_forecast"]["date"],"2027-01-01")
 def test_earnings_missing_text_refused(self):
  with self.assertRaises(ValueError):fmp.earnings({"current":[{}],"previous":[{}]})
 def test_earnings_locators_and_no_invented_verdict(self):
  x={"year":2025,"period":"Q1","content":"Operator: Welcome to our quarterly company conference call. We expect growth next quarter."}
  r=fmp.earnings({"current":[dict(x,period='Q2')],"previous":[x]})
  self.assertTrue(r["calls"]["current"]["passages"][0]["locator"].startswith("current:P"))
  self.assertNotIn("sentiment",r)
if __name__=="__main__":unittest.main()

