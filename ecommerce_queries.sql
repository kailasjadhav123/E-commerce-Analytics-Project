-- E-COMMERCE ANALYTICS PROJECT — SQL SCRIPTS /-----------

-- SECTION 1: DDL — TABLE CREATION /---------

CREATE TABLE IF NOT EXISTS customers (
    customer_id       INTEGER PRIMARY KEY,
    first_name        TEXT    NOT NULL,
    last_name         TEXT    NOT NULL,
    email             TEXT    UNIQUE NOT NULL,
    phone             TEXT,
    city              TEXT,
    state             TEXT,
    pincode           TEXT,
    segment           TEXT    CHECK(segment IN ('Premium','Regular','Budget')),
    registration_date DATE    NOT NULL,
    is_active         INTEGER DEFAULT 1 CHECK(is_active IN (0,1))
);

CREATE TABLE IF NOT EXISTS products (
    product_id   INTEGER PRIMARY KEY,
    product_name TEXT    NOT NULL,
    category     TEXT    NOT NULL,
    brand        TEXT,
    unit_price   REAL    NOT NULL CHECK(unit_price > 0),
    cost_price   REAL    NOT NULL CHECK(cost_price > 0),
    stock_qty    INTEGER DEFAULT 0,
    is_active    INTEGER DEFAULT 1 CHECK(is_active IN (0,1))
);

CREATE TABLE IF NOT EXISTS orders (
    order_id      INTEGER PRIMARY KEY,
    customer_id   INTEGER NOT NULL REFERENCES customers(customer_id),
    order_date    DATE    NOT NULL,
    status        TEXT    CHECK(status IN ('Delivered','Shipped','Cancelled','Returned','Processing')),
    payment_mode  TEXT,
    channel       TEXT,
    discount_pct  REAL    DEFAULT 0,
    shipping_cost REAL    DEFAULT 0,
    total_amount  REAL,
    city          TEXT,
    state         TEXT
);

CREATE TABLE IF NOT EXISTS order_items (
    item_id      INTEGER PRIMARY KEY,
    order_id     INTEGER NOT NULL REFERENCES orders(order_id),
    product_id   INTEGER NOT NULL REFERENCES products(product_id),
    quantity     INTEGER NOT NULL CHECK(quantity > 0),
    unit_price   REAL    NOT NULL,
    discount_pct REAL    DEFAULT 0,
    line_revenue REAL    NOT NULL
);

CREATE TABLE IF NOT EXISTS returns (
    return_id     INTEGER PRIMARY KEY,
    order_id      INTEGER NOT NULL REFERENCES orders(order_id),
    return_date   DATE    NOT NULL,
    reason        TEXT,
    refund_amount REAL,
    status        TEXT    CHECK(status IN ('Approved','Pending','Rejected'))
);


CREATE INDEX IF NOT EXISTS idx_orders_customer   ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_date       ON orders(order_date);
CREATE INDEX IF NOT EXISTS idx_items_order       ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_items_product     ON order_items(product_id);
CREATE INDEX IF NOT EXISTS idx_returns_order     ON returns(order_id);



-- SECTION 2: DATA CLEANING & NULL HANDLING /--------------
SELECT
    'customers'       AS tbl,
    SUM(CASE WHEN email   IS NULL THEN 1 ELSE 0 END) AS null_email,
    SUM(CASE WHEN city    IS NULL THEN 1 ELSE 0 END) AS null_city,
    SUM(CASE WHEN segment IS NULL THEN 1 ELSE 0 END) AS null_segment
FROM customers
UNION ALL
SELECT
    'orders',
    SUM(CASE WHEN total_amount IS NULL THEN 1 ELSE 0 END),
    SUM(CASE WHEN payment_mode IS NULL THEN 1 ELSE 0 END),
    SUM(CASE WHEN channel      IS NULL THEN 1 ELSE 0 END)
FROM orders;

-- Replace NULL 
UPDATE orders
SET total_amount = 0
WHERE total_amount IS NULL;

--Flag outlier orders
WITH stats AS (
    SELECT AVG(total_amount) AS avg_amt,
           AVG(total_amount * total_amount) - AVG(total_amount)*AVG(total_amount) AS var_amt
    FROM orders WHERE status = 'Delivered'
)
SELECT order_id, total_amount,
       ROUND((total_amount - avg_amt) / SQRT(var_amt), 2) AS z_score
FROM orders, stats
WHERE ABS((total_amount - avg_amt) / SQRT(var_amt)) > 3
  AND status = 'Delivered';

-- Duplicate order 
SELECT order_id, COUNT(*) AS cnt
FROM orders
GROUP BY order_id
HAVING cnt > 1;

- Orphaned order items
SELECT oi.item_id, oi.order_id
FROM order_items oi
LEFT JOIN orders o ON oi.order_id = o.order_id
WHERE o.order_id IS NULL;

-- SECTION 3: EXPLORATORY DATA ANALYSIS /--------

--  Orders by status
SELECT status,
       COUNT(*)                              AS order_count,
       ROUND(100.0*COUNT(*)/SUM(COUNT(*)) OVER(),1) AS pct
FROM orders
GROUP BY status
ORDER BY order_count DESC;

-- Revenue by category
SELECT p.category,
       COUNT(DISTINCT oi.order_id)           AS orders,
       SUM(oi.quantity)                      AS units_sold,
       ROUND(SUM(oi.line_revenue),2)         AS total_revenue,
       ROUND(AVG(oi.unit_price),2)           AS avg_price
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
JOIN orders   o ON oi.order_id   = o.order_id
WHERE o.status = 'Delivered'
GROUP BY p.category
ORDER BY total_revenue DESC;

- Customer distribution 
SELECT segment, state, COUNT(*) AS customers
FROM customers
GROUP BY segment, state
ORDER BY customers DESC
LIMIT 20;

--  Payment mode analysis
SELECT payment_mode,
       COUNT(*)                              AS order_count,
       ROUND(SUM(total_amount),2)            AS total_gmv,
       ROUND(AVG(total_amount),2)            AS avg_order_value
FROM orders
WHERE status NOT IN ('Cancelled')
GROUP BY payment_mode
ORDER BY total_gmv DESC;

SELECT channel,
       COUNT(*)                              AS orders,
       ROUND(SUM(total_amount),2)            AS revenue,
       ROUND(AVG(total_amount),2)            AS aov
FROM orders
WHERE status = 'Delivered'
GROUP BY channel;

-- Poducts by revenue
SELECT p.product_name, p.category, p.brand,
       SUM(oi.quantity)              AS units_sold,
       ROUND(SUM(oi.line_revenue),2) AS revenue,
       ROUND(AVG(oi.unit_price),2)   AS avg_price
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
JOIN orders   o ON oi.order_id   = o.order_id
WHERE o.status = 'Delivered'
GROUP BY p.product_id
ORDER BY revenue DESC
LIMIT 10;

-- SECTION 4: KPI CALCULATIONS / -----------------

-- Overall Business KPIs
SELECT
    COUNT(DISTINCT o.order_id)                         AS total_orders,
    COUNT(DISTINCT o.customer_id)                      AS unique_customers,
    ROUND(SUM(o.total_amount), 2)                      AS gross_revenue,
    ROUND(AVG(o.total_amount), 2)                      AS avg_order_value,
    ROUND(SUM(oi.quantity), 0)                         AS total_units_sold,
    ROUND(SUM(o.total_amount) / COUNT(DISTINCT o.customer_id), 2) AS revenue_per_customer
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.status = 'Delivered';

SELECT
    ROUND(SUM(oi.line_revenue), 2)                                   AS revenue,
    ROUND(SUM(oi.quantity * p.cost_price), 2)                        AS cogs,
    ROUND(SUM(oi.line_revenue) - SUM(oi.quantity * p.cost_price), 2) AS gross_profit,
    ROUND(100.0 * (SUM(oi.line_revenue) - SUM(oi.quantity * p.cost_price))
          / NULLIF(SUM(oi.line_revenue), 0), 1)                      AS gross_margin_pct
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
JOIN orders   o ON oi.order_id   = o.order_id
WHERE o.status = 'Delivered';

SELECT
    COUNT(DISTINCT o.order_id)                                AS delivered_orders,
    COUNT(DISTINCT r.return_id)                               AS returned_orders,
    ROUND(100.0 * COUNT(DISTINCT r.return_id)
          / NULLIF(COUNT(DISTINCT o.order_id), 0), 2)        AS return_rate_pct
FROM orders o
LEFT JOIN returns r ON o.order_id = r.order_id
WHERE o.status IN ('Delivered','Returned');

-- Customer Lifetime Value 
SELECT
    c.segment,
    COUNT(DISTINCT c.customer_id)               AS customers,
    ROUND(AVG(cust_stats.order_count), 1)       AS avg_orders,
    ROUND(AVG(cust_stats.total_spent), 2)       AS avg_clv,
    ROUND(MAX(cust_stats.total_spent), 2)       AS max_clv
FROM customers c
JOIN (
    SELECT customer_id,
           COUNT(order_id)       AS order_count,
           SUM(total_amount)     AS total_spent
    FROM orders
    WHERE status = 'Delivered'
    GROUP BY customer_id
) cust_stats ON c.customer_id = cust_stats.customer_id
GROUP BY c.segment
ORDER BY avg_clv DESC;

-- Discount impact 
SELECT
    CASE
        WHEN discount_pct = 0    THEN 'No Discount'
        WHEN discount_pct <= 0.1 THEN 'Up to 10%'
        WHEN discount_pct <= 0.2 THEN '11-20%'
        ELSE 'Above 20%'
    END                              AS discount_band,
    COUNT(*)                         AS orders,
    ROUND(AVG(total_amount), 2)      AS avg_order_value,
    ROUND(SUM(total_amount), 2)      AS total_revenue
FROM orders
WHERE status = 'Delivered'
GROUP BY discount_band
ORDER BY total_revenue DESC;

-- SECTION 5: CUSTOMER SEGMENTATION — RFM ANALYSIS /---------------

--  Calculate RFM 
WITH rfm_base AS (
    SELECT
        c.customer_id,
        c.first_name || ' ' || c.last_name         AS customer_name,
        c.segment,
        MAX(o.order_date)                           AS last_order_date,
        CAST(JULIANDAY('2025-01-01') -
             JULIANDAY(MAX(o.order_date)) AS INT)   AS recency_days,
        COUNT(DISTINCT o.order_id)                  AS frequency,
        ROUND(SUM(o.total_amount), 2)               AS monetary
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    WHERE o.status = 'Delivered'
    GROUP BY c.customer_id
),
rfm_ranked AS (
    SELECT *,
        NTILE(5) OVER (ORDER BY recency_days ASC)  AS r_score,
        NTILE(5) OVER (ORDER BY frequency DESC)    AS f_score,
        NTILE(5) OVER (ORDER BY monetary DESC)     AS m_score
    FROM rfm_base
),
rfm_scored AS (
    SELECT *,
        (r_score + f_score + m_score)              AS rfm_total,
        CAST(r_score AS TEXT) || CAST(f_score AS TEXT) || CAST(m_score AS TEXT) AS rfm_cell
    FROM rfm_ranked
)
SELECT *,
    CASE
        WHEN rfm_total >= 13 THEN 'Champions'
        WHEN rfm_total >= 10 THEN 'Loyal Customers'
        WHEN rfm_total >= 8  THEN 'Potential Loyalists'
        WHEN rfm_total >= 6  THEN 'At Risk'
        WHEN r_score <= 2    THEN 'Lost Customers'
        ELSE 'Need Attention'
    END AS rfm_segment
FROM rfm_scored
ORDER BY rfm_total DESC;

-- RFM segment 
WITH rfm_base AS (
    SELECT customer_id,
           MAX(order_date)                                            AS last_order,
           CAST(JULIANDAY('2025-01-01')-JULIANDAY(MAX(order_date)) AS INT) AS recency_days,
           COUNT(DISTINCT order_id)                                   AS frequency,
           SUM(total_amount)                                          AS monetary
    FROM orders WHERE status='Delivered' GROUP BY customer_id
),
rfm_scored AS (
    SELECT *,
        NTILE(5) OVER (ORDER BY recency_days ASC)  AS r,
        NTILE(5) OVER (ORDER BY frequency DESC)    AS f,
        NTILE(5) OVER (ORDER BY monetary DESC)     AS m
    FROM rfm_base
),
rfm_seg AS (
    SELECT *, (r+f+m) AS total,
        CASE WHEN (r+f+m)>=13 THEN 'Champions'
             WHEN (r+f+m)>=10 THEN 'Loyal Customers'
             WHEN (r+f+m)>=8  THEN 'Potential Loyalists'
             WHEN (r+f+m)>=6  THEN 'At Risk'
             WHEN r<=2        THEN 'Lost Customers'
             ELSE 'Need Attention' END AS rfm_segment
    FROM rfm_scored
)
SELECT rfm_segment,
       COUNT(*)                        AS customers,
       ROUND(AVG(recency_days),0)      AS avg_recency,
       ROUND(AVG(frequency),1)         AS avg_frequency,
       ROUND(AVG(monetary),2)          AS avg_monetary,
       ROUND(SUM(monetary),2)          AS total_revenue
FROM rfm_seg
GROUP BY rfm_segment
ORDER BY total_revenue DESC;

-- SECTION 6: TREND ANALYSIS  /-----------------------

-- Monthly Revenue
SELECT
    STRFTIME('%Y',  order_date)                         AS year,
    STRFTIME('%m',  order_date)                         AS month,
    STRFTIME('%Y-%m', order_date)                       AS year_month,
    COUNT(DISTINCT order_id)                            AS orders,
    ROUND(SUM(total_amount), 2)                         AS revenue,
    ROUND(AVG(total_amount), 2)                         AS aov
FROM orders
WHERE status = 'Delivered'
GROUP BY year_month
ORDER BY year_month;

-- Month Growth
WITH monthly AS (
    SELECT STRFTIME('%Y-%m', order_date)    AS ym,
           SUM(total_amount)                AS revenue
    FROM orders WHERE status='Delivered'
    GROUP BY ym
),
mom AS (
    SELECT ym, revenue,
           LAG(revenue) OVER (ORDER BY ym) AS prev_month_revenue
    FROM monthly
)
SELECT ym,
       ROUND(revenue, 2)                                              AS revenue,
       ROUND(prev_month_revenue, 2)                                   AS prev_revenue,
       ROUND(100.0*(revenue - prev_month_revenue)/
             NULLIF(prev_month_revenue,0), 1)                         AS mom_growth_pct
FROM mom
ORDER BY ym;

-- Year Revenue 
WITH yearly AS (
    SELECT STRFTIME('%Y', order_date)    AS yr,
           COUNT(DISTINCT order_id)      AS orders,
           ROUND(SUM(total_amount), 2)   AS revenue,
           ROUND(AVG(total_amount), 2)   AS aov,
           COUNT(DISTINCT customer_id)   AS unique_customers
    FROM orders
    WHERE status = 'Delivered'
    GROUP BY yr
)
SELECT yr, orders, revenue, aov, unique_customers,
       ROUND(100.0*(revenue - LAG(revenue) OVER (ORDER BY yr))/
             NULLIF(LAG(revenue) OVER (ORDER BY yr),0), 1) AS yoy_growth_pct
FROM yearly;

-- Quarterly Performance
SELECT
    STRFTIME('%Y', order_date)    AS year,
    CASE STRFTIME('%m', order_date)
        WHEN '01' THEN 'Q1' WHEN '02' THEN 'Q1' WHEN '03' THEN 'Q1'
        WHEN '04' THEN 'Q2' WHEN '05' THEN 'Q2' WHEN '06' THEN 'Q2'
        WHEN '07' THEN 'Q3' WHEN '08' THEN 'Q3' WHEN '09' THEN 'Q3'
        ELSE 'Q4' END             AS quarter,
    COUNT(DISTINCT order_id)      AS orders,
    ROUND(SUM(total_amount),2)    AS revenue
FROM orders
WHERE status='Delivered'
GROUP BY year, quarter
ORDER BY year, quarter;

-- Cohort Analysis — customer retention
WITH first_order AS (
    SELECT customer_id, MIN(order_date) AS first_order_date
    FROM orders WHERE status='Delivered'
    GROUP BY customer_id
),
cohort AS (
    SELECT fo.customer_id,
           STRFTIME('%Y-%m', fo.first_order_date) AS cohort_month,
           STRFTIME('%Y-%m', o.order_date)         AS order_month
    FROM first_order fo
    JOIN orders o ON fo.customer_id = o.customer_id AND o.status='Delivered'
),
cohort_size AS (
    SELECT cohort_month, COUNT(DISTINCT customer_id) AS cohort_customers
    FROM cohort GROUP BY cohort_month
)
SELECT c.cohort_month,
       cs.cohort_customers,
       c.order_month,
       COUNT(DISTINCT c.customer_id) AS active_customers,
       ROUND(100.0*COUNT(DISTINCT c.customer_id)/cs.cohort_customers,1) AS retention_pct
FROM cohort c
JOIN cohort_size cs ON c.cohort_month = cs.cohort_month
GROUP BY c.cohort_month, c.order_month
ORDER BY c.cohort_month, c.order_month
LIMIT 50;

-- SECTION 7: TOP-N BUSINESS INSIGHTS /-----------------

-- States by revenue
SELECT state,
       COUNT(DISTINCT customer_id)          AS customers,
       COUNT(DISTINCT order_id)             AS orders,
       ROUND(SUM(total_amount), 2)          AS revenue,
       ROUND(AVG(total_amount), 2)          AS aov
FROM orders
WHERE status = 'Delivered'
GROUP BY state
ORDER BY revenue DESC
LIMIT 5;

-- Customers by lifetime value
SELECT c.customer_id,
       c.first_name || ' ' || c.last_name  AS name,
       c.segment, c.city,
       COUNT(DISTINCT o.order_id)          AS total_orders,
       ROUND(SUM(o.total_amount), 2)       AS lifetime_value,
       ROUND(AVG(o.total_amount), 2)       AS avg_order_value,
       MAX(o.order_date)                   AS last_order_date
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
WHERE o.status = 'Delivered'
GROUP BY c.customer_id
ORDER BY lifetime_value DESC
LIMIT 10;

-- Products with highest return rate
SELECT p.product_name, p.category,
       COUNT(DISTINCT oi.order_id)         AS total_orders,
       COUNT(DISTINCT r.return_id)         AS returns,
       ROUND(100.0*COUNT(DISTINCT r.return_id)/
             NULLIF(COUNT(DISTINCT oi.order_id),0), 1) AS return_rate_pct
FROM products p
JOIN order_items oi ON p.product_id = oi.product_id
JOIN orders      o  ON oi.order_id  = o.order_id
LEFT JOIN returns r ON o.order_id   = r.order_id
WHERE o.status IN ('Delivered','Returned')
GROUP BY p.product_id
HAVING total_orders >= 5
ORDER BY return_rate_pct DESC
LIMIT 10;

--  Peak ordering 
SELECT
    CASE STRFTIME('%w', order_date)
        WHEN '0' THEN 'Sunday'   WHEN '1' THEN 'Monday'
        WHEN '2' THEN 'Tuesday'  WHEN '3' THEN 'Wednesday'
        WHEN '4' THEN 'Thursday' WHEN '5' THEN 'Friday'
        ELSE 'Saturday' END       AS day_of_week,
    COUNT(*)                      AS orders,
    ROUND(SUM(total_amount),2)    AS revenue
FROM orders
WHERE status = 'Delivered'
GROUP BY STRFTIME('%w', order_date)
ORDER BY orders DESC;

-- Repeat customer revenue split
WITH customer_order_rank AS (
    SELECT customer_id, order_id, total_amount,
           ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date) AS order_rank
    FROM orders WHERE status = 'Delivered'
)
SELECT
    CASE WHEN order_rank = 1 THEN 'New Customer' ELSE 'Repeat Customer' END AS customer_type,
    COUNT(*)                         AS orders,
    ROUND(SUM(total_amount), 2)      AS revenue,
    ROUND(AVG(total_amount), 2)      AS aov
FROM customer_order_rank
GROUP BY customer_type;

-- Categories frequently bought together
SELECT a.category AS cat_a, b.category AS cat_b,
       COUNT(*)   AS co_occurrence
FROM order_items oi_a
JOIN products a ON oi_a.product_id = a.product_id
JOIN order_items oi_b ON oi_a.order_id = oi_b.order_id AND oi_a.item_id < oi_b.item_id
JOIN products b ON oi_b.product_id = b.product_id
GROUP BY cat_a, cat_b
ORDER BY co_occurrence DESC
LIMIT 10;
