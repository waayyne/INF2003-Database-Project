# GlowBase

GlowBase is a **Beauty Product Analytics and Review System** for the **INF2003 Database Systems** group project.

The project demonstrates how one web application can use both:

- **MariaDB** for structured relational product data
- **MongoDB** for flexible review document data

The website is built with:

- Flask
- HTML / CSS
- MariaDB
- MongoDB

---

## 1. Project Overview

GlowBase allows public users to:

- View beauty products
- Search and filter products
- View product details
- View product reviews
- Submit product reviews without logging in
- View analytics dashboard

Admin users can:

- Login to the admin dashboard
- Manage products
- Add products
- Edit products
- Delete products
- Manage reviews
- Edit reviews
- Delete reviews
- View SQL nested query demo
- View SQL trigger demo
- View SQL view and index demo

---

## 2. Current System Status

Current version:

```text
Flask + MariaDB + MongoDB
```

Current database split:

```text
MariaDB → Products, brands, categories, product ingredients, product highlights
MongoDB → Product reviews
```

The old CSV/pandas version was only used during early frontend testing. The current application no longer depends on CSV files for the main website runtime.

---

## 3. Database Split

### MariaDB

MariaDB stores structured product data because the data has clear relationships.

Main tables:

```text
products
brands
categories
product_categories
product_ingredients
product_highlights
product_add_logs
```

Purpose:

```text
products              → stores main product details
brands                → stores brand names
categories            → stores product category values
product_categories    → links products to categories
product_ingredients   → stores product ingredients
product_highlights    → stores product highlights
product_add_logs      → stores trigger audit logs when products are inserted
```

### MongoDB

MongoDB stores product reviews because review documents can have optional and flexible fields.

Collection:

```text
reviews
```

Example review fields:

```text
product_id
product_name
brand_name
rating
is_recommended
review_title
review_text
skin_type
skin_tone
submission_time
```

---

## 4. Completed Requirements

| Requirement | Status | Where it is shown |
|---|---:|---|
| Web application | Done | Flask routes and HTML templates |
| Relational database | Done | MariaDB |
| NoSQL database | Done | MongoDB |
| At least 3 SQL tables | Done | products, brands, categories, etc. |
| SQL Create | Done | Admin Add Product |
| SQL Read | Done | Products page, product details, analytics |
| SQL Update | Done | Admin Edit Product |
| SQL Delete | Done | Admin Delete Product |
| NoSQL Create | Done | Submit Review |
| NoSQL Read | Done | Reviews page and Admin Manage Reviews |
| NoSQL Update | Done | Admin Edit Review |
| NoSQL Delete | Done | Admin Delete Review |
| Nested queries | Done | SQL Demo page |
| SQL trigger | Done | Trigger Demo page and product_add_logs |
| SQL view | Done | product_summary_view |
| SQL indexes | Done | Product table indexes |
| Search/filter | Done | Products page and Manage Reviews page |
| Admin dashboard | Done | /admin/dashboard |
| GenAI reflection | To include in report | Report section |
| ER diagram | To include in report | Report section |
| Screenshots/evidence | To include in report | Report appendix/evidence section |

---

## 5. Website Routes

### Public Routes

```text
/
/products
/product/<product_id>
/reviews
/submit-review
/analytics
```

### Admin Routes

```text
/admin/login
/admin/logout
/admin/dashboard
/admin/products
/admin/products/add
/admin/products/edit/<product_id>
/admin/products/delete/<product_id>
/admin/reviews
/admin/reviews/edit/<review_id>
/admin/reviews/delete/<review_id>
/admin/sql-demo
/admin/trigger-demo
/admin/view-index-demo
```

Temporary admin login:

```text
Username: admin
Password: admin123
```

This is for project demo only. A stronger production version should store admin users in MariaDB and use password hashing.

---

## 6. Key Features

### Public Features

```text
Home page
Product listing
Product search
Product filtering by brand, category, rating, and price
Product detail page
Related product reviews
Review listing
Submit review form
Analytics dashboard
```

### Admin Features

```text
Admin login/logout
Admin dashboard
Add product
Edit product
Delete product with confirmation alert
Manage reviews
Filter reviews by search, product ID, brand, rating, recommendation, and limit
Edit MongoDB review document
Delete MongoDB review document with confirmation alert
SQL nested query demo
SQL trigger demo
SQL view and index demo
```

---

## 7. Database Features Implemented

### 7.1 SQL CRUD

| CRUD Operation | Feature |
|---|---|
| Create | Admin add product |
| Read | Product listing, product details, analytics |
| Update | Admin edit product |
| Delete | Admin delete product |

SQL Update example used in the application:

```sql
UPDATE products
SET product_name = %s,
    price_usd = %s,
    rating = %s,
    size = %s,
    out_of_stock = %s
WHERE product_id = %s;
```

### 7.2 NoSQL CRUD

| CRUD Operation | Feature |
|---|---|
| Create | Submit review |
| Read | Reviews page and Admin Manage Reviews |
| Update | Admin edit review |
| Delete | Admin delete review |

MongoDB update example used in the application:

```python
reviews_collection.update_one(
    {"_id": ObjectId(review_id)},
    {"$set": {
        "rating": int(rating),
        "is_recommended": int(is_recommended),
        "review_title": review_title,
        "review_text": review_text
    }}
)
```

MongoDB delete example used in the application:

```python
reviews_collection.delete_one({"_id": ObjectId(review_id)})
```

### 7.3 Nested Queries

Nested queries are shown in:

```text
/admin/sql-demo
```

Examples include:

```sql
SELECT p.product_id, p.product_name, b.brand_name, p.rating, p.price_usd
FROM products p, brands b
WHERE p.brand_id = b.brand_id
AND p.rating > (
    SELECT AVG(rating)
    FROM products
)
ORDER BY p.rating DESC
LIMIT 20;
```

```sql
SELECT p.product_id, p.product_name, b.brand_name, p.rating, p.price_usd
FROM products p, brands b
WHERE p.brand_id = b.brand_id
AND p.brand_id IN (
    SELECT brand_id
    FROM products
    GROUP BY brand_id
    HAVING COUNT(*) > 3
)
ORDER BY b.brand_name, p.product_name
LIMIT 20;
```

### 7.4 SQL Trigger

Trigger demo is shown in:

```text
/admin/trigger-demo
```

Trigger used:

```sql
CREATE TRIGGER after_product_insert
AFTER INSERT ON products
FOR EACH ROW
BEGIN
    INSERT INTO product_add_logs (
        product_id,
        product_name,
        action_type
    )
    VALUES (
        NEW.product_id,
        NEW.product_name,
        'INSERT'
    );
END;
```

Purpose:

```text
When an admin adds a new product, MariaDB automatically inserts an audit log into product_add_logs.
```

### 7.5 SQL View

View demo is shown in:

```text
/admin/view-index-demo
```

View used:

```sql
CREATE VIEW product_summary_view AS
SELECT
    p.product_id,
    p.product_name,
    b.brand_name,
    p.price_usd,
    p.rating,
    p.reviews,
    p.loves_count,
    p.out_of_stock
FROM products p, brands b
WHERE p.brand_id = b.brand_id;
```

Purpose:

```text
The view combines product and brand data into one virtual table, making repeated product queries easier to write.
```

### 7.6 SQL Indexes

Indexes are shown in:

```text
/admin/view-index-demo
```

Indexes used:

```sql
CREATE INDEX idx_products_product_name ON products(product_name);
CREATE INDEX idx_products_brand_id ON products(brand_id);
CREATE INDEX idx_products_rating ON products(rating);
CREATE INDEX idx_products_price ON products(price_usd);
```

Purpose:

```text
Indexes are created on frequently searched, filtered, and joined columns to improve query performance.
```

Note:

```text
The PRIMARY index on product_id is automatically created because product_id is the primary key.
```

---

## 8. Folder Structure

```text
glowbase/
│   app.py
│   db.py
│   requirements.txt
│   .env
│   .gitignore
│   README.md
│   glowbasev1.sql
│   glowbase.reviews.json
│   sql_features_triggers.sql
│   sql_features_views_indexes.sql
│
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
│
└── templates/
    ├── base.html
    ├── index.html
    ├── products.html
    ├── product_detail.html
    ├── reviews.html
    ├── submit_review.html
    ├── analytics.html
    ├── admin_login.html
    ├── admin_dashboard.html
    ├── admin_products.html
    ├── admin_add_product.html
    ├── admin_edit_product.html
    ├── admin_reviews.html
    ├── admin_edit_review.html
    ├── sql_demo.html
    ├── trigger_demo.html
    └── view_index_demo.html
```

Important:

```text
.env should not be pushed to GitHub.
venv should not be pushed to GitHub.
Large raw dataset files should not be pushed to GitHub unless required by submission instructions.
```

---

## 9. Requirements

Recommended `requirements.txt`:

```text
flask
mysql-connector-python
pymongo
python-dotenv
```

Optional:

```text
pandas
```

Pandas is not needed for the main website runtime anymore, but it can still be used for data cleaning or import scripts.

Install packages:

```bash
py -m pip install flask mysql-connector-python pymongo python-dotenv
```

or:

```bash
pip install -r requirements.txt
```

---

## 10. Environment Variables

Create a `.env` file in the project root.

Example:

```env
MARIADB_HOST=localhost
MARIADB_USER=root
MARIADB_PASSWORD=your_password
MARIADB_DATABASE=glowbase

MONGO_URI=mongodb://localhost:27017/
MONGO_DATABASE=glowbase
MONGO_REVIEWS_COLLECTION=reviews
```

Do not push `.env` to GitHub.

---

## 11. Database Setup

### 11.1 Import MariaDB schema/data

From the project root:

```bat
"C:\Program Files\MariaDB 12.2\bin\mariadb.exe" -u root -p glowbase < glowbasev1.sql
```

If the database does not exist yet, first login to MariaDB and run:

```sql
CREATE DATABASE glowbase;
```

### 11.2 Import MongoDB reviews

Use MongoDB Compass or `mongoimport`.

Example using `mongoimport`:

```bash
mongoimport --db glowbase --collection reviews --file glowbase.reviews.json --jsonArray
```

### 11.3 Add SQL trigger

Run:

```bat
"C:\Program Files\MariaDB 12.2\bin\mariadb.exe" -u root -p glowbase < sql_features_triggers.sql
```

Check:

```sql
SHOW TRIGGERS;
```

### 11.4 Add SQL view and indexes

Run:

```bat
"C:\Program Files\MariaDB 12.2\bin\mariadb.exe" -u root -p glowbase < sql_features_views_indexes.sql
```

Check:

```sql
SHOW FULL TABLES WHERE Table_type = 'VIEW';
SHOW INDEX FROM products;
```

---

## 12. How to Run

### Windows

Open Command Prompt in the project folder:

```bat
cd C:\Users\USER\Documents\GitHub\INF2003-Database-Project\glowbase
```

Run:

```bat
py app.py
```

Open:

```text
http://127.0.0.1:5000/
```

### macOS

Open Terminal in the project folder:

```bash
python3 app.py
```

Open:

```text
http://127.0.0.1:5000/
```

---

## 13. Useful Demo Pages

```text
http://127.0.0.1:5000/
http://127.0.0.1:5000/products
http://127.0.0.1:5000/reviews
http://127.0.0.1:5000/submit-review
http://127.0.0.1:5000/analytics
http://127.0.0.1:5000/admin/login
http://127.0.0.1:5000/admin/dashboard
http://127.0.0.1:5000/admin/products
http://127.0.0.1:5000/admin/reviews
http://127.0.0.1:5000/admin/sql-demo
http://127.0.0.1:5000/admin/trigger-demo
http://127.0.0.1:5000/admin/view-index-demo
```

Admin login:

```text
Username: admin
Password: admin123
```

---

## 14. Demo Checklist

Before presenting, prepare screenshots/proof for:

```text
1. Home page
2. Product listing page
3. Product filtering/search
4. Product detail page with MongoDB reviews
5. Submit review form
6. Admin dashboard
7. SQL Create: Add product
8. SQL Read: View products
9. SQL Update: Edit product
10. SQL Delete: Delete product
11. NoSQL Create: Submit review
12. NoSQL Read: Manage reviews / Reviews page
13. NoSQL Update: Edit review
14. NoSQL Delete: Delete review
15. Nested query demo page
16. Trigger demo page
17. View and index demo page
18. MariaDB tables screenshot
19. MongoDB collection screenshot
20. ER diagram
```

---

## 15. GenAI Usage Note

GenAI was used as a support tool for:

```text
- Understanding project requirements
- Planning the MariaDB and MongoDB split
- Debugging Flask, MariaDB, and MongoDB issues
- Refactoring pandas/CSV logic into database queries
- Drafting SQL query examples
- Structuring README and report content
```

The team still verified and modified the generated suggestions based on:

```text
- Actual dataset columns
- Actual MariaDB schema
- Actual MongoDB document fields
- Project requirements
- Application testing results
```

Final implementation decisions, testing, screenshots, and explanations should be completed and checked by the team.

---

## 16. Notes for Team Members

```text
- Start MariaDB before running the app.
- Start MongoDB before running the app.
- Make sure .env values match your local database username/password.
- Do not push .env to GitHub.
- Do not push venv to GitHub.
- If MongoDB reviews do not show, check that MongoDB is running.
- If MariaDB pages fail, check that glowbase database exists and the schema was imported.
- If trigger demo is empty, add a product first.
- If view/index demo fails, run sql_features_views_indexes.sql first.
```

---

## 17. Final Project Status

```text
Coding/database features: complete
Report screenshots/evidence: still need to prepare
ER diagram: still need to include in report
GenAI reflection: still need to include in report
```




To Do:
3. product_categories table has no data
In the SQL dump, the product_categories junction table is empty — INSERT block is blank. This means the many-to-many relationship between products and categories exists in schema but has no actual data showing it. This weakens your ER diagram story. You should either populate it or explain why in the report.
4. Only one trigger
You have after_product_insert but no trigger for UPDATE or DELETE. Not strictly required, but having only an INSERT trigger is minimal. Consider adding an after_product_delete trigger that also logs to product_add_logs with action_type 'DELETE' — it's a small addition that makes the feature much stronger.
5. MongoDB CRUD is missing a dedicated NoSQL Update from the public side
The only NoSQL update (update_one) is in the admin panel. That's fine, but worth noting — public users can only create (submit review) and read. Make sure your report highlights the admin-side update/delete for MongoDB.
6. No performance analysis / query comparison
The project description says this is optional but notes it can impress. The sql_demo page shows nested queries but doesn't quantify speed or compare query plans. Even one EXPLAIN output in the report comparing with/without indexes would be a nice touch for the 40% Database mark.
7. Admin password is hardcoded in app.py
admin123 is hardcoded. Mention in your report this is demo-only and that a real system would store hashed credentials in MariaDB.


add in when user filter the query display the SQL Statement on the website as well.