import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'src'))
from fmp_skills.company import company

class Rules(unittest.TestCase):
 def test_future_financials_not_backdated(self):
   with self.assertRaises(ValueError):company({'income':[{'date':'2026-06-30','revenue':1}],'as_of':'2026-01-01'})
 def test_later_filing_and_comparable_trend(self):
   with self.assertRaises(ValueError):company({'income':[{'date':'2026-06-30','filingDate':'2026-07-31','revenue':1}],'as_of':'2026-07-01'})
   r=company({'income':[{'date':'2026-06-30','period':'Q2','reportedCurrency':'USD','revenue':120,'netIncome':12},{'date':'2025-06-30','period':'Q2','reportedCurrency':'USD','revenue':100,'netIncome':10}]})
   self.assertEqual(r['financial_trend']['revenue_change_pct'],20);self.assertEqual(r['financial_trend']['net_income_change_pct'],20)
 def test_news_cutoff_and_insider_transaction_types(self):
   r=company({'income':[{'date':'2025-06-30','period':'Q2','reportedCurrency':'USD','revenue':100,'netIncome':10}],'as_of':'2025-07-01','news':[{'publishedDate':'2025-07-02','title':'Future'}],'insiders':[{'transactionDate':'2025-06-30','transactionType':'M-Exempt','securitiesTransacted':10,'url':'https://example.org/form4'}]})
   self.assertEqual(r['news'],[]);self.assertEqual(r['insiders'][0]['type'],'exercise/conversion')
   self.assertEqual(r['insiders'][0]['source'],'https://example.org/form4')
if __name__=='__main__':unittest.main()
