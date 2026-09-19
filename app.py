import math
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
from statsmodels.tsa.holtwinters import SimpleExpSmoothing

st.set_page_config(page_title="SupplyPulse | Inventory Control Tower", page_icon="◈", layout="wide")
st.markdown("""
<style>
.block-container{padding-top:1.2rem;max-width:1500px}
.hero{padding:1.2rem 1.4rem;border-radius:18px;background:linear-gradient(135deg,#0b2a24,#14532d);color:white;margin-bottom:1rem}
.hero h1{margin:0;font-size:2rem}.hero p{margin:.35rem 0 0;color:#d7f8df}
.badge{display:inline-block;background:#16a34a;color:white;padding:.25rem .6rem;border-radius:999px;font-size:.75rem;font-weight:700}
</style>
""",unsafe_allow_html=True)
Z={.90:1.2816,.95:1.6449,.99:2.3263}

@st.cache_data
def generate():
    rng=np.random.default_rng(19); n_sku=500; days=365
    dates=pd.date_range(end=pd.Timestamp.today().normalize(),periods=days)
    sku_ids=np.arange(1,n_sku+1); categories=rng.choice(["Grocery","Beauty","Home","Electronics","Fashion","Pet","Health"],n_sku)
    cost=rng.uniform(25,1800,n_sku); price=cost*rng.uniform(1.22,2.25,n_sku); lead=rng.integers(2,22,n_sku); base=rng.lognormal(2.3,.8,n_sku)
    rows=[]
    for i,sid in enumerate(sku_ids):
        seasonal=1+.28*np.sin(np.arange(days)/365*2*np.pi+rng.random()*6.2)
        trend=np.linspace(1,rng.uniform(.88,1.12),days); demand=np.maximum(0,rng.poisson(np.maximum(base[i]*seasonal*trend,.1)))
        on=max(10,int(base[i]*lead[i]*rng.uniform(2.5,4.5)))
        for d,u in zip(dates,demand):
            on-=int(u)
            if on<base[i]*lead[i]*1.2:on+=int(base[i]*lead[i]*rng.uniform(2,4))
            rows.append([d.date(),sid,categories[i],cost[i],price[i],lead[i],int(u),max(0,on)])
    return pd.DataFrame(rows,columns=["date","sku_id","category","unit_cost","unit_price","lead_time_days","units_sold","units_on_hand"])

df=generate()
service=st.sidebar.slider("Target service level",.90,.99,.95,.01)
cats=st.sidebar.multiselect("Category",sorted(df.category.unique()),default=sorted(df.category.unique()))
view=df[df.category.isin(cats)].copy(); z=min(Z,key=lambda k:abs(k-service))
recs=[]
for sid,g in view.groupby("sku_id"):
    g=g.sort_values("date"); fc=float(g.tail(28).units_sold.mean()); sd=float(g.tail(30).units_sold.std(ddof=0)); lt=int(g.lead_time_days.iloc[-1])
    rp=fc*lt+z*sd*np.sqrt(max(lt,1)); on=float(g.units_on_hand.iloc[-1]); days=on/fc if fc>0 else np.inf
    recs.append([sid,g.category.iloc[0],g.unit_cost.iloc[-1],g.unit_price.iloc[-1],lt,fc,sd,on,days,rp,max(0,math.ceil(rp-on))])
r=pd.DataFrame(recs,columns=["sku_id","category","unit_cost","unit_price","lead_time_days","forecast_daily","demand_std","units_on_hand","days_of_stock","reorder_point","suggested_order_qty"])
r["ttm_revenue_proxy"]=r.forecast_daily*365*r.unit_price; r["inventory_value"]=r.units_on_hand*r.unit_cost
r["below_reorder"]=r.units_on_hand<r.reorder_point; r["overstock"]=r.days_of_stock>90
r["stockout_revenue_risk"]=np.maximum(r.reorder_point-r.units_on_hand,0)*r.unit_price; r["overstock_value"]=np.maximum(r.days_of_stock-90,0)*r.forecast_daily*r.unit_cost
r["abc"]=pd.qcut(r.ttm_revenue_proxy.rank(method="first",ascending=False),q=[0,.2,.5,1],labels=["A","B","C"])

st.markdown('<div class="hero"><span class="badge">SUPPLY CHAIN • INVENTORY CONTROL</span><h1>SupplyPulse — Inventory Control Tower</h1><p>Demand forecasting, ABC segmentation, reorder signals and working-capital exposure across a 500-SKU synthetic portfolio.</p></div>',unsafe_allow_html=True)
c1,c2,c3,c4,c5=st.columns(5)
c1.metric("Inventory Value",f"₹{r.inventory_value.sum()/1e7:.2f}Cr")
c2.metric("SKUs Below Reorder",f"{r.below_reorder.sum():,}")
c3.metric("Overstock Value",f"₹{r.overstock_value.sum()/1e6:.1f}M")
c4.metric("Stockout Revenue Risk",f"₹{r.stockout_revenue_risk.sum()/1e6:.1f}M")
c5.metric("Portfolio SKUs",f"{r.sku_id.nunique():,}")
st.caption(f"Data scale: {len(view):,} daily rows • {r.sku_id.nunique():,} SKUs • 365 days")

t1,t2,t3,t4=st.tabs(["Control Tower","Replenishment","Demand Analytics","Working Capital"])
with t1:
    l,m,rr=st.columns(3)
    l.plotly_chart(px.pie(r,names="abc",values="ttm_revenue_proxy",title="ABC Revenue Concentration"),use_container_width=True)
    m.plotly_chart(px.bar(r.groupby("category",as_index=False).stockout_revenue_risk.sum(),x="category",y="stockout_revenue_risk",title="Stockout Revenue Risk by Category"),use_container_width=True)
    rr.plotly_chart(px.scatter(r,x="days_of_stock",y="forecast_daily",size="inventory_value",color="abc",hover_data=["sku_id","category"],title="Demand vs Days of Stock"),use_container_width=True)
with t2:
    urgency=r[r.below_reorder].sort_values(["days_of_stock","stockout_revenue_risk"])
    st.dataframe(urgency[["sku_id","category","abc","days_of_stock","reorder_point","suggested_order_qty","stockout_revenue_risk"]],use_container_width=True,hide_index=True)
    st.download_button("Download Replenishment Plan",urgency.to_csv(index=False).encode(),"supplypulse_replenishment.csv","text/csv")
with t3:
    sku=st.selectbox("SKU",sorted(r.sku_id.unique())); g=view[view.sku_id==sku].sort_values("date")
    fit=SimpleExpSmoothing(g.units_sold.astype(float),initialization_method="estimated").fit(optimized=True); future=fit.forecast(30)
    st.plotly_chart(px.line(g.tail(90),x="date",y="units_sold",title=f"90-Day Demand History — SKU {sku}"),use_container_width=True)
    fc_df=pd.DataFrame({"date":pd.date_range(pd.to_datetime(g.date.max())+pd.Timedelta(days=1),periods=30),"forecast":future.values})
    st.plotly_chart(px.line(fc_df,x="date",y="forecast",title="30-Day Forecast"),use_container_width=True)
    rr=r[r.sku_id==sku].iloc[0]; a,b,c=st.columns(3); a.metric("Forecast / Day",f"{rr.forecast_daily:.1f}"); b.metric("Reorder Point",f"{rr.reorder_point:.0f}"); c.metric("Suggested Order",f"{rr.suggested_order_qty:,}")
with t4:
    by_cat=r.groupby("category",as_index=False).agg(inventory_value=("inventory_value","sum"),overstock_value=("overstock_value","sum"))
    st.plotly_chart(px.bar(by_cat,x="category",y=["inventory_value","overstock_value"],barmode="group",title="Working Capital by Category"),use_container_width=True)
    st.dataframe(r.sort_values("inventory_value",ascending=False)[["sku_id","category","abc","inventory_value","days_of_stock","overstock"]].head(50),use_container_width=True,hide_index=True)
