# GlowBase

GlowBase is a **Beauty Product Analytics and Review System** developed for the **INF2003 Database Systems** group project.

The project demonstrates how a single Flask web application can use both:

- **MariaDB** for structured relational product data
- **MongoDB** for flexible product review documents

---

## 1. Project Overview

GlowBase allows public users to browse beauty products, search and filter product data, view product details, read reviews, submit reviews, and view product analytics.

Admin users can log in to manage product records, manage review documents, and demonstrate database features such as SQL CRUD, NoSQL CRUD, nested queries, triggers, views, and indexes.

---

## 2. Technology Stack

| Layer | Technology |
|---|---|
| Backend | Flask |
| Frontend | HTML, CSS |
| Relational database | MariaDB |
| NoSQL database | MongoDB |
| Environment config | python-dotenv |

---

## 3. Current System Status

Current implementation:

```text
Flask + MariaDB + MongoDB
```

Database split:

```text
MariaDB → Products, brands, categories, product ingredients, product highlights
MongoDB → Product reviews
```

The old CSV/pandas version was only used during early frontend testing. The current application no longer depends on CSV files for the main website runtime.

---

## 4. Database Design

### 4.1 MariaDB

MariaDB stores structured product data because the product dataset has clear relationships between products, brands, categories, ingredients, and highlights.

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

Table purpose:

| Table | Purpose |
|---|---|
| products | Stores main product details |
| brands | Stores brand names |
| categories | Stores product category values |
| product_categories | Links products to categories |
| product_ingredients | Stores product ingredients |
| product_highlights | Stores product highlights |
| product_add_logs | Stores trigger audit logs for product actions |

### 4.2 MongoDB

MongoDB stores product reviews because reviews can contain flexible and optional fields.

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

## 5. Main Features

### 5.1 Public Features

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

### 5.2 Admin Features

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

## 6. Implemented Database Requirements

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
| Screenshots/evidence | To prepare | Report appendix/evidence section |

---

## 7. Website Routes

### 7.1 Public Routes

```text
/
/products
/product/<product_id>
/reviews
/submit-review
/analytics
```

### 7.2 Admin Routes

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

This login is for project demonstration only. A production version should store admin users in the database and use password hashing.

---

## 8. Database Features

### 8.1 SQL CRUD

| CRUD Operation | Feature |
|---|---|
| Create | Admin add product |
| Read | Product listing, product details, analytics |
| Update | Admin edit product |
| Delete | Admin delete product |

Example SQL update used in the application:

```sql
UPDATE products
SET product_name = %s,
    price_usd = %s,
    rating = %s,
    size = %s,
    out_of_stock = %s
WHERE product_id = %s;
```

### 8.2 NoSQL CRUD

| CRUD Operation | Feature |
|---|---|
| Create | Submit review |
| Read | Reviews page and Admin Manage Reviews |
| Update | Admin edit review |
| Delete | Admin delete review |

Example MongoDB update:

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

Example MongoDB delete:

```python
reviews_collection.delete_one({"_id": ObjectId(review_id)})
```

### 8.3 Nested Queries

Nested queries are shown at:

```text
/admin/sql-demo
```

Example 1: Products with rating higher than the average rating.

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

Example 2: Products from brands with more than 3 products.

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

### 8.4 SQL Trigger

Trigger demo is shown at:

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

### 8.5 SQL View

View and index demo is shown at:

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

### 8.6 SQL Indexes

Indexes are shown at:

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

## 9. Project Structure

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

Do not push these files/folders to GitHub:

```text
.env
venv/
__pycache__/
Large raw dataset files unless required by submission instructions
```

---

## 10. Requirements

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

Pandas is not needed for the main website runtime anymore. It can still be used for data cleaning or import scripts.

Install packages manually:

```bash
py -m pip install flask mysql-connector-python pymongo python-dotenv
```

Or install using `requirements.txt`:

```bash
pip install -r requirements.txt
```

---

## 11. Environment Variables

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

## 12. Database Setup

### 12.1 Create MariaDB database

Log in to MariaDB and run:

```sql
CREATE DATABASE glowbase;
```

### 12.2 Import MariaDB schema/data

From the project root:

```bat
"C:\Program Files\MariaDB 12.2\bin\mariadb.exe" -u root -p glowbase < glowbasev1.sql
```

### 12.3 Import MongoDB reviews

Use MongoDB Compass or `mongoimport`.

Example using `mongoimport`:

```bash
mongoimport --db glowbase --collection reviews --file glowbase.reviews.json --jsonArray
```

### 12.4 Add SQL trigger

Run:

```bat
"C:\Program Files\MariaDB 12.2\bin\mariadb.exe" -u root -p glowbase < sql_features_triggers.sql
```

Check:

```sql
SHOW TRIGGERS;
```

### 12.5 Add SQL view and indexes

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

## 13. How to Run

### 13.1 Windows

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

### 13.2 macOS

Open Terminal in the project folder.

Run:

```bash
python3 app.py
```

Open:

```text
http://127.0.0.1:5000/
```

---

## 14. Useful Demo Pages

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

## 15. Demo Checklist

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

## 16. GenAI Usage Note

GenAI was used as a support tool for:

```text
- Understanding project requirements
- Planning the MariaDB and MongoDB split
- Debugging Flask, MariaDB, and MongoDB issues
- Refactoring pandas/CSV logic into database queries
- Drafting SQL query examples
- Structuring README and report content
```

The team verified and modified the generated suggestions based on:

```text
- Actual dataset columns
- Actual MariaDB schema
- Actual MongoDB document fields
- Project requirements
- Application testing results
```

Final implementation decisions, testing, screenshots, and explanations should be completed and checked by the team.

---

## 17. Team Notes

```text
- Start MariaDB before running the app.
- Start MongoDB before running the app.
- Make sure .env values match your local database username/password.
- Do not push .env to GitHub.
- Do not push venv to GitHub.
- If MongoDB reviews do not show, check that MongoDB is running.
- If MariaDB pages fail, check that the glowbase database exists and the schema was imported.
- If trigger demo is empty, add a product first.
- If view/index demo fails, run sql_features_views_indexes.sql first.
```

---

## 18. Final Project Status

```text
Coding/database features: mostly complete
Report screenshots/evidence: still need to prepare
ER diagram: still need to include in report
GenAI reflection: still need to include in report
```

---

# To Do

## 1. Populate or explain the `product_categories` table

The SQL dump currently has no data in the `product_categories` junction table. This means the many-to-many relationship between products and categories exists in the schema, but there is no actual data showing the relationship.

Action:

```text
Either populate product_categories with valid product-category links,
or explain in the report why this table is empty.
```

Why this matters:

```text
An empty junction table weakens the ER diagram explanation because the many-to-many relationship is not demonstrated with real data.
```

---

## 2. Add another SQL trigger

The project currently has `after_product_insert`, but there is no trigger for update or delete.

Suggested improvement:

```text
Add after_product_delete.
```

Example purpose:

```text
When an admin deletes a product, MariaDB automatically inserts a DELETE audit log into product_add_logs.
```

This is not strictly required, but it makes the trigger feature stronger.

---

## 3. Explain MongoDB CRUD clearly in the report

The public side supports:

```text
NoSQL Create → Submit review
NoSQL Read   → View reviews
```

The admin side supports:

```text
NoSQL Update → Edit review
NoSQL Delete → Delete review
```

Important report note:

```text
Public users can create and read reviews.
Admin users handle update and delete actions for MongoDB reviews.
```

This is acceptable, but it should be clearly explained in the report.

---

## 4. Add performance analysis or query comparison

The project has SQL indexes, but the report can be stronger by showing an `EXPLAIN` comparison.

Suggested evidence:

```text
Show EXPLAIN output before and after using indexes,
or explain how indexes help with product filtering/search.
```

This is optional, but it can strengthen the database discussion.

---

## 5. Explain hardcoded admin password

The admin password is currently hardcoded in `app.py`.

Current demo login:

```text
Username: admin
Password: admin123
```

Report explanation:

```text
This is used only for project demonstration. A production version should store admin accounts in MariaDB and use password hashing instead of hardcoding credentials.
```

---

## 6. Display SQL statements when users filter products

When users search or filter products on the website, display the SQL statement used for the query on the page.

Suggested location:

```text
Products page
Admin products page, if filtering is available there
SQL demo page, if needed
```

Purpose:

```text
This helps demonstrate the actual SQL query used by the application when filtering product data.
```

Suggested display format:

```text
SQL statement used:
SELECT ...
FROM ...
WHERE ...
ORDER BY ...
```

Important:

```text
Display a safe demonstration version of the SQL statement.
Do not expose database passwords or sensitive environment values.
```
