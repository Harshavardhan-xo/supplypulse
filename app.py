import math, numpy as np, pandas as pd, streamlit as st, plotly.express as px
from statsmodels.tsa.holtwinters import SimpleExpSmoothing

st.set_page_config(page_title="SupplyPulse",layout="wide")
st.title("SupplyPulse — Inventory Health & Stockout Risk")
st.caption("Synthetic 150-SKU inventory analytics dashboard.")

@st.cache_data
def make():
    rng=np.random.default_rng(42); n=150; days=365
    dates=pd.date_range(end=pd.Timestamp.today().normalize(),periods=days)
    rows=[]
    for i in range(1,n+1):
        cat=rng.choice(["Grocery","Beauty","Home","Electronics","Fashion","Pet"])
        cost=float(rng.uniform(40,1200)); price=cost*rng.uniform(1.25,2.2); lead=int(rng.integers(2,18))
        base=rng.uniform(2,35); seasonal=1+.25*np.sin(np.linspace(0,2*np.pi,days)+rng.random()*6)
        demand=np.maximum(0,rng.poisson(np.maximum(base*seasonal,.1))); on=max(5,base*lead*3)
        for d,u in zip(dates,demand):
            on-=int(u)
            if on<base*lead: on+=int(base*lead*rng.uniform(2,4))
            rows.append([d,i,cat,cost,price,lead,int(u),max(on,0)])
    return pd.DataFrame(rows,columns=["date","sku_id","category","unit_cost","unit_price","lead_time_days","units_sold","units_on_hand"])

df=make()
service=st.sidebar.slider("Service level",.90,.99,.95,.01)
cat=st.sidebar.multiselect("Category",sorted(df.category.unique()),default=sorted(df.category.unique()))
df=df[df.category.isin(cat)]
Z={.90:1.2816,.95:1.6449,.99:2.3263}; z=min(Z,key=lambda x:abs(x-service))
summary=[]
for sid,g in df.groupby("sku_id"):
    g=g.sort_values("date"); series=g.units_sold.astype(float)
    fit=SimpleExpSmoothing(series,initialization_method="estimated").fit(optimized=True)
    fc=max(float(fit.forecast(1).iloc[0]),0); sd=float(series.tail(30).std(ddof=0))
    lead=int(g.lead_time_days.iloc[0]); rp=fc*lead+z*sd*np.sqrt(lead); on=float(g.units_on_hand.iloc[-1])
    days=on/fc if fc else 0
    summary.append([sid,g.category.iloc[0],g.unit_cost.iloc[0],g.unit_price.iloc[0],lead,fc,sd,on,days,rp,max(0,math.ceil(rp-on))])
r=pd.DataFrame(summary,columns=["sku_id","category","unit_cost","unit_price","lead_time_days","forecast_daily","demand_std","units_on_hand","days_of_stock","reorder_point","suggested_order_qty"])
r["below_reorder"]=r.units_on_hand<r.reorder_point; r["overstock"]=r.days_of_stock>90
r["overstock_value"]=np.maximum(r.days_of_stock-90,0)*r.forecast_daily*r.unit_cost
r["stockout_revenue_risk"]=np.maximum(r.reorder_point-r.units_on_hand,0)*r.unit_price

c1,c2,c3,c4=st.columns(4)
c1.metric("Below Reorder",int(r.below_reorder.sum()))
c2.metric("Overstock Value",f"INR {r.loc[r.overstock,'overstock_value'].sum():,.0f}")
c3.metric("Stockout Revenue Risk",f"INR {r.loc[r.below_reorder,'stockout_revenue_risk'].sum():,.0f}")
c4.metric("SKUs Tracked",r.sku_id.nunique())
st.plotly_chart(px.bar(r.groupby("category",as_index=False).overstock_value.sum(),x="category",y="overstock_value",title="Overstock Value by Category"),use_container_width=True)
st.subheader("Reorder List")
st.dataframe(r[r.below_reorder].sort_values("days_of_stock")[["sku_id","category","days_of_stock","reorder_point","suggested_order_qty"]],use_container_width=True)

sku=st.selectbox("Inspect SKU",sorted(r.sku_id.unique()))
g=df[df.sku_id==sku].sort_values("date")
fit=SimpleExpSmoothing(g.units_sold.astype(float),initialization_method="estimated").fit(optimized=True)
future=fit.forecast(14)
fig=px.line(g.tail(60),x="date",y="units_sold",title=f"Actual Demand — SKU {sku}")
fig.add_scatter(x=pd.date_range(g.date.max()+pd.Timedelta(days=1),periods=14),y=future.values,name="Forecast")
st.plotly_chart(fig,use_container_width=True)
