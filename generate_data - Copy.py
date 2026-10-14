"""Generate reproducible, entirely fictional Adobe Channel Intelligence demo data.
Run: python generate_data.py
Standard library only. Dates are relative to the execution date.
"""
import csv, random
from pathlib import Path
from datetime import date, timedelta

rng = random.Random(20261014)
OUT = Path(__file__).resolve().parent / 'data'
OUT.mkdir(parents=True, exist_ok=True)
TODAY = date.today()

def iso(d): return d.isoformat()
def write(name, rows, fields):
    with (OUT / name).open('w', newline='', encoding='utf-8') as f:
        writer=csv.DictWriter(f, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
    print(f'{name}: {len(rows)} rows')

def save(name, rows):
    write(name, rows, list(rows[0]))

countries=['US','CA','GB','IN','AU']
offers=[('ADOBE-ACROBAT-PRO','Acrobat Pro'),('ADOBE-CC-ALL','Creative Cloud All Apps'),('ADOBE-PHOTOSHOP','Photoshop'),('ADOBE-ILLUSTRATOR','Illustrator'),('ADOBE-EXPRESS','Adobe Express')]
resellers=[]; mappings=[]
for i in range(1,101):
    rid=f'AR-{i:04d}'; irid=f'IMR-{i:04d}'; country=countries[(i-1)%len(countries)]
    resellers.append(dict(reseller_id=rid,reseller_name=f'Demo Partner {i:03d}',country=country,status='ACTIVE' if i%11 else 'INACTIVE',created_date=iso(TODAY-timedelta(days=rng.randint(90,1000)))))
    mappings.append(dict(reseller_id=rid,ingram_reseller_id=irid,country=country))
save('adobe_resellers.csv',resellers);save('ingram_reseller_mapping.csv',mappings)

customers=[]
for i in range(1,501):
    r=resellers[(i-1)%100]
    customers.append(dict(customer_id=f'AC-{i:05d}',reseller_id=r['reseller_id'],customer_name=f'Demo Customer {i:04d}',country=r['country'],status='ACTIVE'))
save('adobe_customers.csv',customers)

subs=[]; adobe_orders=[]; ingram_orders=[]; pending=[]; recommendations=[]
sub_num=0; order_num=0
# Explicit lifecycle scenarios; never infer missed renewal from date alone.
outcomes=['UPCOMING','COMPLETED','PROCESSING','ACTION_REQUIRED','GRACE_PERIOD','NOT_RENEWED_EXPIRED','INVESTIGATION_REQUIRED','ACTIVE_FUTURE']
for customer in customers:
    cid=customer['customer_id']; rid=customer['reseller_id']; irid=mappings[int(rid[-4:])-1]['ingram_reseller_id']
    for j in range(2):
        sub_num+=1; sid=f'SUB-{sub_num:06d}'
        offer_id,product=offers[(sub_num-1)%len(offers)]
        outcome=outcomes[(sub_num-1)%len(outcomes)]
        qty=rng.randint(3,80)
        if outcome=='UPCOMING': renewal=TODAY+timedelta(days=rng.randint(1,30))
        elif outcome=='ACTIVE_FUTURE': renewal=TODAY+timedelta(days=rng.randint(91,350))
        elif outcome=='GRACE_PERIOD': renewal=TODAY-timedelta(days=rng.randint(1,10))
        elif outcome=='COMPLETED': renewal=TODAY-timedelta(days=rng.randint(1,45))
        elif outcome=='PROCESSING': renewal=TODAY-timedelta(days=rng.randint(1,10))
        else: renewal=TODAY-timedelta(days=rng.randint(15,90))
        status='EXPIRED' if outcome=='NOT_RENEWED_EXPIRED' else 'ACTIVE'
        auto_renew=outcome in ('COMPLETED','PROCESSING','ACTIVE_FUTURE') and rng.random()<0.75
        subs.append(dict(subscription_id=sid,customer_id=cid,offer_id=offer_id,product_name=product,current_quantity=qty,renewal_date=iso(renewal),auto_renew=str(auto_renew).lower(),renewed_quantity=qty if outcome=='COMPLETED' else 0,status=status,renewal_outcome=outcome))
        # Completed renewals have actual completed orders. Processing renewals have pending orders.
        if outcome in ('COMPLETED','PROCESSING'):
            order_num+=1; oid=f'AO-{order_num:06d}'; st='COMPLETED' if outcome=='COMPLETED' else 'PROCESSING'
            order_date=renewal-timedelta(days=2) if outcome=='COMPLETED' else renewal+timedelta(days=1)
            adobe_orders.append(dict(adobe_order_id=oid,customer_id=cid,subscription_id=sid,order_type='RENEWAL',order_date=iso(order_date),offer_id=offer_id,quantity=qty,status=st))
            ingram_orders.append(dict(ingram_order_id=f'IO-{order_num:06d}',ingram_reseller_id=irid,customer_id=cid,adobe_order_id=oid,offer_id=offer_id,order_date=iso(order_date),quantity=qty,status='INVOICED' if st=='COMPLETED' else 'PENDING',invoiced_amount=round(qty*240,2) if st=='COMPLETED' else 0,currency='USD'))
        # Historical NEW orders establish reseller purchase activity.
        if j==0:
            for k in range(3):
                order_num+=1; oid=f'AO-{order_num:06d}'; d=TODAY-timedelta(days=rng.randint(10,540))
                q=rng.randint(1,qty)
                adobe_orders.append(dict(adobe_order_id=oid,customer_id=cid,subscription_id=sid,order_type='NEW',order_date=iso(d),offer_id=offer_id,quantity=q,status='COMPLETED'))
                ingram_orders.append(dict(ingram_order_id=f'IO-{order_num:06d}',ingram_reseller_id=irid,customer_id=cid,adobe_order_id=oid,offer_id=offer_id,order_date=iso(d),quantity=q,status='INVOICED',invoiced_amount=round(q*240,2),currency='USD'))
        if len(pending)<80 and sub_num%11==0:
            pending.append(dict(customer_id=cid,reseller_id=rid,subscription_id=sid,offer_id=offer_id,pending_quantity=rng.randint(1,20),detected_date=iso(TODAY-timedelta(days=rng.randint(1,35))),reconciliation_status='OPEN'))
        if len(recommendations)<100 and sub_num%9==0:
            recommendations.append(dict(recommendation_id=f'REC-{len(recommendations)+1:04d}',customer_id=cid,subscription_id=sid,offer_id=offer_id,recommendation_type=rng.choice(['SEAT_EXPANSION','UPSELL','CROSS_SELL']),suggested_quantity=rng.randint(2,15),confidence=rng.choice(['HIGH','MEDIUM']),source='SYNTHETIC_DEMO'))

save('adobe_subscriptions.csv',subs)
save('adobe_orders.csv',adobe_orders)
save('ingram_orders.csv',ingram_orders)
save('adobe_open_acquisitions.csv',pending)
save('adobe_recommendations.csv',recommendations)
prices=[]
for r in mappings:
    for idx,(offer,_) in enumerate(offers):
        prices.append(dict(offer_id=offer,ingram_reseller_id=r['ingram_reseller_id'],currency='USD',reseller_unit_price=[180,600,240,300,120][idx],price_period='ANNUAL',effective_date=iso(TODAY-timedelta(days=30))))
save('ingram_prices.csv',prices)
print('All data is synthetic. Annual USD prices are invented for demonstration and not Adobe or Ingram pricing.')
