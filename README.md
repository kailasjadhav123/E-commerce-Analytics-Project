# 🛒 E-Commerce Analytics — Data Analytics Portfolio Project

> **Domain:** E-Commerce | **Tools:** Python · SQL · Excel · Power BI  
> **Skill Level:** Industry-level portfolio project for Data Analyst interviews

---

## 📋 Table of Contents
1. [Project Architecture](#1-project-architecture)
2. [Business Problem & Objectives](#2-business-problem--objectives)
3. [Data Dictionary](#3-data-dictionary)
4. [Entity-Relationship Description](#4-entity-relationship-description)
5. [Implementation Guide](#5-step-by-step-implementation-guide)
6. [Excel Dashboard Plan](#6-excel-dashboard-plan)
7. [Power BI Dashboard Design](#7-power-bi-dashboard-design)


---

## 1. Project Architecture

```
ecommerce_project/
│
├── data/
│   ├── ecommerce.db          ← SQLite database (5 tables, 2,800+ rows)
│   ├── customers.csv
│   ├── orders.csv
│   ├── order_items.csv
│   ├── products.csv
│   ├── returns.csv
│   ├── ECommerce_Dashboard.xlsx  ← Excel dashboard (5 sheets)
│   └── figures/              ← 6 matplotlib charts (PNG)
│
├── python/
│   ├── 01_generate_data.py   ← Synthetic data generation
│   ├── 02_eda_visualization.py ← EDA, 6 charts, statistical tests, ML
│   └── 03_excel_dashboard.py ← Programmatic Excel workbook builder
│
├── sql/
│   └── ecommerce_queries.sql ← 25+ SQL queries (DDL + 7 analysis sections)
│
└── docs/
    └── README.md             ← This file
```

**Technology Stack:**

| Layer | Tool | Purpose |
|---|---|---|
| Data Generation | Python (faker-style) | Realistic synthetic dataset |
| Storage | SQLite | Portable relational database |
| SQL Analysis | SQLite / compatible with PostgreSQL | 25+ analytical queries |
| EDA & ML | Python: pandas, matplotlib, seaborn, scipy, sklearn | Visualisation & modelling |
| Reporting | Excel (openpyxl) | Business dashboard |
| BI | Power BI | Interactive executive dashboard |

---

## 2. Business Problem & Objectives

### Problem Statement
An Indian e-commerce company operating across multiple states wants to understand its revenue performance, customer behaviour, and product economics to drive data-informed decisions. The company has data across orders, customers, products, and returns but lacks consolidated analytics.

### Business Objectives
1. **Revenue Analysis** — Track total revenue, average order value, and gross margin across time.
2. **Customer Segmentation** — Identify high-value customers using RFM analysis; reduce churn.
3. **Product Performance** — Find top and bottom performers; optimise pricing and category mix.
4. **Return Rate Management** — Identify products and categories with high return rates.
5. **Geographic Insights** — Pinpoint top states driving revenue growth.
6. **Channel Optimisation** — Understand which sales channels deliver highest ROI.

### Key Business Questions
- Which customer segments contribute most to revenue?
- What is our month-over-month and year-over-year revenue growth?
- Which products have the highest return rates and why?
- Which states and cities are growth opportunities?
- How does discounting affect order value and customer behaviour?

---

## 3. Data Dictionary

### Table: `customers` (300 rows)
| Column | Type | Description | Example |
|---|---|---|---|
| customer_id | INTEGER | Primary key | 1 |
| first_name | TEXT | Customer's first name | Aarav |
| last_name | TEXT | Customer's last name | Sharma |
| email | TEXT | Unique email (login ID) | customer1@email.com |
| phone | TEXT | Mobile number | +917823456789 |
| city | TEXT | City of residence | Mumbai |
| state | TEXT | State of residence | Maharashtra |
| pincode | TEXT | 6-digit postal code | 400001 |
| segment | TEXT | Premium / Regular / Budget | Premium |
| registration_date | DATE | Account creation date | 2022-03-15 |
| is_active | INTEGER | 1 = active, 0 = churned | 1 |

### Table: `products` (40 rows)
| Column | Type | Description | Example |
|---|---|---|---|
| product_id | INTEGER | Primary key | 1 |
| product_name | TEXT | Display name | Smartphone |
| category | TEXT | Electronics / Clothing / etc. | Electronics |
| brand | TEXT | Brand name | Samsung |
| unit_price | REAL | Selling price (INR) | 29999.00 |
| cost_price | REAL | Cost of goods (INR) | 14000.00 |
| stock_qty | INTEGER | Current inventory | 150 |
| is_active | INTEGER | Listed on platform | 1 |

### Table: `orders` (800 rows)
| Column | Type | Description | Example |
|---|---|---|---|
| order_id | INTEGER | Primary key | 1 |
| customer_id | INTEGER | FK → customers | 42 |
| order_date | DATE | Order placement date | 2023-06-12 |
| status | TEXT | Delivered/Shipped/Cancelled/Returned/Processing | Delivered |
| payment_mode | TEXT | UPI/Credit Card/COD/etc. | UPI |
| channel | TEXT | Mobile App/Website/Mobile Web | Mobile App |
| discount_pct | REAL | Discount fraction (0–0.20) | 0.10 |
| shipping_cost | REAL | Shipping fee (INR) | 49.00 |
| total_amount | REAL | Net order value (INR) | 4500.00 |
| city | TEXT | Delivery city | Pune |
| state | TEXT | Delivery state | Maharashtra |

### Table: `order_items` (1,620 rows)
| Column | Type | Description | Example |
|---|---|---|---|
| item_id | INTEGER | Primary key | 1 |
| order_id | INTEGER | FK → orders | 1 |
| product_id | INTEGER | FK → products | 5 |
| quantity | INTEGER | Units purchased | 2 |
| unit_price | REAL | Price at time of purchase | 2699.90 |
| discount_pct | REAL | Inherited from order | 0.10 |
| line_revenue | REAL | qty × price × (1−discount) | 4859.82 |

### Table: `returns` (60 rows)
| Column | Type | Description | Example |
|---|---|---|---|
| return_id | INTEGER | Primary key | 1 |
| order_id | INTEGER | FK → orders | 37 |
| return_date | DATE | Return initiation date | 2023-07-01 |
| reason | TEXT | Customer-stated reason | Defective product |
| refund_amount | REAL | Refund issued (INR) | 1250.00 |
| status | TEXT | Approved/Pending/Rejected | Approved |

---

## 4. Entity-Relationship Description

```
CUSTOMERS  ──< ORDERS  ──< ORDER_ITEMS >── PRODUCTS
                  │
                  └──< RETURNS
```

- **CUSTOMERS → ORDERS**: One customer can place many orders (1:N). `customer_id` is the foreign key on `orders`.
- **ORDERS → ORDER_ITEMS**: One order contains one or more line items (1:N). `order_id` is the foreign key on `order_items`.
- **PRODUCTS → ORDER_ITEMS**: One product can appear in many order items (1:N). `product_id` is the foreign key on `order_items`.
- **ORDERS → RETURNS**: One delivered/returned order may have one return record (1:0..1). `order_id` is the foreign key on `returns`.

---

## 5. Step-by-Step Implementation Guide

### Step 1: Environment Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install dependencies
pip install pandas numpy matplotlib seaborn scipy scikit-learn openpyxl sqlite3
```

### Step 2: Generate Data
```bash
python python/01_generate_data.py
# Output: data/ecommerce.db + 5 CSV files
```

### Step 3: Run SQL Analysis
```bash
# Open with any SQL client or run via Python
sqlite3 data/ecommerce.db < sql/ecommerce_queries.sql
# Or use DB Browser for SQLite (free GUI tool)
```

### Step 4: Python EDA
```bash
python python/02_eda_visualization.py
# Output: 6 charts in data/figures/
```

### Step 5: Build Excel Dashboard
```bash
python python/03_excel_dashboard.py
# Output: data/ECommerce_Dashboard.xlsx
```

### Step 6: Power BI Dashboard
1. Open Power BI Desktop
2. Get Data → SQLite → browse to `data/ecommerce.db`
3. Load all 5 tables
4. Apply the DAX measures from Section 7
5. Build visuals as per the layout plan

---

## 6. Excel Dashboard Plan

### Sheet 1: 📊 Executive Summary
**Purpose:** C-suite snapshot — one-screen KPI overview

| Element | Type | KPI Tracked |
|---|---|---|
| KPI Cards (row 1) | Merged cells with conditional formatting | Revenue, Orders, AOV, Unique Customers |
| Secondary KPIs | Coloured tiles | Return Rate, Cancel Rate, Avg Discount |
| Monthly Revenue Table | Structured table | Month, Revenue, MoM Growth %, Volume Index |
| Monthly Revenue Chart | Clustered column | Revenue trend over 36 months |

### Sheet 2: 📦 Category Performance
**Purpose:** Product team decision-making

| Pivot Structure | Row | Column | Values |
|---|---|---|---|
| Category Revenue | Category | — | SUM(Revenue), SUM(Profit), Margin% |
| Category by Year | Category | Year | Revenue comparison |

**Chart:** Horizontal bar for revenue share + Column for margin comparison

### Sheet 3: 👥 Customer RFM
**Purpose:** Marketing team — targeting and retention campaigns

| Element | Description |
|---|---|
| RFM Score Table | Customer-level: Recency, Frequency, Monetary, Score, Segment |
| Segment Summary | Pivot by RFM Segment → Count, Avg CLV, Avg Recency |
| Colour coding | Green = Champions, Red = Lost Customers |

**Chart:** Pie chart for segment distribution + Bar for avg CLV by segment

### Sheet 4: 🗺 State Analysis
**Purpose:** Supply chain and regional marketing

| Pivot Structure | Rows | Values |
|---|---|---|
| State Revenue | State | Orders, Revenue, AOV, Revenue Share % |

**Chart:** Horizontal bar for top 8 states. Conditional formatting creates heat-map effect on Revenue column.

### Sheet 5: 📋 Data Dictionary
**Purpose:** Self-documenting workbook for stakeholders

Full table-column-type-description reference with examples.

**Dashboard Design Principles Used:**
- **Header row**: Dark navy (`#1F4E79`) with white text
- **Alternating rows**: Light blue tint for readability
- **KPI tiles**: Accent blue with large, bold values
- **Currency format**: `₹#,##0` throughout
- **No gridlines** in any sheet (clean look)

---

## 7. Power BI Dashboard Design

### Page Layout (3 Pages)

#### Page 1: Revenue Overview
| Position | Visual | Fields |
|---|---|---|
| Top strip | 4 KPI Cards | Total Revenue, Orders, AOV, Active Customers |
| Left (large) | Line Chart | Revenue by Month, with slicer for Year |
| Right top | Donut Chart | Revenue by Category |
| Right bottom | Bar Chart | Revenue by Channel |
| Bottom | Matrix | Year × Quarter revenue with conditional formatting |

#### Page 2: Customer Intelligence
| Position | Visual | Fields |
|---|---|---|
| Top | 3 KPI Cards | Total Customers, Champions count, Churn Risk count |
| Left | Scatter Plot | Frequency vs Monetary, coloured by RFM Segment |
| Right top | Treemap | Customer count by RFM Segment |
| Right bottom | Bar | Top 10 customers by CLV |
| Bottom | Map | Customer density by State |

#### Page 3: Product & Returns
| Position | Visual | Fields |
|---|---|---|
| Top | 3 KPI Cards | Total Products, Return Rate, Best Margin Category |
| Left | Bar Chart | Top 10 products by revenue |
| Right | Bar Chart | Return rate by category |
| Bottom left | Table | Product-level: Revenue, Margin, Units Sold |
| Bottom right | Bar | Return reasons distribution |

---

### DAX Measures (5 Core Measures)

#### Measure 1: Total Revenue
```dax
Total Revenue =
CALCULATE(
    SUMX(orders, orders[total_amount]),
    orders[status] = "Delivered"
)
```
**Explanation:** Uses CALCULATE with a filter to sum only delivered orders. SUMX iterates row-by-row, enabling future context modifications.

---

#### Measure 2: Month-over-Month Growth %
```dax
MoM Growth % =
VAR CurrentMonth = [Total Revenue]
VAR PrevMonth =
    CALCULATE(
        [Total Revenue],
        DATEADD(orders[order_date], -1, MONTH)
    )
RETURN
    DIVIDE(CurrentMonth - PrevMonth, PrevMonth, 0)
```
**Explanation:** Uses DATEADD for time intelligence. DIVIDE handles division-by-zero gracefully. Shows as percentage with format `0.0%`.

---

#### Measure 3: Average Order Value (AOV)
```dax
AOV =
DIVIDE(
    CALCULATE(SUM(orders[total_amount]), orders[status] = "Delivered"),
    CALCULATE(COUNTROWS(orders),        orders[status] = "Delivered"),
    0
)
```
**Explanation:** Explicitly filters to delivered orders in both numerator and denominator. More reliable than AVERAGE which counts all rows.

---

#### Measure 4: Customer Lifetime Value (CLV)
```dax
CLV =
DIVIDE(
    CALCULATE(SUM(orders[total_amount]), orders[status] = "Delivered"),
    DISTINCTCOUNT(orders[customer_id]),
    0
)
```
**Explanation:** Total delivered revenue divided by distinct customers. Place on a visual filtered by segment or date to see CLV in context.

---

#### Measure 5: Return Rate %
```dax
Return Rate % =
VAR ReturnedOrders =
    CALCULATE(COUNTROWS(orders), orders[status] = "Returned")
VAR TotalOrders =
    CALCULATE(COUNTROWS(orders),
              orders[status] IN {"Delivered","Returned"})
RETURN
    DIVIDE(ReturnedOrders, TotalOrders, 0)
```
**Explanation:** Scopes the denominator to meaningful orders only (excluding cancelled/processing), giving an accurate return rate from fulfilled orders.

---

### Slicer & Filter Recommendations

| Slicer | Type | Purpose |
|---|---|---|
| Date (order_date) | Date Range / Relative | Filter all visuals to time period |
| Year | Single-select dropdown | Year-over-year comparison |
| Customer Segment | Multi-select checkbox | Premium vs Regular vs Budget |
| Category | Multi-select checkbox | Product-level drill-down |
| State | Dropdown / Map click | Geographic filtering |
| Order Status | Multi-select | Exclude cancelled in ad-hoc |
| Channel | Single select | Mobile App vs Website analysis |

**Recommended Interactions:**
- Cross-filtering ON between all visuals on each page
- Drill-through from Category donut → Product detail table
- Tooltip page showing customer RFM stats on hover

### Key Insights the Dashboard Reveals
1. **Revenue seasonality** — Q4 (Oct–Dec) consistently outperforms Q1 by 20–35%
2. **Champion segment punch above weight** — top 20% customers = ~60% revenue
3. **Electronics margin risk** — highest revenue but lowest margin; needs review
4. **Mobile App dominates** — 50% of orders but similar AOV to web; invest in app UX
5. **Maharashtra + Karnataka = 40% revenue** — regional concentration risk

---

