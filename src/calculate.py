"""Auditable commission reconstruction. JSON/CSV working outputs, not a final workbook.
All source rows retain original workbook row numbers. No source files are edited.
"""
import argparse, calendar, collections, csv, datetime as dt, json, os,re,hashlib
from pathlib import Path
R=Path(os.environ.get('CLIPBOARD_CASE_ROOT',Path(__file__).resolve().parent))
D=json.loads((R/'working/source_data.json').read_text())
SOURCE_ROWS=json.loads((R/'working/source_row_numbers.json').read_text()) if (R/'working/source_row_numbers.json').exists() else {}
def date(v): return dt.date.fromisoformat(v) if v else None
def rows(name):
    a=D[name]; indices=SOURCE_ROWS.get(name) or list(range(1,len(a)+1))
    return [dict(zip(a[0],r),source_row=indices[i]) for i,r in enumerate(a[1:],1)]
def export(name,data):
    (R/'working'/f'{name}.json').write_text(json.dumps(data,default=str,ensure_ascii=False,indent=2))
    if data:
        with (R/'working'/f'{name}.csv').open('w',newline='') as f:
            fields=list(dict.fromkeys(k for row in data for k in row))
            c=csv.DictWriter(f,fieldnames=fields);c.writeheader();c.writerows(data)
ROSTER=rows('1. Sales Roster'); HR={r['hr_id']:r for r in rows('2. HR Export')}
CRM={r['crm_owner_id']:dict(r,hr=HR[r['hr_id']]) for r in ROSTER}
COMP={r['Role']:r for r in rows('5. Compensation')}
FX={r['Country Code']:r for r in rows('3. Exchange Rates')}
OPP=rows('8. Opportunity Export'); SHIFTS=rows('9. App Export'); BILL=rows('10. Billing Export')
MAP=rows('7. Opportunity to ID Mapping'); BYCRM={r['crm_account_id']:r for r in MAP}
APPCRM={r['app_account_id']:r['crm_account_id'] for r in MAP}; BILLCRM={r['billing_account_id']:r['crm_account_id'] for r in MAP}
ICS={'SMB Account Executive','ENT Account Executive','SMB Account Manager','ENT Account Manager'}
RAMP={}
for r in rows('4. Ramp Terms'):
    if r['Role'] in ICS:
        perc=re.findall(r'(\d+)%',r['Start Date Ramp Terms'])
        if len(perc)!=2:raise ValueError('Unrecognised ramp terms; review rule text before refresh: '+r['Role'])
        RAMP[r['Role']]=[int(x)/100 for x in perc]
BANDS={r[0]:dict(low=r[3],high=r[4],m1=r[5],m2=r[8]) for r in D['6. Accelerators'] if r[0] in ('SMB Account Executive','ENT Account Executive') and isinstance(r[3],(int,float))}
SPIFF={r[0]:r[3] for r in D['6. Accelerators'] if r[0] in ('SMB Account Manager','ENT Account Manager') and isinstance(r[3],(int,float))}
def group(data,key):
    g=collections.defaultdict(list)
    for r in data:g[key(r)].append(r)
    return g
OG=group(OPP,lambda r:r['crm_account_id']); SG=group(SHIFTS,lambda r:APPCRM[r['app_account_id']]); BG=group(BILL,lambda r:BILLCRM[r['billing_account_id']])
def validate_source():
    for data,key,label in [(ROSTER,'hr_id','roster HR'),(ROSTER,'crm_owner_id','roster CRM'),(rows('2. HR Export'),'hr_id','HR'),(MAP,'crm_account_id','map CRM'),(MAP,'app_account_id','map app'),(MAP,'billing_account_id','map billing'),(OPP,'opportunity_id','opportunity'),(SHIFTS,'shift_id','shift')]:
        keys=[r[key] for r in data]
        if None in keys or len(set(keys))!=len(keys):raise ValueError('Missing or duplicate source key: '+label)
    for cid,g in OG.items():
        for key in ['account_type','net_terms','segment','charge_rate_per_shift','pay_rate_per_shift','crm_owner_id','closed_by_owner_id']:
            if len({r[key] for r in g})!=1:raise ValueError(f'Conflicting account property {cid}: {key}; review before payroll')
    for cid,g in SG.items():
        if len({r['account_first_worked_shift_date'] for r in g})!=1:raise ValueError('Conflicting supplied first-worked anchor: '+cid)
        if any(bool(r['worked_shift'])!=bool(r['shift_worked_date']) for r in g):raise ValueError('Worked flag/date disagreement: '+cid)
validate_source()

def calculate(month='2026-06', *, accept_reversed=False, latest_go_live=False, duplicate_opps=False,
              terms=True, include_denied=False, half=True, incremental=True,
              ramp_dates=None, month_end_ramp=False, exclude_accounts=(), gtm_worked=False, trace_rows=False, ignore_employment=False, exclude_pre_anchor=False, carry_pre_hire=False):
    start=date(month+'-01'); days=calendar.monthrange(start.year,start.month)[1];end=start+dt.timedelta(days=days-1)
    prev=(start-dt.timedelta(days=1)).strftime('%Y-%m'); ramp_dates=ramp_dates or {}
    account=[]; events=[]; trace=[]
    for cid,opps in OG.items():
        wins=[r for r in opps if r['opportunity_stage']=='Closed Won' or (accept_reversed and r['closed_won_date'])]
        o=min(wins,key=lambda r:(r['effective_start_date'],r['opportunity_id'])) if wins else opps[0]
        live=date((max(wins,key=lambda r:r['effective_start_date']) if latest_go_live and wins else o)['effective_start_date']) if wins else None
        shifts=SG[cid]; first=date(shifts[0]['account_first_worked_shift_date']) if shifts else None
        event_start=len(events)
        owner=CRM.get(o['closed_by_owner_id']);role=owner['hr']['Current Role'] if owner else None
        rate=COMP[role]['Standard Payout'] if role in ('SMB Account Executive','ENT Account Executive') else None
        gtm=o['account_type']=='GTM'; margin=o['charge_rate_per_shift']-o['pay_rate_per_shift']
        factor=({15:1.2,30:1,45:.9,60:.7}[o['net_terms']] if terms else 1) if not gtm else 1
        convert=.03/rate if gtm and rate else 1
        ws=[0.,0.,0.]; f1month=0.; current_nr=0.; may_nr=0.; posted=0;worked=0
        current_existing=prev_existing=0.; credits=collections.defaultdict(float)
        for b in BG[cid]:
            if b['ticket_status']=='approved' or include_denied:credits[b['billing_month']]+=b['credit_amount']
        for s in shifts:
            sd=date(s['shift_worked_date']); pd=date(s['shift_posted_date'])
            if s['worked_shift'] and s['shift_worked_date'][:7]==month:current_nr+=margin;worked+=1
            if s['worked_shift'] and s['shift_worked_date'][:7]==prev:may_nr+=margin
            if s['shift_posted_date'][:7]==month:posted+=1
            metric_date=(sd if gtm_worked else pd) if gtm else sd
            eligible=(s['worked_shift'] if gtm_worked else True) if gtm else s['worked_shift']
            if exclude_pre_anchor and gtm and first and metric_date and metric_date<first:eligible=False
            value=o['charge_rate_per_shift'] if gtm else margin
            win=0
            if eligible and metric_date and first:
                age=(metric_date-first).days
                win=1 if age<30 and (gtm or age>=0) else 2 if 30<=age<60 else 3 if 60<=age<90 else 0
                if win:ws[win-1]+=value
                if win==1 and start<=metric_date<=end:
                    f1month+=value
                    if wins and cid not in exclude_accounts: events.append(dict(crm_account_id=cid,owner=o['closed_by_owner_id'],recognition_date=str(metric_date),window='F1',raw_credit=value,credited_revenue=value*factor*convert,source_row=s['source_row'],source_tab='9. App Export'))
            if trace_rows and wins and cid not in exclude_accounts:
                trace.append(dict(crm_account_id=cid,shift_source_row=s['source_row'],shift_id=s['shift_id'],ae_window=win,metric_date=str(metric_date) if metric_date else '',metric_value=value if eligible else 0,worked_june_nr=margin if s['worked_shift'] and start<=sd<=end else 0))
        f2=max(0,ws[1]-ws[0])*(.5 if half else 1);f3=max(0,ws[2]-max(ws[:2]))*(.5 if half else 1)
        for window,offset,value in [('F2',59,f2),('F3',89,f3)]:
            close=first+dt.timedelta(days=offset) if first else None
            if wins and close and start<=close<=end and cid not in exclude_accounts:
                events.append(dict(crm_account_id=cid,owner=o['closed_by_owner_id'],recognition_date=str(close),window=window,raw_credit=value,credited_revenue=value*factor*convert,source_row=o['source_row'],source_tab='8. Opportunity Export'))
        ae=sum(e['credited_revenue'] for e in events[event_start:])
        duplicate_factor=len(opps) if duplicate_opps else 1
        if duplicate_factor>1:
            for e in list(events):
                if e['crm_account_id']==cid:
                    for _ in range(duplicate_factor-1):events.append(dict(e))
            ae*=duplicate_factor
        existing=bool(live and live<start and cid not in exclude_accounts)
        retention=bool(live and live<date(prev+'-01') and cid not in exclude_accounts)
        account.append(dict(crm_account_id=cid,app_account_id=BYCRM[cid]['app_account_id'],billing_account_id=BYCRM[cid]['billing_account_id'],opportunity_rows=','.join(str(r['source_row']) for r in opps),winning_opportunity=o['opportunity_id'] if wins else '',closed_won_count=len(wins),go_live=str(live) if live else '',first_worked=str(first) if first else '',ae_owner=o['closed_by_owner_id'],am_owner=o['crm_owner_id'],account_type=o['account_type'],role=role or '',margin=margin,charge=o['charge_rate_per_shift'],terms_factor=factor,gtm_conversion=convert,W1=ws[0],W2=ws[1],W3=ws[2],F1_month=f1month,F2_improvement_half=f2,F3_improvement_half=f3,ae_credited=ae,worked_june_nr=current_nr,approved_month_credits=credits[month],am_existing=(current_nr-credits[month])*duplicate_factor if existing else 0,retention_june=(current_nr-credits[month])*duplicate_factor if retention else 0,retention_may=(may_nr-credits[prev])*duplicate_factor if retention else 0,posted_june=posted,worked_june=worked))
    reps=[]
    for r in ROSTER:
        h=HR[r['hr_id']];role=h['Current Role']; c=COMP[role];hire=date(h['Start Date']);leave=date(h['End Date']) or dt.date.max
        employed=lambda day:ignore_employment or hire<=day<=leave
        employed_days=sum(employed(start+dt.timedelta(days=i)) for i in range(days))
        rs=date(ramp_dates.get(r['name'],h['Current Role Start Date'])); isic=role in ICS
        ramp_pct=lambda day: RAMP[role][0 if (day-rs).days<30 else 1] if isic and 0<=(day-rs).days<60 and employed(day) else 0
        floor=sum(c['Monthly Quota Target']/days*ramp_pct(start+dt.timedelta(days=i)) for i in range(days)) if isic else 0
        ramping=bool(ramp_pct(end)) if month_end_ramp else any(ramp_pct(start+dt.timedelta(days=i)) for i in range(days))
        aevents=[e for e in events if e['owner']==r['crm_owner_id']]
        ae_all=sum(e['credited_revenue'] for e in aevents)
        ae_pay=sum(e['credited_revenue'] for e in aevents if employed(date(e['recognition_date'])))
        am=sum(a['am_existing'] for a in account if a['am_owner']==r['crm_owner_id'])
        # AM employment filtering uses worked-date revenue, credits recognised at month-end (explicit provisional assumption).
        am_pay=am if employed_days==days else 0
        if 0<employed_days<days and 'Account Manager' in role:
            for a in account:
                if a['am_owner']==r['crm_owner_id'] and a['go_live'] and date(a['go_live'])<start:
                    am_pay+=sum(a['margin'] for s in SG[a['crm_account_id']] if s['worked_shift'] and start<=date(s['shift_worked_date'])<=end and employed(date(s['shift_worked_date'])))
                    if employed(end):am_pay-=a['approved_month_credits']
        isae='Account Executive' in role
        production=(ae_pay if isae else am_pay) if isic else 0
        has_ramp_days=any(ramp_pct(start+dt.timedelta(days=i)) for i in range(days))
        paid_credit=(max(production,floor) if has_ramp_days else production) if isic else 0
        manager_production=(ae_all if carry_pre_hire else sum(e['credited_revenue'] for e in aevents if date(e['recognition_date'])>=hire)) if isae else am
        manager_credit=(max(manager_production,floor) if has_ramp_days else manager_production) if isic else 0
        quota=c['Monthly Quota Target']*employed_days/days
        may=sum(a['retention_may'] for a in account if a['am_owner']==r['crm_owner_id']);jun=sum(a['retention_june'] for a in account if a['am_owner']==r['crm_owner_id'])
        spiff=SPIFF[role] if role in SPIFF and not ramping and may>0 and jun>=may and employed_days>0 else 0
        def payout(m1,m2):
            if not isae or ramping:return paid_credit*c['Standard Payout']
            lo,hi=BANDS[role]['low'],BANDS[role]['high']
            if incremental:return (min(paid_credit,lo)+min(max(paid_credit-lo,0),hi-lo)*m1+max(paid_credit-hi,0)*m2)*c['Standard Payout']
            return paid_credit*c['Standard Payout']*(m2 if paid_credit>hi else m1 if paid_credit>lo else 1)
        band=BANDS.get(role,dict(m1=1,m2=1))
        commission=payout(band['m1'],band['m2'])+spiff if isic else 0
        revised=payout(1.3,1.5)+spiff if role=='SMB Account Executive' else commission
        reps.append(dict(name=r['name'],hr_id=r['hr_id'],crm_owner_id=r['crm_owner_id'],role=role,manager=h['Manager - ID'],hr_source_row=h['source_row'],role_start=str(rs),employment_days=employed_days,prorated_quota=quota,ramping=ramping,ramp_floor=floor,ae_before_employment=ae_all,ae_pay_eligible=ae_pay,am_existing=am,production=production,paid_credit=paid_credit,manager_credit=manager_credit,retention_may=may,retention_june=jun,spiff=spiff,new_rollup=0.,existing_rollup=0.,commission_usd=commission,repriced_usd=revised,currency=FX[h['Country Code']]['Code'],fx=FX[h['Country Code']]['1 USD =']))
    rh={r['hr_id']:r for r in reps}
    for ic in reps:
        if ic['role'] not in ICS:continue
        manager=ic['manager'];seen=set()
        while manager in rh:
            assert manager not in seen,'Manager cycle';seen.add(manager)
            target=rh[manager];metric='new_rollup' if 'Account Executive' in ic['role'] else 'existing_rollup'
            target[metric]+=ic['manager_credit'];manager=target['manager']
    for r in reps:
        if r['role'] not in ICS:
            c=COMP[r['role']]
            r['commission_usd']=(r['new_rollup'] if c['Metric I']=='New Customer Net Revenue' else r['existing_rollup'])*c['Standard Payout']
            if r['role']=='Head of Sales & AM':r['commission_usd']+=r['existing_rollup']*c['Standard Payout 2']
            if not r['employment_days']:r['commission_usd']=0
            r['repriced_usd']=r['commission_usd']
        r['commission_local']=r['commission_usd']*r['fx'];r['repricing_delta']=r['repriced_usd']-r['commission_usd']
    return account,events,reps,trace

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--month',default='2026-06');args=parser.parse_args()
    available=max(s['shift_worked_date'][:7] for s in SHIFTS if s['worked_shift'])
    if args.month>available:
        raise SystemExit(f'Cannot calculate {args.month}: worked-shift extract ends in {available}. Obtain refreshed source data; month label changes are insufficient.')
    coverage=json.loads((R/'working/source_coverage.json').read_text()) if (R/'working/source_coverage.json').exists() else dict(complete_through='2026-06-30',basis='Synthetic demonstration coverage')
    requested_end=date(args.month+'-01')+dt.timedelta(days=calendar.monthrange(int(args.month[:4]),int(args.month[5:]))[1]-1)
    if str(requested_end)>coverage['complete_through']:raise SystemExit('Source coverage has not been confirmed through the requested month end; refresh complete exports first.')
    a,e,r,t=calculate(args.month,trace_rows=True)
    for name,data in [('accounts',a),('credit_events',e),('rep_calculation',r),('shift_trace',t)]:export(name,data)
    (R/'working/plan_parameters.json').write_text(json.dumps(dict(ramp=RAMP,bands=BANDS,spiff=SPIFF)))
    (R/'working/run_metadata.json').write_text(json.dumps({'month':args.month,'available_worked_month':available,'source_coverage':coverage,'source_workbook':'source/synthetic_data.json','source_sha256':hashlib.sha256((R/'source/synthetic_data.json').read_bytes()).hexdigest(),'status':'reconstructed entitlement, not cash paid'}))
    print('Accounts',len(a),'events',len(e),'reps',len(r),'trace',len(t))
    print('Current-plan reconstructed USD',sum(x['commission_usd'] for x in r),'Repriced',sum(x['repriced_usd'] for x in r),'Delta',sum(x['repricing_delta'] for x in r))
    for x in sorted(r,key=lambda x:x['commission_usd'],reverse=True)[:8]:print(x['name'],x['commission_usd'],x['paid_credit'],x['new_rollup'])
