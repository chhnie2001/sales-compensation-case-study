"""Run the public synthetic example with standard-library Python only."""
import argparse, json, os, shutil, subprocess, sys
from pathlib import Path
from generate_demo import make_data
ROOT=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'runs/demo');a=p.parse_args()
r=a.output.resolve()
if r.exists():raise SystemExit('Choose a new --output directory; existing runs are never overwritten.')
(r/'source').mkdir(parents=True);(r/'working').mkdir()
source=json.dumps(make_data(),indent=2)+'\n'
(r/'source/synthetic_data.json').write_text(source)
(r/'working/source_data.json').write_text(source)
(r/'working/source_coverage.json').write_text(json.dumps(dict(complete_through='2026-06-30',basis='Synthetic demonstration coverage, not actual employer data')))
env=dict(os.environ,CLIPBOARD_CASE_ROOT=str(r),PYTHONDONTWRITEBYTECODE='1')
subprocess.run([sys.executable,str(ROOT/'src/calculate.py'),'--month','2026-06'],env=env,check=True)
reps=json.loads((r/'working/rep_calculation.json').read_text())
summary={'dataset':'SYNTHETIC ONLY','month':'2026-06','representatives':len(reps),'accounts':4,'current_usd':round(sum(x['commission_usd'] for x in reps),6),'repriced_usd':round(sum(x['repriced_usd'] for x in reps),6),'delta_usd':round(sum(x['repricing_delta'] for x in reps),6),'not_actual_case_results':True}
(r/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
lines=['# Synthetic demonstration results','','These numbers are generated from wholly invented inputs, not the original assessment and not actual payroll.','','| Representative | Current USD | Repriced USD | Local payout | Currency |','|---|---:|---:|---:|---|']
for x in reps:lines.append(f"| {x['name']} | {x['commission_usd']:.2f} | {x['repriced_usd']:.2f} | {x['commission_local']:.2f} | {x['currency']} |")
lines += ['',f"Total current: **${summary['current_usd']:,.2f}**. Total repriced: **${summary['repriced_usd']:,.2f}**. Delta: **${summary['delta_usd']:,.2f}**.",'','Repricing changes SMB AE marginal tier multipliers to 1.3× / 1.5×. Other rules remain fixed. This is an isolated scenario, not a recommendation for a real employer.']
(r/'REPORT.md').write_text('\n'.join(lines)+'\n')
print(json.dumps(summary,indent=2))
