"""Hand-calculated synthetic controls; no original case fixtures."""
import importlib.util,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class DemoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.run_dir=Path(cls.tmp.name)/'demo'
        subprocess.run([sys.executable,str(ROOT/'run_demo.py'),'--output',str(cls.run_dir)],check=True,capture_output=True)
        os.environ['CLIPBOARD_CASE_ROOT']=str(cls.run_dir)
        spec=importlib.util.spec_from_file_location('engine',ROOT/'src/calculate.py');cls.m=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.m)
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup();os.environ.pop('CLIPBOARD_CASE_ROOT',None)
    def test_independent_hand_calculated_payouts(self):
        _,_,reps,_=self.m.calculate()
        expected={'H1':644,'H2':120,'H3':304,'H4':29.4,'H5':67.4}
        self.assertEqual(len(reps),5)
        for r in reps:self.assertAlmostEqual(r['commission_usd'],expected[r['hr_id']])
        # Alpha: 1000*.1 + 1000*.1*1.5 + 1970*.1*2 = 644.
        # Beta: (20*80-50 + 15*100)*.08 + 60 = 304.
        # Lead: (3970+1000)*.01 + (3050+490)*.005 = 67.4.
    def test_repriced_and_fx(self):
        _,_,reps,_=self.m.calculate();by={x['hr_id']:x for x in reps}
        self.assertAlmostEqual(by['H1']['repriced_usd'],525.5)
        self.assertAlmostEqual(by['H2']['commission_local'],96)
        self.assertAlmostEqual(by['H4']['commission_local'],23.52)
    def test_account_event_reconciliation(self):
        a,e,r,_=self.m.calculate();self.assertAlmostEqual(sum(x['ae_credited'] for x in a),sum(x['credited_revenue'] for x in e))
        self.assertAlmostEqual(sum(x['commission_usd'] for x in r),1164.8)
    def test_no_duplicate_opportunity_credit(self):
        a,_,_,_=self.m.calculate();b=next(x for x in a if x['crm_account_id']=='SYN-B')
        self.assertEqual(b['closed_won_count'],2);self.assertEqual(b['go_live'],'2026-04-15');self.assertEqual(b['am_existing'],1550)
        a,_,_,_=self.m.calculate(duplicate_opps=True);b=next(x for x in a if x['crm_account_id']=='SYN-B');self.assertEqual(b['am_existing'],3100)
    def test_denied_credit_not_deducted(self):
        a,_,_,_=self.m.calculate();b=next(x for x in a if x['crm_account_id']=='SYN-B');self.assertEqual(b['approved_month_credits'],50)
        a,_,_,_=self.m.calculate(include_denied=True);b=next(x for x in a if x['crm_account_id']=='SYN-B');self.assertEqual(b['approved_month_credits'],175)
    def test_window_closures(self):
        a,e,_,_=self.m.calculate();b=next(x for x in a if x['crm_account_id']=='SYN-B');d=next(x for x in a if x['crm_account_id']=='SYN-D')
        self.assertEqual(b['F2_improvement_half'],120);self.assertEqual(d['F3_improvement_half'],250)
        self.assertTrue(any(x['window']=='F3' and x['recognition_date']=='2026-06-29' and x['raw_credit']==250 for x in e))
    def test_ramp_floor(self):
        _,_,r,_=self.m.calculate();r=next(x for x in r if x['hr_id']=='H2')
        self.assertTrue(r['ramping']);self.assertAlmostEqual(r['ramp_floor'],1000);self.assertEqual(r['production'],750);self.assertAlmostEqual(r['paid_credit'],1000)
    def test_gtm_posted_vs_worked(self):
        a,_,_,_=self.m.calculate();c=next(x for x in a if x['crm_account_id']=='SYN-C');self.assertEqual(c['posted_june'],15);self.assertEqual(c['worked_june'],7);self.assertEqual(c['ae_credited'],750)
        a,_,_,_=self.m.calculate(gtm_worked=True);c=next(x for x in a if x['crm_account_id']=='SYN-C');self.assertEqual(c['ae_credited'],350)
    def test_reject_overwriting_run(self):
        p=subprocess.run([sys.executable,str(ROOT/'run_demo.py'),'--output',str(self.run_dir)],capture_output=True,text=True)
        self.assertNotEqual(p.returncode,0);self.assertIn('never overwritten',p.stderr)
    def test_reject_future_month_without_data(self):
        p=subprocess.run([sys.executable,str(ROOT/'src/calculate.py'),'--month','2026-07'],capture_output=True,text=True)
        self.assertNotEqual(p.returncode,0);self.assertIn('worked-shift extract ends',p.stderr)
    def test_duplicate_keys_rejected(self):
        self.m.ROSTER.append(dict(self.m.ROSTER[0]))
        try:
            with self.assertRaisesRegex(ValueError,'duplicate'):self.m.validate_source()
        finally:self.m.ROSTER.pop()
if __name__=='__main__':unittest.main()
