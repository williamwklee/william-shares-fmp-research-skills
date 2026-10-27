"""Independent counterexamples required by the objective/delivery audit."""
import sys,unittest,json,subprocess,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'src'))
from fmp_skills.funds import funds
from fmp_skills.company import company

class Company(unittest.TestCase):
 def base(self):return dict(as_of='2026-10-26',income=[dict(symbol='SYN',date='2026-06-27',period='Q3',reportedCurrency='USD',revenue=120,netIncome=12),dict(symbol='SYN',date='2025-06-28',period='Q3',reportedCurrency='USD',revenue=100,netIncome=10)])
 def test_ended_pending_and_future_forecasts(self):
  d=self.base();d['estimates_period']='annual';d['estimates']=[dict(date='2027-09-27',numAnalystsEps=30),dict(date='2026-09-27',numAnalystsEps=29)]
  r=company(d);self.assertEqual(r['pending_report_estimate']['date'],'2026-09-27');self.assertEqual(r['next_future_estimate']['date'],'2027-09-27');self.assertEqual(r['financial_trend']['revenue_change_pct'],20)
 def test_annual_cutoff_cannot_backdate_quarterly_expectations(self):
  d=self.base();d.update(estimates_period='quarter',latest_reported_annual_date='2025-09-27',estimates=[dict(date='2025-12-27'),dict(date='2026-09-27'),dict(date='2026-12-27')])
  r=company(d);self.assertEqual(r['pending_report_estimate']['date'],'2026-09-27');self.assertEqual(r['next_future_estimate']['date'],'2026-12-27');self.assertTrue(any('Annual reporting cutoff ignored' in w for w in r['warnings']))
 def test_stale_annual_cutoff_cannot_override_newer_statement(self):
  d=self.base();d.update(as_of='2027-02-01',latest_reported_annual_date='2025-09-27',estimates_period='annual',income=[dict(d['income'][0],date='2026-12-27',period='Q1')],estimates=[dict(date='2026-09-27'),dict(date='2027-09-27')])
  r=company(d);self.assertIsNone(r['pending_report_estimate']);self.assertEqual(r['next_available_forecast']['date'],'2027-09-27')
 def test_quarter_estimates_with_annual_actuals_and_multiple_ended_horizons(self):
  d=self.base();d.update(income=[dict(d['income'][0],date='2025-09-27',period='FY')],estimates_period='quarter',estimates=[dict(date='2025-12-27'),dict(date='2026-03-27'),dict(date='2026-09-27'),dict(date='2026-12-27')])
  r=company(d);self.assertIsNone(r['pending_report_estimate']);self.assertEqual(len(r['unresolved_ended_estimates']),3);self.assertTrue(any('Pending estimate period unresolved' in w for w in r['warnings']))
  d['income'][0]['period']='Q4';r=company(d);self.assertIsNone(r['pending_report_estimate'])
  d['income'][0]['period']='FY';d['estimates']=[dict(date='2026-09-27'),dict(date='2026-12-27')];self.assertIsNone(company(d)['pending_report_estimate'])
 def test_unknown_estimate_frequency_does_not_invent_pending_period(self):
  d=self.base();d['estimates']=[dict(date='2026-09-27'),dict(date='2027-09-27')]
  r=company(d);self.assertIsNone(r['pending_report_estimate']);self.assertEqual(len(r['unresolved_ended_estimates']),1)
 def test_missing_statement_date_has_explicit_error(self):
  d=self.base();d['income']=[dict(revenue=100)]
  with self.assertRaisesRegex(ValueError,'statement date is required'):company(d)
 def test_missing_conflicting_and_incompatible_segments(self):
  d=self.base();r=company(d);self.assertTrue(any('Segments absent' in w for w in r['warnings']));self.assertTrue(any('partial company' in w for w in r['warnings']))
  d['segments']=[dict(date='2026-06-27',period='Q3',reportedCurrency='USD',data=dict(A=99))];self.assertTrue(any('does not reconcile' in w for w in company(d)['warnings']))
  d['segments'][0]['reportedCurrency']='EUR';self.assertTrue(any('incompatible' in w for w in company(d)['warnings']))
 def test_identity_and_double_counting(self):
  d=self.base();d['balance']=[dict(symbol='OTHER',date='2026-06-27',period='Q3',reportedCurrency='USD')]
  with self.assertRaises(ValueError):company(d)
  d.pop('balance');d['modules']={'funds':funds({'fund_a':[dict(securityCusip='123456789',asset='SYN',name='Example',weightPercentage=25)],'fund_b':[]})}
  r=company(d);self.assertEqual(r['company_fund_exposure'][0]['weight_pct'],25);self.assertNotIn('total_ownership',r);self.assertIn('not summed ownership',r['markdown'])

if __name__=='__main__':unittest.main()
