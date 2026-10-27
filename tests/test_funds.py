import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'src'))
from fmp_skills.funds import funds

class Rules(unittest.TestCase):
 def test_cusip_and_us_isin_join(self):
   r=funds({'fund_a':[{'isin':'US0378331005','weightPercentage':60,'name':'Example'}],'fund_b':[{'securityCusip':'037833100','weightPercentage':25,'name':'Example'}]})
   self.assertEqual(r['overlap_percentage_points'],25)
 def test_inconsistent_identifiers_refused(self):
   with self.assertRaises(ValueError):funds({'fund_a':[{'isin':'US0378331005','securityCusip':'BAD','weightPercentage':60}],'fund_b':[]})
 def test_unqualified_symbols_excluded_and_allocations_applied(self):
   a=[{'securityCusip':'AAA','weightPercentage':60,'name':'Alpha'},{'asset':'NOID','weightPercentage':40,'name':'Unknown'}]
   b=[{'securityCusip':'AAA','weightPercentage':20,'name':'Alpha'},{'securityCusip':'BBB','weightPercentage':80,'name':'Beta'}]
   r=funds({'fund_a':a,'fund_b':b,'allocation_pct':{'fund_a':50,'fund_b':50}})
   self.assertEqual(r['combined_direct_security_weight_pct']['CUSIP:AAA'],40);self.assertEqual(r['fund_a']['excluded_gross_weight'],40)
 def test_cash_derivatives_and_nested_funds_are_not_equities(self):
   r=funds({'fund_a':[{'securityCusip':'ABC','name':'Example ETF','weightPercentage':100}],'fund_b':[]})
   self.assertEqual(r['fund_a']['comparable_weight'],0)
if __name__=='__main__':unittest.main()
