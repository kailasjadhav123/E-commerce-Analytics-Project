"""
E-Commerce Analytics Project — Python EDA & Visualization
"""

import pandas as pd
import numpy as np
import sqlite3
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from scipy import stats
import warnings, os

warnings.filterwarnings("ignore")

# ── Paths ────────────────────
BASE    = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, "..", "data", "ecommerce.db")
FIG_DIR = os.path.join(BASE, "..", "data", "figures")
os.makedirs(FIG_DIR, exist_ok=True)

# ── Style ─────────────────────────────
PALETTE = ["#2C7BB6","#D7191C","#1A9641","#FDAE61","#ABD9E9","#F46D43"]
plt.rcParams.update({
    "figure.facecolor": "#FAFAFA",
    "axes.facecolor"  : "#FAFAFA",
    "axes.grid"       : True,
    "grid.alpha"      : 0.3,
    "font.family"     : "DejaVu Sans",
})

# SECTION 1: DATA LOADING & PREPROCESSING ----------------------

conn = sqlite3.connect(DB_PATH)

customers  = pd.read_sql("SELECT * FROM customers",   conn, parse_dates=["registration_date"])
products   = pd.read_sql("SELECT * FROM products",    conn)
orders     = pd.read_sql("SELECT * FROM orders",      conn, parse_dates=["order_date"])
items      = pd.read_sql("SELECT * FROM order_items", conn)
returns    = pd.read_sql("SELECT * FROM returns",     conn, parse_dates=["return_date"])
conn.close()

print("=" * 60)
print("  E-COMMERCE DATA LOADING SUMMARY")
print("=" * 60)
for name, df in [("Customers",customers),("Products",products),
                 ("Orders",orders),("Items",items),("Returns",returns)]:
    print(f"  {name:15s}: {len(df):,} rows × {df.shape[1]} cols | "
          f"nulls: {df.isnull().sum().sum()}")

# ── Preprocessing ────────────
orders["year"]       = orders["order_date"].dt.year
orders["month"]      = orders["order_date"].dt.month
orders["year_month"] = orders["order_date"].dt.to_period("M")
orders["quarter"]    = orders["order_date"].dt.to_period("Q")
orders["dow"]        = orders["order_date"].dt.day_name()

delivered = orders[orders["status"] == "Delivered"].copy()

# Merge for enriched analysis
order_detail = (
    items.merge(orders[["order_id","customer_id","order_date","status",
                         "year","month","year_month","discount_pct"]],
                on="order_id")
         .merge(products[["product_id","product_name","category","brand",
                           "cost_price"]], on="product_id")
)
order_detail["profit"] = (order_detail["line_revenue"] -
                           order_detail["quantity"] * order_detail["cost_price"])

# SECTION 2: EXPLORATORY DATA ANALYSIS  /-------------------

print("\n" + "=" * 60)
print("  BASIC STATISTICS")
print("=" * 60)

print(f"\n  Total Revenue   : ₹{delivered['total_amount'].sum():>12,.0f}")
print(f"  Total Orders    : {len(delivered):>12,}")
print(f"  Avg Order Value : ₹{delivered['total_amount'].mean():>12,.0f}")
print(f"  Unique Customers: {delivered['customer_id'].nunique():>12,}")
print(f"  Cancellation %  : {(orders['status']=='Cancelled').mean()*100:.1f}%")
print(f"  Return Rate     : {(orders['status']=='Returned').mean()*100:.1f}%")

print("\n  Order Status Distribution:")
print(orders["status"].value_counts().to_string())

print("\n  Revenue by Segment:")
seg_rev = (delivered.merge(customers[["customer_id","segment"]], on="customer_id")
           .groupby("segment")["total_amount"].agg(["sum","mean","count"]))
seg_rev.columns = ["Total Revenue","Avg Order","Orders"]
print(seg_rev.round(0).to_string())

# ── Revenue Distribution ────────────────
print("\n  Delivered orders — total_amount stats:")
print(delivered["total_amount"].describe().round(2).to_string())

# ── RFM Computation ───────────────────────
reference = pd.Timestamp("2025-01-01")
rfm = (delivered.groupby("customer_id")
       .agg(recency=("order_date", lambda x: (reference - x.max()).days),
            frequency=("order_id",  "nunique"),
            monetary=("total_amount","sum"))
       .reset_index())

rfm["r"] = pd.qcut(rfm["recency"],   5, labels=[5,4,3,2,1])
rfm["f"] = pd.qcut(rfm["frequency"].rank(method="first"), 5, labels=[1,2,3,4,5])
rfm["m"] = pd.qcut(rfm["monetary"],  5, labels=[1,2,3,4,5])
rfm["rfm_score"] = rfm[["r","f","m"]].astype(int).sum(axis=1)

def label_rfm(score):
    if score >= 13: return "Champions"
    if score >= 10: return "Loyal"
    if score >= 8:  return "Potential Loyalists"
    if score >= 6:  return "At Risk"
    return "Lost"

rfm["segment"] = rfm["rfm_score"].apply(label_rfm)
print("\n  RFM Segment Distribution:")
print(rfm["segment"].value_counts().to_string())

# SECTION 3: VISUALIZATIONS /-----------------------

# ── Chart 1: Monthly Revenue Trend ───────────────────
monthly = (delivered.groupby("year_month")["total_amount"]
           .sum().reset_index())
monthly["ym_str"] = monthly["year_month"].astype(str)
monthly["mom_growth"] = monthly["total_amount"].pct_change() * 100

fig, ax1 = plt.subplots(figsize=(14, 5))
ax2 = ax1.twinx()

ax1.fill_between(range(len(monthly)), monthly["total_amount"], alpha=0.25, color=PALETTE[0])
ax1.plot(range(len(monthly)), monthly["total_amount"], color=PALETTE[0], lw=2.5, marker="o", ms=4)
ax2.bar(range(len(monthly)), monthly["mom_growth"].fillna(0), alpha=0.4, color=PALETTE[3], width=0.4)
ax2.axhline(0, color="grey", lw=0.8)

ax1.set_xticks(range(len(monthly)))
ax1.set_xticklabels(monthly["ym_str"], rotation=45, ha="right", fontsize=8)
ax1.set_ylabel("Revenue (₹)", color=PALETTE[0], fontsize=11)
ax2.set_ylabel("MoM Growth (%)", color=PALETTE[3], fontsize=11)
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"₹{x/1e3:.0f}K"))
ax1.set_title("Monthly Revenue Trend with MoM Growth", fontsize=14, fontweight="bold", pad=12)
plt.tight_layout()
plt.savefig(f"{FIG_DIR}/01_monthly_revenue_trend.png", dpi=150)
plt.close()
print("\n  ✅ Chart 1: Monthly Revenue Trend saved")

# ── Chart 2: Revenue by Category ──────────────
cat_perf = (order_detail[order_detail["status"]=="Delivered"]
            .groupby("category")
            .agg(revenue=("line_revenue","sum"), profit=("profit","sum"))
            .reset_index()
            .sort_values("revenue", ascending=True))
cat_perf["margin_pct"] = 100 * cat_perf["profit"] / cat_perf["revenue"]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

bars = ax1.barh(cat_perf["category"], cat_perf["revenue"]/1e3, color=PALETTE[:len(cat_perf)])
ax1.bar_label(bars, fmt="₹%.0fK", padding=4, fontsize=9)
ax1.set_xlabel("Revenue (₹ Thousands)")
ax1.set_title("Revenue by Category", fontweight="bold")

bars2 = ax2.barh(cat_perf["category"], cat_perf["margin_pct"],
                 color=[PALETTE[1] if m < 35 else PALETTE[2] for m in cat_perf["margin_pct"]])
ax2.bar_label(bars2, fmt="%.1f%%", padding=4, fontsize=9)
ax2.set_xlabel("Gross Margin %")
ax2.set_title("Gross Margin by Category", fontweight="bold")
ax2.axvline(cat_perf["margin_pct"].mean(), color="grey", ls="--", lw=1.2, label="Avg")
ax2.legend(fontsize=9)

plt.tight_layout()
plt.savefig(f"{FIG_DIR}/02_category_revenue_margin.png", dpi=150)
plt.close()
print("  ✅ Chart 2: Category Revenue & Margin saved")

# ── Chart 3: RFM Segment Distribution ────────────
rfm_summary = (rfm.groupby("segment")
               .agg(customers=("customer_id","count"),
                    avg_monetary=("monetary","mean"))
               .reset_index()
               .sort_values("avg_monetary", ascending=False))

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

colors = [PALETTE[i % len(PALETTE)] for i in range(len(rfm_summary))]
wedges, texts, autotexts = ax1.pie(
    rfm_summary["customers"],
    labels=rfm_summary["segment"],
    autopct="%1.1f%%",
    colors=colors,
    startangle=140,
    pctdistance=0.75)
for at in autotexts: at.set_fontsize(9)
ax1.set_title("Customer Count by RFM Segment", fontweight="bold")

ax2.bar(rfm_summary["segment"], rfm_summary["avg_monetary"]/1e3,
        color=colors)
ax2.set_ylabel("Avg CLV (₹ Thousands)")
ax2.set_title("Average CLV by RFM Segment", fontweight="bold")
ax2.tick_params(axis="x", rotation=30)
for bar in ax2.patches:
    ax2.text(bar.get_x()+bar.get_width()/2,
             bar.get_height()+0.3,
             f"₹{bar.get_height():.1f}K",
             ha="center", fontsize=8)

plt.tight_layout()
plt.savefig(f"{FIG_DIR}/03_rfm_segments.png", dpi=150)
plt.close()
print("  ✅ Chart 3: RFM Segments saved")

# ── Chart 4: Order Value Distribution ──────────────
cust_orders = delivered.merge(customers[["customer_id","segment"]], on="customer_id")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

sns.histplot(delivered["total_amount"], bins=40, ax=ax1, color=PALETTE[0], kde=True)
ax1.axvline(delivered["total_amount"].mean(), color="red", ls="--", lw=1.5,
            label=f"Mean ₹{delivered['total_amount'].mean():.0f}")
ax1.axvline(delivered["total_amount"].median(), color="green", ls="--", lw=1.5,
            label=f"Median ₹{delivered['total_amount'].median():.0f}")
ax1.set_xlabel("Order Value (₹)")
ax1.set_title("Order Value Distribution", fontweight="bold")
ax1.legend(fontsize=9)

seg_order = ["Premium","Regular","Budget"]
seg_data   = [cust_orders[cust_orders["segment"]==s]["total_amount"].values for s in seg_order]
bp = ax2.boxplot(seg_data, labels=seg_order, patch_artist=True, notch=True)
for patch, color in zip(bp["boxes"], PALETTE):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)
ax2.set_ylabel("Order Value (₹)")
ax2.set_title("Order Value by Customer Segment", fontweight="bold")

plt.tight_layout()
plt.savefig(f"{FIG_DIR}/04_order_value_distribution.png", dpi=150)
plt.close()
print("  ✅ Chart 4: Order Value Distribution saved")

# Chart 5: Payment Mode -------------------------------
pay_chan = (delivered.groupby(["payment_mode","channel"])
            .agg(orders=("order_id","count"))
            .reset_index()
            .pivot(index="payment_mode", columns="channel", values="orders")
            .fillna(0))

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

sns.heatmap(pay_chan, annot=True, fmt=".0f", cmap="Blues",
            linewidths=0.5, ax=ax1, cbar_kws={"label":"Orders"})
ax1.set_title("Orders: Payment Mode × Channel", fontweight="bold")
ax1.set_xlabel("")

pay_rev = (delivered.groupby("payment_mode")
           .agg(revenue=("total_amount","sum"))
           .sort_values("revenue", ascending=False)
           .reset_index())
ax2.barh(pay_rev["payment_mode"], pay_rev["revenue"]/1e3, color=PALETTE)
ax2.set_xlabel("Revenue (₹ Thousands)")
ax2.set_title("Revenue by Payment Mode", fontweight="bold")
for bar in ax2.patches:
    ax2.text(bar.get_width()+1, bar.get_y()+bar.get_height()/2,
             f"₹{bar.get_width():.0f}K", va="center", fontsize=9)

plt.tight_layout()
plt.savefig(f"{FIG_DIR}/05_payment_channel_analysis.png", dpi=150)
plt.close()
print("  ✅ Chart 5: Payment & Channel Analysis saved")

# ── Chart 6: Correlation Heatmap + Scatter ───────────
cust_stats = (delivered.groupby("customer_id")
              .agg(orders=("order_id","nunique"),
                   revenue=("total_amount","sum"),
                   aov=("total_amount","mean"),
                   avg_discount=("discount_pct","mean"))
              .reset_index())
cust_stats = cust_stats.merge(customers[["customer_id","segment"]], on="customer_id")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

corr_cols = ["orders","revenue","aov","avg_discount"]
corr_mat  = cust_stats[corr_cols].corr()
mask = np.triu(np.ones_like(corr_mat, dtype=bool))
sns.heatmap(corr_mat, annot=True, fmt=".2f", cmap="RdYlGn",
            mask=mask, vmin=-1, vmax=1, ax=ax1,
            linewidths=0.5, cbar_kws={"shrink":0.8})
ax1.set_title("Correlation Matrix\n(Customer Behaviour)", fontweight="bold")

for seg, color in zip(["Premium","Regular","Budget"], PALETTE):
    sub = cust_stats[cust_stats["segment"]==seg]
    ax2.scatter(sub["orders"], sub["revenue"]/1e3, alpha=0.5,
                label=seg, s=40, color=color)
slope, intercept, r_val, _, _ = stats.linregress(cust_stats["orders"], cust_stats["revenue"])
x_line = np.linspace(cust_stats["orders"].min(), cust_stats["orders"].max(), 50)
ax2.plot(x_line, (slope*x_line + intercept)/1e3, "k--", lw=1.5,
         label=f"Trend (R²={r_val**2:.2f})")
ax2.set_xlabel("Number of Orders")
ax2.set_ylabel("Total Revenue (₹ Thousands)")
ax2.set_title("Orders vs Revenue by Segment", fontweight="bold")
ax2.legend(fontsize=9)

plt.tight_layout()
plt.savefig(f"{FIG_DIR}/06_correlation_scatter.png", dpi=150)
plt.close()
print("  ✅ Chart 6: Correlation & Scatter saved")

# SECTION 4: STATISTICAL ANALYSIS/-----------------------

print("\n" + "=" * 60)
print("  STATISTICAL ANALYSIS")
print("=" * 60)

# Normality test on order values
stat, p = stats.shapiro(delivered["total_amount"].sample(min(200, len(delivered))))
print(f"\n  Shapiro-Wilk normality test on order values:")
print(f"    Statistic={stat:.4f}, p-value={p:.4f}")
print(f"    {'NOT normal (right-skewed)' if p < 0.05 else 'Normal distribution'} — use median for central tendency")

premium_aov = cust_orders[cust_orders["segment"]=="Premium"]["total_amount"]
regular_aov = cust_orders[cust_orders["segment"]=="Regular"]["total_amount"]
t_stat, t_p  = stats.ttest_ind(premium_aov, regular_aov)
print(f"\n  T-Test: Premium vs Regular order values:")
print(f"    t={t_stat:.3f}, p={t_p:.4f} → "
      f"{'Significant' if t_p < 0.05 else 'Not significant'} difference (α=0.05)")
print(f"    Premium Avg: ₹{premium_aov.mean():.0f} | Regular Avg: ₹{regular_aov.mean():.0f}")

# Pearson correlation
r, p_r = stats.pearsonr(cust_stats["orders"], cust_stats["revenue"])
print(f"\n  Pearson Correlation (orders vs revenue):")
print(f"    r={r:.3f}, p={p_r:.4f} → Strong {'positive' if r>0 else 'negative'} relationship")

disc_none = delivered[delivered["discount_pct"]==0]["total_amount"]
disc_some = delivered[delivered["discount_pct"]>0]["total_amount"]
t2, p2 = stats.ttest_ind(disc_none, disc_some)
print(f"\n  T-Test: Discount impact on order value:")
print(f"    No discount mean ₹{disc_none.mean():.0f} | Discount mean ₹{disc_some.mean():.0f}")
print(f"    t={t2:.3f}, p={p2:.4f} → "
      f"{'Significant' if p2<0.05 else 'No significant'} difference")

# SECTION 5: OPTIONAL PREDICTIVE MODEL — CLV REGRESSION /----------

print("\n" + "=" * 60)
print("  PREDICTIVE MODEL — CLV Regression (OLS)")
print("=" * 60)

from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.preprocessing import LabelEncoder

model_df = cust_stats.copy()
le = LabelEncoder()
model_df["segment_enc"] = le.fit_transform(model_df["segment"])

X = model_df[["orders","aov","avg_discount","segment_enc"]]
y = model_df["revenue"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
model = LinearRegression().fit(X_train, y_train)
y_pred = model.predict(X_test)

print(f"\n  R² Score  : {r2_score(y_test, y_pred):.4f}")
print(f"  MAE       : ₹{mean_absolute_error(y_test, y_pred):,.0f}")
print(f"\n  Coefficients:")
for feat, coef in zip(X.columns, model.coef_):
    print(f"    {feat:15s}: {coef:+.3f}")
print(f"  Intercept   : {model.intercept_:.3f}")
print(f"\n  Interpretation: Each additional order increases CLV by ₹{model.coef_[0]:.0f}")

print("\n" + "=" * 60)
print("  ALL ANALYSIS COMPLETE — figures saved to data/figures/")
print("=" * 60)
