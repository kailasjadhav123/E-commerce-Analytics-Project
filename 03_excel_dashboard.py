"""
E-Commerce Analytics Project — Excel Dashboard
"""

import pandas as pd
import numpy as np
import sqlite3, os
from openpyxl import Workbook
from openpyxl.styles import (Font, PatternFill, Alignment, Border, Side,
                              GradientFill)
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, LineChart, PieChart, Reference
from openpyxl.chart.series import DataPoint

# ── Load data ───────────────
BASE    = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, "..", "data", "ecommerce.db")
OUT     = os.path.join(BASE, "..", "data", "ECommerce_Dashboard.xlsx")

conn = sqlite3.connect(DB_PATH)
orders    = pd.read_sql("SELECT * FROM orders",      conn, parse_dates=["order_date"])
items     = pd.read_sql("SELECT * FROM order_items", conn)
customers = pd.read_sql("SELECT * FROM customers",   conn)
products  = pd.read_sql("SELECT * FROM products",    conn)
returns   = pd.read_sql("SELECT * FROM returns",     conn)
conn.close()

delivered = orders[orders["status"] == "Delivered"].copy()
delivered["year_month"] = delivered["order_date"].dt.to_period("M").astype(str)
delivered["year"]  = delivered["order_date"].dt.year
delivered["month"] = delivered["order_date"].dt.month_name()

order_detail = (items
    .merge(orders[["order_id","customer_id","order_date","status","discount_pct"]], on="order_id")
    .merge(products[["product_id","category","cost_price"]], on="product_id"))
order_detail["profit"] = (order_detail["line_revenue"] -
                           order_detail["quantity"] * order_detail["cost_price"])

# ── Style helpers ─────────────────
HEADER_FILL   = PatternFill("solid", fgColor="1F4E79")
SUBHDR_FILL   = PatternFill("solid", fgColor="2C7BB6")
ALT_FILL      = PatternFill("solid", fgColor="EBF2FA")
ACCENT_FILL   = PatternFill("solid", fgColor="D6E4F0")
WHITE_FILL    = PatternFill("solid", fgColor="FFFFFF")
GREEN_FILL    = PatternFill("solid", fgColor="E2EFDA")
ORANGE_FILL   = PatternFill("solid", fgColor="FCE4D6")

THIN = Side(style="thin", color="B0C4DE")
THIN_BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

def hdr(cell, text, size=11, bold=True, color="FFFFFF", fill=None):
    cell.value = text
    cell.font  = Font(bold=bold, size=size, color=color,
                      name="Calibri")
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    cell.border = THIN_BORDER
    if fill: cell.fill = fill

def data_cell(cell, value, fmt=None, fill=None, bold=False, align="center"):
    cell.value = value
    cell.font  = Font(size=10, name="Calibri", bold=bold)
    cell.alignment = Alignment(horizontal=align, vertical="center")
    cell.border = THIN_BORDER
    if fmt:  cell.number_format = fmt
    if fill: cell.fill = fill

def set_col_width(ws, col, width):
    ws.column_dimensions[get_column_letter(col)].width = width

# ── Build workbook ───────────
wb = Workbook()
wb.remove(wb.active)   # remove default sheet

# SHEET 1: Executive Summary /---------------------------------
ws1 = wb.create_sheet("📊 Executive Summary")
ws1.sheet_view.showGridLines = False
ws1.row_dimensions[1].height = 40

# Title
ws1.merge_cells("A1:H1")
title = ws1["A1"]
title.value = "E-COMMERCE ANALYTICS DASHBOARD — EXECUTIVE SUMMARY"
title.font  = Font(bold=True, size=16, color="FFFFFF", name="Calibri")
title.fill  = PatternFill("solid", fgColor="1F4E79")
title.alignment = Alignment(horizontal="center", vertical="center")

ws1.row_dimensions[3].height = 22
ws1.row_dimensions[4].height = 30

kpis = [
    ("Total Revenue", f"₹{delivered['total_amount'].sum():,.0f}", "A3"),
    ("Total Orders",  f"{len(delivered):,}",                     "C3"),
    ("Avg Order Value", f"₹{delivered['total_amount'].mean():,.0f}", "E3"),
    ("Unique Customers", f"{delivered['customer_id'].nunique():,}", "G3"),
]
kpi_labels_row, kpi_val_row = 3, 4
for label, value, start_col in kpis:
    col_idx = ord(start_col[0]) - ord("A") + 1
    ws1.merge_cells(start_row=kpi_labels_row, start_column=col_idx,
                    end_row=kpi_labels_row, end_column=col_idx+1)
    ws1.merge_cells(start_row=kpi_val_row, start_column=col_idx,
                    end_row=kpi_val_row, end_column=col_idx+1)
    lc = ws1.cell(kpi_labels_row, col_idx)
    hdr(lc, label, size=10, fill=SUBHDR_FILL)
    vc = ws1.cell(kpi_val_row, col_idx)
    hdr(vc, value, size=13, fill=ACCENT_FILL, color="1F4E79")

# Additional KPIs --------
extra_kpis = [
    ("Return Rate",     f"{(orders['status']=='Returned').mean()*100:.1f}%"),
    ("Cancel Rate",     f"{(orders['status']=='Cancelled').mean()*100:.1f}%"),
    ("Avg Discount",    f"{delivered['discount_pct'].mean()*100:.1f}%"),
    ("Gross Margin",    "~42%"),
]
ws1.row_dimensions[6].height = 20
ws1.row_dimensions[7].height = 28
for i, (label, value) in enumerate(extra_kpis):
    col = 1 + i * 2
    ws1.merge_cells(start_row=6, start_column=col, end_row=6, end_column=col+1)
    ws1.merge_cells(start_row=7, start_column=col, end_row=7, end_column=col+1)
    lc = ws1.cell(6, col); hdr(lc, label, size=9, fill=PatternFill("solid", fgColor="2E75B6"))
    vc = ws1.cell(7, col); hdr(vc, value, size=12, fill=GREEN_FILL, color="1F4E79")

monthly = (delivered.groupby("year_month")["total_amount"]
           .sum().reset_index())
monthly.columns = ["Year-Month","Revenue"]
monthly["MoM Growth"] = monthly["Revenue"].pct_change().fillna(0)

row_start = 9
ws1.row_dimensions[row_start].height = 22
ws1.merge_cells(f"A{row_start}:D{row_start}")
hdr(ws1[f"A{row_start}"], "Monthly Revenue Trend", size=11, fill=HEADER_FILL)

headers_monthly = ["Year-Month","Revenue (₹)","MoM Growth %","Volume Index"]
for ci, h in enumerate(headers_monthly, 1):
    c = ws1.cell(row_start+1, ci)
    hdr(c, h, size=10, fill=SUBHDR_FILL)
    set_col_width(ws1, ci, 16)

for ri, (_, row) in enumerate(monthly.iterrows()):
    r = row_start + 2 + ri
    fill = ALT_FILL if ri % 2 == 0 else WHITE_FILL
    ws1.row_dimensions[r].height = 18
    data_cell(ws1.cell(r, 1), row["Year-Month"],  fill=fill)
    data_cell(ws1.cell(r, 2), row["Revenue"],     fmt='₹#,##0', fill=fill, align="right")
    data_cell(ws1.cell(r, 3), row["MoM Growth"],  fmt='0.0%',   fill=fill, align="right")
    data_cell(ws1.cell(r, 4), f'=B{r}/MAX($B${row_start+2}:$B${row_start+1+len(monthly)})',
              fmt='0.0%', fill=fill, align="right")

# Chart: Monthly Revenue-----------
chart_r = BarChart()
chart_r.type = "col"
chart_r.title = "Monthly Revenue"
chart_r.y_axis.title = "Revenue (₹)"
chart_r.x_axis.title = "Month"
data_ref = Reference(ws1, min_col=2, max_col=2,
                     min_row=row_start+1, max_row=row_start+1+len(monthly))
cats_ref = Reference(ws1, min_col=1,
                     min_row=row_start+2, max_row=row_start+1+len(monthly))
chart_r.add_data(data_ref, titles_from_data=True)
chart_r.set_categories(cats_ref)
chart_r.shape = 4
chart_r.width = 22; chart_r.height = 13
ws1.add_chart(chart_r, "F9")

# SHEET 2: Category Performance /--------------------------
ws2 = wb.create_sheet("📦 Category Performance")
ws2.sheet_view.showGridLines = False

ws2.merge_cells("A1:G1")
hdr(ws2["A1"], "CATEGORY PERFORMANCE ANALYSIS", size=14, fill=HEADER_FILL)

cat_perf = (order_detail[order_detail["status"]=="Delivered"]
            .groupby("category")
            .agg(Orders    =("order_id","nunique"),
                 Units     =("quantity","sum"),
                 Revenue   =("line_revenue","sum"),
                 Profit    =("profit","sum"),
                 Avg_Price =("unit_price","mean"))
            .reset_index()
            .sort_values("Revenue", ascending=False))
cat_perf["Margin_pct"] = cat_perf["Profit"] / cat_perf["Revenue"]
cat_perf["Revenue_pct"] = cat_perf["Revenue"] / cat_perf["Revenue"].sum()

cols = ["Category","Orders","Units","Revenue","Profit","Margin%","Revenue%","Avg Price"]
for ci, h in enumerate(cols, 1):
    hdr(ws2.cell(2, ci), h, size=10, fill=SUBHDR_FILL)
    set_col_width(ws2, ci, 16)

for ri, row in enumerate(cat_perf.itertuples(), 3):
    fill = ALT_FILL if (ri-3)%2==0 else WHITE_FILL
    ws2.row_dimensions[ri].height = 18
    data_cell(ws2.cell(ri,1), row.category,   fill=fill, align="left")
    data_cell(ws2.cell(ri,2), row.Orders,      fill=fill, fmt="#,##0")
    data_cell(ws2.cell(ri,3), row.Units,       fill=fill, fmt="#,##0")
    data_cell(ws2.cell(ri,4), row.Revenue,     fill=fill, fmt='₹#,##0', align="right")
    data_cell(ws2.cell(ri,5), row.Profit,      fill=fill, fmt='₹#,##0', align="right")
    data_cell(ws2.cell(ri,6), row.Margin_pct,  fill=fill, fmt='0.0%',   align="right")
    data_cell(ws2.cell(ri,7), row.Revenue_pct, fill=fill, fmt='0.0%',   align="right")
    data_cell(ws2.cell(ri,8), row.Avg_Price,   fill=fill, fmt='₹#,##0', align="right")

# Pie chart for category revenue share
pie = PieChart()
pie.title = "Revenue Share by Category"
labels = Reference(ws2, min_col=1, min_row=3, max_row=2+len(cat_perf))
data   = Reference(ws2, min_col=4, min_row=2, max_row=2+len(cat_perf))
pie.add_data(data, titles_from_data=True)
pie.set_categories(labels)
pie.width = 18; pie.height = 13
ws2.add_chart(pie, "A12")


# SHEET 3: Customer Segmentation /-----------------------
ws3 = wb.create_sheet("👥 Customer RFM")
ws3.sheet_view.showGridLines = False

ws3.merge_cells("A1:H1")
hdr(ws3["A1"], "CUSTOMER SEGMENTATION — RFM ANALYSIS", size=14, fill=HEADER_FILL)

reference_date = pd.Timestamp("2025-01-01")
rfm = (delivered.groupby("customer_id")
       .agg(last_order=("order_date","max"),
            frequency =("order_id","nunique"),
            monetary  =("total_amount","sum"))
       .reset_index())
rfm["recency"] = (reference_date - rfm["last_order"]).dt.days
rfm["R"] = pd.qcut(rfm["recency"],   5, labels=[5,4,3,2,1])
rfm["F"] = pd.qcut(rfm["frequency"].rank(method="first"), 5, labels=[1,2,3,4,5])
rfm["M"] = pd.qcut(rfm["monetary"],  5, labels=[1,2,3,4,5])
rfm["RFM_Score"] = rfm[["R","F","M"]].astype(int).sum(axis=1)

def rfm_label(s):
    if s >= 13: return "Champions"
    if s >= 10: return "Loyal Customers"
    if s >= 8:  return "Potential Loyalists"
    if s >= 6:  return "At Risk"
    return "Lost Customers"

rfm["RFM_Segment"] = rfm["RFM_Score"].apply(rfm_label)
rfm = rfm.merge(customers[["customer_id","first_name","last_name","segment","city"]], on="customer_id")

headers_rfm = ["Customer ID","Name","City","Recency","Frequency","Monetary",
               "RFM Score","RFM Segment"]
for ci, h in enumerate(headers_rfm, 1):
    hdr(ws3.cell(2, ci), h, size=10, fill=SUBHDR_FILL)
    set_col_width(ws3, ci, 18)

seg_colors = {"Champions":"00B050","Loyal Customers":"70AD47",
              "Potential Loyalists":"FFC000","At Risk":"FF7043","Lost Customers":"FF0000"}

for ri, row in enumerate(rfm.itertuples(), 3):
    fill_color = seg_colors.get(row.RFM_Segment, "FFFFFF")
    seg_fill = PatternFill("solid", fgColor=fill_color+"33")
    ws3.row_dimensions[ri].height = 16
    data_cell(ws3.cell(ri,1), row.customer_id,                    fill=ALT_FILL if (ri-3)%2==0 else WHITE_FILL)
    data_cell(ws3.cell(ri,2), f"{row.first_name} {row.last_name}", fill=ALT_FILL if (ri-3)%2==0 else WHITE_FILL, align="left")
    data_cell(ws3.cell(ri,3), row.city,                            fill=ALT_FILL if (ri-3)%2==0 else WHITE_FILL, align="left")
    data_cell(ws3.cell(ri,4), row.recency,                         fill=ALT_FILL if (ri-3)%2==0 else WHITE_FILL, fmt="#,##0")
    data_cell(ws3.cell(ri,5), row.frequency,                       fill=ALT_FILL if (ri-3)%2==0 else WHITE_FILL, fmt="#,##0")
    data_cell(ws3.cell(ri,6), row.monetary,                        fill=ALT_FILL if (ri-3)%2==0 else WHITE_FILL, fmt="₹#,##0", align="right")
    data_cell(ws3.cell(ri,7), row.RFM_Score,                       fill=ALT_FILL if (ri-3)%2==0 else WHITE_FILL, fmt="#,##0")
    data_cell(ws3.cell(ri,8), row.RFM_Segment,                     fill=seg_fill, bold=True)

# SHEET 4: State Revenue Heatmap /----------------
ws4 = wb.create_sheet("🗺 State Analysis")
ws4.sheet_view.showGridLines = False

ws4.merge_cells("A1:F1")
hdr(ws4["A1"], "REVENUE & ORDER ANALYSIS BY STATE", size=14, fill=HEADER_FILL)

state_data = (delivered.groupby("state")
              .agg(Orders=("order_id","count"),
                   Revenue=("total_amount","sum"),
                   Customers=("customer_id","nunique"),
                   AOV=("total_amount","mean"))
              .reset_index()
              .sort_values("Revenue", ascending=False))
state_data["Revenue_Share"] = state_data["Revenue"] / state_data["Revenue"].sum()

for ci, h in enumerate(["State","Orders","Revenue","Customers","AOV","Revenue Share"], 1):
    hdr(ws4.cell(2, ci), h, size=10, fill=SUBHDR_FILL)
    set_col_width(ws4, ci, 18)

max_rev = state_data["Revenue"].max()
for ri, row in enumerate(state_data.itertuples(), 3):
    intensity = int(200 - 150 * (row.Revenue / max_rev))
    hex_fill = f"{intensity:02X}D4FF"
    heat_fill = PatternFill("solid", fgColor=hex_fill)
    ws4.row_dimensions[ri].height = 18
    data_cell(ws4.cell(ri,1), row.state,         fill=ALT_FILL if (ri-3)%2==0 else WHITE_FILL, align="left")
    data_cell(ws4.cell(ri,2), row.Orders,         fill=ALT_FILL if (ri-3)%2==0 else WHITE_FILL, fmt="#,##0")
    data_cell(ws4.cell(ri,3), row.Revenue,        fill=heat_fill,           fmt="₹#,##0", align="right")
    data_cell(ws4.cell(ri,4), row.Customers,      fill=ALT_FILL if (ri-3)%2==0 else WHITE_FILL, fmt="#,##0")
    data_cell(ws4.cell(ri,5), row.AOV,            fill=ALT_FILL if (ri-3)%2==0 else WHITE_FILL, fmt="₹#,##0", align="right")
    data_cell(ws4.cell(ri,6), row.Revenue_Share,  fill=ALT_FILL if (ri-3)%2==0 else WHITE_FILL, fmt="0.0%")

bar2 = BarChart()
bar2.type = "bar"
bar2.title = "Top States by Revenue"
bar2.y_axis.title = "Revenue (₹)"
n = min(8, len(state_data))
data_ref2 = Reference(ws4, min_col=3, max_col=3, min_row=2, max_row=2+n)
cats2 = Reference(ws4, min_col=1, min_row=3, max_row=2+n)
bar2.add_data(data_ref2, titles_from_data=True)
bar2.set_categories(cats2)
bar2.width = 20; bar2.height = 14
ws4.add_chart(bar2, f"A{3+len(state_data)+2}")

# SHEET 5: Data Dictionary /----------
ws5 = wb.create_sheet("📋 Data Dictionary")
ws5.sheet_view.showGridLines = False

ws5.merge_cells("A1:E1")
hdr(ws5["A1"], "DATA DICTIONARY — ALL TABLES", size=14, fill=HEADER_FILL)

dd_data = [

    ("customers","customer_id","INTEGER","Unique customer identifier","1"),
    ("customers","first_name","TEXT","Customer first name","Aarav"),
    ("customers","last_name","TEXT","Customer last name","Sharma"),
    ("customers","email","TEXT","Unique email address","customer1@email.com"),
    ("customers","city","TEXT","City of residence","Mumbai"),
    ("customers","state","TEXT","State of residence","Maharashtra"),
    ("customers","segment","TEXT","Business segment: Premium/Regular/Budget","Premium"),
    ("customers","registration_date","DATE","Account creation date","2022-03-15"),
    ("customers","is_active","INTEGER","1=active, 0=inactive","1"),
    ("products","product_id","INTEGER","Unique product identifier","1"),
    ("products","product_name","TEXT","Product display name","Smartphone"),
    ("products","category","TEXT","Product category","Electronics"),
    ("products","unit_price","REAL","Selling price in INR","29999.00"),
    ("products","cost_price","REAL","Cost of goods in INR","14000.00"),
    ("products","stock_qty","INTEGER","Units in inventory","150"),
    ("orders","order_id","INTEGER","Unique order identifier","1"),
    ("orders","customer_id","INTEGER","FK → customers.customer_id","42"),
    ("orders","order_date","DATE","Date order was placed","2023-06-12"),
    ("orders","status","TEXT","Order lifecycle status","Delivered"),
    ("orders","payment_mode","TEXT","Payment method used","UPI"),
    ("orders","channel","TEXT","Sales channel","Mobile App"),
    ("orders","discount_pct","REAL","Discount applied (0-0.20)","0.10"),
    ("orders","total_amount","REAL","Net order value in INR","4500.00"),
    ("order_items","item_id","INTEGER","Unique line-item identifier","1"),
    ("order_items","order_id","INTEGER","FK → orders.order_id","1"),
    ("order_items","product_id","INTEGER","FK → products.product_id","5"),
    ("order_items","quantity","INTEGER","Units purchased","2"),
    ("order_items","line_revenue","REAL","qty × price × (1-discount)","5399.80"),
    ("returns","return_id","INTEGER","Unique return identifier","1"),
    ("returns","order_id","INTEGER","FK → orders.order_id","37"),
    ("returns","return_date","DATE","Date return was initiated","2023-07-01"),
    ("returns","reason","TEXT","Customer-stated return reason","Defective product"),
    ("returns","refund_amount","REAL","Refund issued in INR","1250.00"),
    ("returns","status","TEXT","Return processing status","Approved"),
]

for ci, h in enumerate(["Table","Column","Data Type","Description","Example"], 1):
    hdr(ws5.cell(2, ci), h, size=10, fill=SUBHDR_FILL)
    set_col_width(ws5, ci, [16, 20, 14, 40, 22][ci-1])

prev_table = ""
for ri, row in enumerate(dd_data, 3):
    tbl_fill = ALT_FILL if row[0] != prev_table else WHITE_FILL
    prev_table = row[0]
    ws5.row_dimensions[ri].height = 16
    for ci, val in enumerate(row, 1):
        data_cell(ws5.cell(ri, ci), val, fill=tbl_fill,
                  align="left" if ci in [1,2,4,5] else "center")

# ── Save ───────────────
wb.save(OUT)
print(f"✅ Excel dashboard saved → {OUT}")
print("   Sheets: Executive Summary | Category Performance | "
      "Customer RFM | State Analysis | Data Dictionary")
