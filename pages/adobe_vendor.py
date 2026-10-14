"""Leadership-ready Adobe X4V experience. All data and actions are synthetic."""
import pandas as pd
import plotly.express as px
import streamlit as st
from services.metrics import subscription_metrics, order_metrics, pending_with_values, reseller_sales_trend, renewal_worklist, opportunity_worklist, money, overdue_reseller_summary, overdue_renewal_aging
from services.workflows import create_case, list_cases, update_case, STATUSES


def metric(label, value, note=None):
    st.metric(label, value, help=note)


def render(data):
    st.title('Adobe | Channel Growth & Revenue Assurance')
    st.caption('Xvantage X4V • Leadership demonstration • Synthetic data and simulated actions')
    subs = subscription_metrics(data['subscriptions'])
    orders = order_metrics(data)
    pending = pending_with_values(data)
    opportunities = opportunity_worklist(data)
    trend = reseller_sales_trend(data)
    overdue_resellers, overdue_subscriptions = overdue_reseller_summary(data)
    renewal = renewal_worklist(data)
    cases = list_cases()
    valid_resellers = set(data['resellers'].reseller_id)
    cases = [c for c in cases if c.get('reseller_id') in valid_resellers]

    st.markdown('### Channel pulse')
    c1,c2,c3,c4 = st.columns(4)
    with c1: metric('Channel resellers', f"{len(data['resellers']):,}")
    with c2: metric('Purchasing resellers · 365d', f"{orders['purchasing_resellers']:,}")
    with c3: metric('Invoiced Adobe sales · 365d', money(orders['channel_revenue']), 'Ingram invoiced sales, not Adobe vendor revenue')
    with c4: metric('End customers', f"{data['customers'].customer_id.nunique():,}")
    c1,c2,c3,c4 = st.columns(4)
    with c1: metric('Pending partner licenses', f"{int(pending.pending_quantity.sum()):,}")
    with c2: metric('Resellers with overdue customer renewals', f"{len(overdue_resellers):,}", 'After renewal date; synthetic reconciled ACTION_REQUIRED status')
    with c3: metric('Renewals due · next 30d', f"{subs['renewals_30']:,}")
    with c4: metric('Open action cases', f"{sum(c.get('status') not in ('RESOLVED','CLOSED') for c in cases):,}")

    tabs = st.tabs(['Executive Overview','Channel Performance','Revenue Assurance','Renewal Intelligence','Growth Opportunities','Action Center'])
    with tabs[0]:
        st.subheader('Where should Adobe focus?')
        left,right = st.columns([1,1])
        with left:
            st.markdown('**Revenue assurance priorities**')
            st.info(f"{pending.customer_id.nunique()} customers have licenses pending partner order. Review and reconcile against Ingram orders before creating a new purchase.")
            st.warning(f"{len(overdue_resellers)} resellers have {subs['overdue_customers']} customers with action-required overdue renewals. This is measured after the renewal date, not by months since last purchase.")
            st.markdown('**Operational overview**')
            status_counts = data['subscriptions'].groupby('renewal_outcome').size().reset_index(name='subscriptions')
            if not status_counts.empty:
                st.plotly_chart(px.bar(status_counts, x='renewal_outcome', y='subscriptions', title='Renewal lifecycle by status'), use_container_width=True)
        with right:
            invoiced = data['ingram_orders'].loc[data['ingram_orders'].status.eq('INVOICED')].copy()
            if not invoiced.empty:
                invoiced['month'] = invoiced.order_date.dt.to_period('M').astype(str)
                monthly = invoiced.groupby('month',as_index=False).invoiced_amount.sum().tail(12)
                st.plotly_chart(px.line(monthly,x='month',y='invoiced_amount',markers=True,title='Invoiced sales trend · synthetic USD'),use_container_width=True)
            st.markdown('**Growth signals**')
            st.metric('Eligible recommendation signals',len(opportunities))
            st.metric('Active license quantities',f"{subs['active_licenses']:,}")
        st.caption('All sales, exposures, quantities and recommendations are fictional. Pending exposure is not confirmed lost revenue.')

    with tabs[1]:
        st.subheader('Reseller renewal health')
        st.caption('Reseller risk is measured ONLY after customer subscription renewal dates, with unconfirmed renewals classified as ACTION_REQUIRED. No 30/60/90-day purchase-inactivity flag is used.')
        a,b,c,d=st.columns(4)
        with a: metric('Resellers with overdue customer renewals',len(overdue_resellers))
        with b: metric('Affected customers',subs['overdue_customers'])
        with c: metric('Overdue subscriptions',len(overdue_subscriptions))
        with d: metric('Overdue license quantities',int(overdue_subscriptions.current_quantity.sum()) if not overdue_subscriptions.empty else 0)
        aging=overdue_renewal_aging(overdue_subscriptions)
        st.plotly_chart(px.bar(aging,x='aging',y='subscriptions',title='Overdue renewal aging · from subscription renewal date',labels={'aging':'Days after renewal','subscriptions':'Subscriptions'}),use_container_width=True)
        st.markdown('**Resellers requiring renewal outreach**')
        if overdue_resellers.empty:
            st.success('No resellers have action-required overdue customer renewals.')
        else:
            st.dataframe(overdue_resellers.rename(columns={'reseller_name':'Reseller','affected_customers':'Customers requiring follow-up','overdue_subscriptions':'Overdue subscriptions','overdue_licenses':'License quantities','oldest_days_overdue':'Oldest days overdue','last_renewal_date':'Earliest overdue renewal date'}).drop(columns=['reseller_id']),use_container_width=True,hide_index=True)
            selected_reseller=st.selectbox('Inspect overdue reseller',overdue_resellers.reseller_id.tolist(),format_func=lambda rid: overdue_resellers.set_index('reseller_id').loc[rid,'reseller_name'],key='inspect_overdue_reseller')
            details=overdue_subscriptions.loc[overdue_subscriptions.reseller_id.eq(selected_reseller)]
            st.dataframe(details[['customer_name','subscription_id','product_name','renewal_date','days_past_renewal','current_quantity','renewal_outcome']],use_container_width=True,hide_index=True)
            with st.form('reseller_renewal_followup'):
                note=st.text_input('Follow-up notes','Review customer renewals past their renewal dates; confirm order and grace-period status')
                if st.form_submit_button('Request reseller renewal follow-up'):
                    st.success('Created demo case '+create_case('RENEWAL_OUTREACH',None,selected_reseller,None,note,'Renewal Specialist'))
        st.markdown('**Sales performance — separate from renewal risk**')
        st.caption('Invoiced sales are shown for channel performance only. A period without new purchases does not indicate a missed renewal.')
        if not trend.empty:
            view=trend.sort_values('current_period',ascending=False).head(15)
            st.plotly_chart(px.bar(view,x='reseller_name',y='current_period',title='Top resellers by invoiced sales · last 90 days'),use_container_width=True)

    with tabs[2]:
        st.subheader('Pending partner order recovery')
        a,b,c=st.columns(3)
        with a: metric('Pending licenses',f"{int(pending.pending_quantity.sum()):,}")
        with b: metric('Affected customers',pending.customer_id.nunique())
        with c: metric('Illustrative order exposure',money(pending.estimated_value.fillna(0).sum()))
        st.caption('Exposure uses fictional Ingram reseller prices and is not verified vendor revenue or lost sales.')
        if not pending.empty:
            p=pending.copy()
            p['age_days']=(pd.Timestamp.today().normalize()-p.detected_date).dt.days
            p['age_bucket']=pd.cut(p.age_days,bins=[-10000,7,30,60,10000],labels=['0–7 days','8–30 days','31–60 days','60+ days'])
            counts=p.groupby('age_bucket',observed=False).pending_quantity.sum().reset_index()
            st.plotly_chart(px.bar(counts,x='age_bucket',y='pending_quantity',title='Pending license aging'),use_container_width=True)
            st.dataframe(p[['customer_name','reseller_name','offer_id','pending_quantity','detected_date','age_days','estimated_value','reconciliation_status']],use_container_width=True,hide_index=True)
            with st.form('pending_followup'):
                idx=st.selectbox('Exception to reconcile',p.index.tolist(),format_func=lambda i:f"{p.loc[i,'customer_name']} · {p.loc[i,'pending_quantity']} licenses")
                if st.form_submit_button('Request reconciliation'):
                    row=p.loc[idx]
                    st.success('Created demo case '+create_case('PENDING_PARTNER_ORDER',row.customer_id,row.reseller_id,row.subscription_id,f'Reconcile {row.pending_quantity} licenses for {row.offer_id}'))

    with tabs[3]:
        st.subheader('Subscription and renewal intelligence')
        a,b,c,d=st.columns(4)
        with a: metric('Due · 30 days',subs['renewals_30'])
        with b: metric('Due · 60 days',subs['renewals_60'])
        with c: metric('Due · 90 days',subs['renewals_90'])
        with d: metric('Processing renewals',subs['processing_renewals'])
        st.metric('Resellers with overdue customer renewals',len(overdue_resellers))
        st.caption('Upcoming windows are cumulative. Overdue cases use synthetic reconciled renewal outcomes, not date alone.')
        if not renewal.empty:
            dist=renewal.groupby('renewal_outcome').size().reset_index(name='subscriptions')
            st.plotly_chart(px.bar(dist,x='renewal_outcome',y='subscriptions',title='Renewal outcome distribution'),use_container_width=True)
        work=renewal_worklist(data,['ACTION_REQUIRED','INVESTIGATION_REQUIRED'])
        st.markdown('**Overdue renewals by reseller**')
        st.dataframe(overdue_resellers[['reseller_name','affected_customers','overdue_subscriptions','overdue_licenses','oldest_days_overdue']] if not overdue_resellers.empty else overdue_resellers, use_container_width=True,hide_index=True)
        st.markdown('**Action-required and investigation worklist**')
        if work.empty: st.success('No renewal exceptions in the selected scope.')
        else:
            st.dataframe(work[['customer_name','reseller_name','subscription_id','product_name','renewal_date','renewal_outcome','auto_renew']],use_container_width=True,hide_index=True)
            with st.form('renewal_followup'):
                idx=st.selectbox('Subscription for outreach',work.index.tolist(),format_func=lambda i:f"{work.loc[i,'customer_name']} · {work.loc[i,'subscription_id']}")
                if st.form_submit_button('Request renewal outreach'):
                    row=work.loc[idx]
                    st.success('Created demo case '+create_case('RENEWAL_OUTREACH',row.customer_id,row.reseller_id,row.subscription_id,'Investigate unconfirmed Adobe renewal','Renewal Specialist'))

    with tabs[4]:
        st.subheader('Customer growth and expansion')
        st.caption('Adobe-style recommendation signals joined with fictional Ingram offer pricing. These are leads, not approved orders.')
        if opportunities.empty: st.info('No eligible opportunities in this scope.')
        else:
            st.metric('Recommendation signals',len(opportunities))
            breakdown=opportunities.groupby('recommendation_type').size().reset_index(name='signals')
            st.plotly_chart(px.bar(breakdown,x='recommendation_type',y='signals',title='Growth opportunity types'),use_container_width=True)
            st.dataframe(opportunities[['customer_name','reseller_name','recommendation_type','suggested_quantity','confidence','illustrative_value']],use_container_width=True,hide_index=True)
            with st.form('growth_followup'):
                idx=st.selectbox('Opportunity to review',opportunities.index.tolist(),format_func=lambda i:f"{opportunities.loc[i,'customer_name']} · {opportunities.loc[i,'recommendation_type']}")
                if st.form_submit_button('Create growth follow-up'):
                    row=opportunities.loc[idx]
                    st.success('Created demo case '+create_case('GROWTH_OPPORTUNITY',row.customer_id,row.reseller_id,None,'Validate Adobe recommendation and reseller eligibility','Channel Account Manager'))

    with tabs[5]:
        st.subheader('Channel action center')
        if not cases: st.info('No action cases yet. Create a case from any workflow tab.')
        else:
            df=pd.DataFrame(cases)
            st.dataframe(df,use_container_width=True,hide_index=True)
            with st.form('update_action'):
                case_id=st.selectbox('Case',df.case_id.tolist())
                status=st.selectbox('New status',STATUSES)
                if st.form_submit_button('Update case'):
                    update_case(case_id,status)
                    st.success('Case updated. Refresh to see the latest case list.')
