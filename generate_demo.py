"""Generate a new fictional example; does not read or transform assessment data."""
import datetime as dt
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent

def make_data():
    d = {}
    d['1. Sales Roster'] = [['name','hr_id','crm_owner_id'], ['Demo AE Alpha','H1','O1'], ['Demo AE Ramp','H2','O2'], ['Demo AM Beta','H3','O3'], ['Demo AM Gamma','H4','O4'], ['Demo Sales Lead','H5','O5']]
    d['2. HR Export'] = [['hr_id','Current Role','Start Date','End Date','Current Role Start Date','Manager - ID','Country Code'],
        ['H1','SMB Account Executive','2025-01-01',None,'2025-01-01','H5','US'],
        ['H2','ENT Account Executive','2026-06-01',None,'2026-06-01','H5','GB'],
        ['H3','SMB Account Manager','2025-01-01',None,'2025-01-01','H5','US'],
        ['H4','ENT Account Manager','2025-01-01',None,'2025-01-01','H5','GB'],
        ['H5','Head of Sales & AM','2025-01-01',None,'2025-01-01',None,'US']]
    d['3. Exchange Rates'] = [['Country Code','Code','1 USD ='],['US','USD',1],['GB','GBP',.8]]
    roles=['SMB Account Executive','ENT Account Executive','SMB Account Manager','ENT Account Manager']
    d['4. Ramp Terms'] = [['Role','Start Date Ramp Terms']] + [[r,'50% for first 30 days; 75% for next 30 days'] for r in roles]
    d['5. Compensation'] = [['Role','Monthly Quota Target','Standard Payout','Metric I','Standard Payout 2'],
        [roles[0],2000,.10,'New Customer Net Revenue',0],[roles[1],2000,.12,'New Customer Net Revenue',0],
        [roles[2],2000,.08,'Existing Customer Net Revenue',0],[roles[3],2000,.06,'Existing Customer Net Revenue',0],
        ['Head of Sales & AM',0,.01,'New Customer Net Revenue',.005]]
    d['6. Accelerators'] = [['Role','Note','Unused','lower','upper','multiplier1','Unused2','Unused3','multiplier2'],
        [roles[0],'synthetic',None,1000,2000,1.5,None,None,2], [roles[1],'synthetic',None,1000,2000,1.4,None,None,1.8],
        [roles[2],'synthetic',None,60,None,None,None,None,None],[roles[3],'synthetic',None,45,None,None,None,None,None]]
    d['7. Opportunity to ID Mapping']=[['crm_account_id','app_account_id','billing_account_id']]+[[a,'APP-'+a,'BILL-'+a] for a in ['SYN-A','SYN-B','SYN-C','SYN-D']]
    h=['opportunity_id','crm_account_id','account_type','net_terms','segment','charge_rate_per_shift','pay_rate_per_shift','crm_owner_id','closed_by_owner_id','opportunity_stage','closed_won_date','effective_start_date']
    d['8. Opportunity Export']=[h,
        ['DEAL-A','SYN-A','Standard',15,'SMB',200,100,'O3','O1','Closed Won','2026-05-25','2026-06-01'],
        ['DEAL-B','SYN-B','Standard',30,'SMB',180,100,'O3','O1','Closed Won','2026-04-01','2026-04-15'],
        ['DEAL-B-DUP','SYN-B','Standard',30,'SMB',180,100,'O3','O1','Closed Won','2026-05-01','2026-05-15'],
        ['DEAL-C','SYN-C','GTM',30,'ENT',200,130,'O4','O2','Closed Won','2026-04-25','2026-05-01'],
        ['DEAL-D','SYN-D','Standard',30,'SMB',200,100,'O3','O1','Closed Won','2026-03-20','2026-04-01']]
    shifts=[['shift_id','app_account_id','shift_posted_date','worked_shift','shift_worked_date','account_first_worked_shift_date']]
    def add(account,anchor,start,count,worked_count=None):
        for i in range(count):
            day=(dt.date.fromisoformat(start)+dt.timedelta(days=i)).isoformat()
            worked=worked_count is None or i<worked_count
            shifts.append(['SHIFT-%04d'%len(shifts),'APP-'+account,day,worked,day if worked else None,anchor])
    add('SYN-A','2026-06-01','2026-06-01',30)
    add('SYN-B','2026-04-15','2026-05-01',10);add('SYN-B','2026-04-15','2026-06-01',20)
    add('SYN-C','2026-06-05','2026-06-05',15,7)
    add('SYN-D','2026-04-01','2026-04-01',5);add('SYN-D','2026-04-01','2026-05-01',10);add('SYN-D','2026-04-01','2026-06-01',15)
    d['9. App Export']=shifts
    d['10. Billing Export']=[['billing_account_id','billing_month','ticket_status','credit_amount'],['BILL-SYN-B','2026-06','approved',50],['BILL-SYN-B','2026-06','denied',125],['BILL-SYN-B','2026-05','approved',0]]
    return d

if __name__=='__main__':
    (ROOT/'source').mkdir(exist_ok=True)
    (ROOT/'source/synthetic_data.json').write_text(json.dumps(make_data(),indent=2)+'\n')
    print('Generated fictional inputs. No original assessment data was read.')
