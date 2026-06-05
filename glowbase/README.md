# GlowBase

GlowBase is a **Beauty Product Analytics and Review System** built for the INF2003 Database Systems group project. It demonstrates how a single web application can use both a relational database and a NoSQL database together as complementary backends.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Technology Stack](#2-technology-stack)
3. [Database Design](#3-database-design)
4. [Project Structure](#4-project-structure)
5. [Setup and Installation](#5-setup-and-installation)
6. [Running the App](#6-running-the-app)
7. [Website Routes](#7-website-routes)
8. [Database Features](#8-database-features)
9. [Admin Demo Pages](#9-admin-demo-pages)
10. [Environment Variables](#10-environment-variables)
11. [Team Notes](#11-team-notes)

---

## 1. Project Overview

GlowBase allows public users to browse and search beauty products, read and submit reviews, and view product analytics. Admin users can manage products and reviews, and demonstrate all database features through dedicated demo pages.

**Database split:**

| Database | Stores |
|---|---|
| MariaDB | Products, brands, categories, ingredients, highlights, audit logs |
| MongoDB | Product reviews |

This split was intentional. Product data is structured and relational — products belong to brands, belong to categories — so MariaDB fits naturally. Reviews are flexible documents where fields like skin type, skin tone, and chemicals are optional and vary per review, making MongoDB the better choice.

---

## 2. Technology Stack

| Layer | Technology |
|---|---|
| Backend | Flask (Python) |
| Frontend | HTML, CSS |
| Relational database | MariaDB |
| NoSQL database | MongoDB |
| Environment config | python-dotenv |

---

## 3. Database Design

### 3.1 MariaDB Tables

| Table | Purpose |
|---|---|
| `products` | Main product details (name, price, rating, stock status) |
| `brands` | Brand names linked to products |
| `categories` | Category values (primary, secondary, tertiary) |
| `product_categories` | Junction table — links products to categories (many-to-many) |
| `product_ingredients` | Ingredient lists per product |
| `product_highlights` | Highlight tags per product |
| `product_add_logs` | Trigger log for product inserts |
| `product_audit_logs` | Trigger audit log for product updates and deletes |

**Relationships:**
- `products` → `brands` : many-to-one (each product has one brand)
- `products` → `product_categories` → `categories` : many-to-many (a product can belong to multiple categories; a category can have multiple products)
- `products` → `product_ingredients` : one-to-many
- `products` → `product_highlights` : one-to-many

### 3.2 MongoDB Collection

Collection: `reviews`

Example document fields:

```
product_id, product_name, brand_name, rating, is_recommended,
review_title, review_text, skin_type, skin_tone, chemicals, submission_time
```

Fields like `skin_type`, `skin_tone`, and `chemicals` are optional and vary between reviews, which is why MongoDB's document model suits this data better than a rigid SQL table.

---

## 4. Project Structure

```
glowbase/
│   app.py                  # Flask routes and application logic
│   db.py                   # Database connections and auto-bootstrap
│   requirements.txt
│   .env                    # Local credentials (do not push to GitHub)
│
├── data/
│   ├── glowbasev1.sql                      # Main MariaDB schema and data
│   ├── populate_product_categories.sql     # Populates the many-to-many junction table
│   ├── sql_features_triggers.sql           # Trigger definitions
│   ├── sql_features_views_indexes.sql      # View and index definitions
│   ├── glowbase.reviews.json               # MongoDB seed data
│   ├── import_glowbase.bat                 # Windows manual import script
│   └── import_glowbase.sh                  # macOS/Linux manual import script
│
├── static/
│   ├── css/style.css
│   └── js/app.js
│
└── templates/
    ├── base.html
    ├── index.html
    ├── products.html
    ├── product_detail.html
    ├── reviews.html
    ├── submit_review.html
    ├── analytics.html
    ├── chemicals.html
    ├── chemical_products.html
    ├── performance_demo.html
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

---

## 5. Setup and Installation

### 5.1 Prerequisites

- Python 3.10 or later
- MariaDB running locally
- MongoDB running locally

### 5.2 Install Python packages

```bash
pip install flask mysql-connector-python pymongo python-dotenv
```

Or using the requirements file:

```bash
pip install -r requirements.txt
```

### 5.3 Configure environment variables

Create a `.env` file in the project root:

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

### 5.4 Database setup — automatic

The app auto-bootstraps on startup. When you run the app for the first time, `db.py` will:

1. Create the `glowbase` MariaDB database if it does not exist
2. Import `glowbasev1.sql` if the `products` table is missing
3. Run `populate_product_categories.sql` to populate the many-to-many junction table
4. Apply views and indexes from `sql_features_views_indexes.sql`
5. Apply triggers from `sql_features_triggers.sql`
6. Seed MongoDB reviews from `glowbase.reviews.json` if the collection is empty

You only need MariaDB and MongoDB running, and a correct `.env` file.

To disable auto-bootstrap, add this to `.env`:

```env
AUTO_BOOTSTRAP=false
```

---

## 6. Running the App

### Windows

```bat
cd glowbase
py app.py
```

### macOS / Linux

```bash
cd glowbase
python3 app.py
```

Open in browser:

```
http://127.0.0.1:5000/
```

---

## 7. Website Routes

### Public Routes

| Route | Page |
|---|---|
| `/` | Home |
| `/products` | Product listing with search and filter |
| `/product/<product_id>` | Product detail with reviews |
| `/reviews` | All reviews |
| `/submit-review` | Submit a new review |
| `/analytics` | Analytics dashboard |
| `/category/<category_name>` | Products filtered by category |
| `/chemicals` | Chemical ingredient browser |
| `/chemicals/<chemical_name>` | Products containing a specific chemical |

### Admin Routes

| Route | Page |
|---|---|
| `/admin/login` | Admin login |
| `/admin/logout` | Admin logout |
| `/admin/dashboard` | Admin dashboard |
| `/admin/products` | Manage products |
| `/admin/products/add` | Add a product |
| `/admin/products/edit/<product_id>` | Edit a product |
| `/admin/products/delete/<product_id>` | Delete a product |
| `/admin/reviews` | Manage reviews |
| `/admin/reviews/edit/<review_id>` | Edit a review |
| `/admin/reviews/delete/<review_id>` | Delete a review |
| `/admin/sql-demo` | SQL nested query and many-to-many demo |
| `/admin/trigger-demo` | SQL trigger demo |
| `/admin/view-index-demo` | SQL view and index demo |
| `/admin/performance-demo` | Query performance demo |

**Demo admin credentials:**

```
Username: admin
Password: admin123
```

These are hardcoded for project demonstration only. A production version would store admin accounts in MariaDB with hashed passwords.

---

## 8. Database Features

### 8.1 SQL CRUD

| Operation | Where |
|---|---|
| Create | Admin → Add Product |
| Read | Products page, product detail, analytics |
| Update | Admin → Edit Product |
| Delete | Admin → Delete Product |

### 8.2 NoSQL CRUD

| Operation | Where |
|---|---|
| Create | Public → Submit Review |
| Read | Public → Reviews page, product detail |
| Update | Admin → Edit Review |
| Delete | Admin → Delete Review |

Public users handle Create and Read. Admin handles Update and Delete.

### 8.3 Nested Queries

Located at `/admin/sql-demo`. Six nested query examples:

1. Products above average rating
2. Products from brands with more than 3 products
3. Products above average price
4. Brands above overall average rating
5. Products with the highest rating
6. Products from brands with at least one out-of-stock product

### 8.4 Many-to-Many Query

Also located at `/admin/sql-demo`. Demonstrates the `product_categories` junction table with a 4-table JOIN across `products`, `brands`, `product_categories`, and `categories`, using a nested subquery to filter by category size.

### 8.5 Triggers

Located at `/admin/trigger-demo`. Three triggers on the `products` table:

| Trigger | Event | Logs to |
|---|---|---|
| `after_product_insert` | AFTER INSERT | `product_add_logs` |
| `after_product_update` | AFTER UPDATE | `product_audit_logs` |
| `after_product_delete` | AFTER DELETE | `product_audit_logs` |

### 8.6 View

`product_summary_view` — joins `products` and `brands` into a virtual table for cleaner repeated queries.

### 8.7 Indexes

Four indexes on the `products` table covering the most frequently searched and filtered columns:

```sql
idx_products_product_name  ON products(product_name)
idx_products_brand_id      ON products(brand_id)
idx_products_rating        ON products(rating)
idx_products_price         ON products(price_usd)
```

### 8.8 MongoDB Aggregation Pipeline

Used in the analytics dashboard and the chemicals browser. Example pipeline stages used: `$match`, `$unwind`, `$group`, `$sort` — equivalent to a SQL GROUP BY with filtering.

---

## 9. Admin Demo Pages

Before presenting, verify these pages work and have data:

- `/admin/sql-demo` — all 6 nested queries and the many-to-many query return results
- `/admin/trigger-demo` — add a product first so the trigger log is not empty
- `/admin/view-index-demo` — view and indexes should already be applied on startup

---

## 10. Environment Variables

| Variable | Purpose |
|---|---|
| `MARIADB_HOST` | MariaDB host (usually `localhost`) |
| `MARIADB_USER` | MariaDB username |
| `MARIADB_PASSWORD` | MariaDB password |
| `MARIADB_DATABASE` | Database name (`glowbase`) |
| `MONGO_URI` | MongoDB connection string |
| `MONGO_DATABASE` | MongoDB database name (`glowbase`) |
| `MONGO_REVIEWS_COLLECTION` | Collection name (`reviews`) |
| `AUTO_BOOTSTRAP` | Set to `false` to disable auto-setup on startup (default: `true`) |
| `SEED_DATA_DIR` | Override path to the `data/` folder (optional) |

---

## 11. Team Notes

- Start MariaDB before running the app
- Start MongoDB before running the app
- Make sure `.env` values match your local database credentials
- Do not push `.env` or `venv/` to GitHub
- If the trigger demo page is empty, add a product first to fire the insert trigger
- If MongoDB reviews do not appear, check that MongoDB is running and the collection was seeded
- If MariaDB pages fail on startup, check that your MariaDB user has CREATE, ALTER, INDEX, and TRIGGER permissions


fiona test