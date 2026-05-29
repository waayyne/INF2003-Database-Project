# GlowBase

GlowBase is a Beauty Product Analytics and Review System for the INF2003 Database Systems group project.

The system uses:

* Flask for the web application
* HTML, CSS, and JavaScript for the frontend
* MariaDB for structured product data
* MongoDB for flexible review data

At the current stage, the website uses CSV files and pandas for frontend testing first. Later, the CSV and pandas parts will be replaced with MariaDB and MongoDB queries.

---

## 1. Project Overview

GlowBase allows users to:

* View beauty products
* Search and filter products
* View product details
* View product reviews
* Submit product reviews without logging in
* View analytics dashboard

Admin users can:

* Login to admin dashboard
* View product records
* Add products
* Delete products

The final version should demonstrate:

* Relational database design using MariaDB
* NoSQL database design using MongoDB
* SQL CRUD
* NoSQL CRUD
* Nested queries
* Views
* Triggers
* Indexes
* Aggregation
* Web application integration

---

## 2. Current Development Stage

Current version:

```
Flask + pandas + CSV files
```

Current flow:

```
CSV files
    ↓
pandas reads CSV files
    ↓
Flask sends data to HTML templates
    ↓
Website displays products, reviews, admin pages, and analytics
```

Current CSV files:

```
data/product_info_matched_clean.csv
data/productreviews_clean.csv
data/user_reviews.csv
```

Important:

```
data/user_reviews.csv is created when users submit reviews through the form.
```

This current version is only for frontend testing before the real databases are connected.

---

## 3. Final System Plan

Final version:

```
Flask + MariaDB + MongoDB
```

Final flow:

```
product_info_matched_clean.csv
    ↓
Import into MariaDB
    ↓
Flask reads product data from MariaDB

productreviews_clean.csv
    ↓
Import into MongoDB
    ↓
Flask reads review data from MongoDB
```

Final database split:

```
Product data → MariaDB
Review data → MongoDB
```

---

## 4. Project Features

### Public User Features

* Home page
* Product listing page
* Product search
* Product filters
* Product detail page
* Reviews page
* Submit review page
* Analytics dashboard

### Admin Features

* Admin login
* Admin dashboard
* View products
* Add product
* Delete product

Current temporary admin login:

```
Username: admin
Password: admin123
```

This is only for testing. In the final version, admin login should use a MariaDB admins table with password hashing.

---

## 5. Website Routes

Current Flask routes:

```
/
/products
/product/<product_id>
/reviews
/submit-review
/analytics
/admin/login
/admin/logout
/admin/dashboard
/admin/products
/admin/products/add
/admin/products/delete/<product_id>
```

---

## 6. Current Folder Structure

```
glowbase/
│   app.py
│   requirements.txt
│   .gitignore
│   README.md
│
├── data/
│   ├── product_info_matched_clean.csv
│   ├── productreviews_clean.csv
│   └── user_reviews.csv
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
    └── admin_add_product.html
```

---

## 7. Setup Instructions

### 7.1 Windows Setup

Use Command Prompt.

Create project folder:

```
mkdir glowbase
cd glowbase
```

Create folders:

```
mkdir templates static static\css static\js data
```

Create files:

```
type nul > app.py
type nul > requirements.txt
type nul > .gitignore
type nul > README.md
type nul > templates\base.html
type nul > templates\index.html
type nul > templates\products.html
type nul > templates\product_detail.html
type nul > templates\reviews.html
type nul > templates\analytics.html
type nul > templates\submit_review.html
type nul > templates\admin_login.html
type nul > templates\admin_dashboard.html
type nul > templates\admin_products.html
type nul > templates\admin_add_product.html
type nul > static\css\style.css
type nul > static\js\app.js
```

Create virtual environment:

```
python -m venv venv
```

Activate virtual environment:

```
venv\Scripts\activate
```

Install dependencies:

```
pip install -r requirements.txt
```

Run application:

```
python app.py
```

Open in browser:

```
http://127.0.0.1:5000
```

---

### 7.2 macOS Setup

Use Terminal.

Create project folder:

```
mkdir glowbase
cd glowbase
```

Create folders:

```
mkdir -p templates static/css static/js data
```

Create files:

```
touch app.py
touch requirements.txt
touch .gitignore
touch README.md
touch templates/base.html
touch templates/index.html
touch templates/products.html
touch templates/product_detail.html
touch templates/reviews.html
touch templates/analytics.html
touch templates/submit_review.html
touch templates/admin_login.html
touch templates/admin_dashboard.html
touch templates/admin_products.html
touch templates/admin_add_product.html
touch static/css/style.css
touch static/js/app.js
```

Create virtual environment:

```
python3 -m venv venv
```

Activate virtual environment:

```
source venv/bin/activate
```

Install dependencies:

```
pip install -r requirements.txt
```

Run application:

```
python app.py
```

If that does not work, run:

```
python3 app.py
```

Open in browser:

```
http://127.0.0.1:5000
```

---

## 8. Windows vs macOS Command Differences

| Purpose              | Windows CMD           | macOS Terminal                  |
| -------------------- | --------------------- | ------------------------------- |
| Create file          | type nul > file.txt   | touch file.txt                  |
| Create nested folder | mkdir static\css      | mkdir -p static/css             |
| Activate venv        | venv\Scripts\activate | source venv/bin/activate        |
| Run Python           | python app.py         | python app.py or python3 app.py |
| Path separator       | \                     | /                               |

---

## 9. requirements.txt

Current requirements.txt:

```
flask
pandas
```

Purpose:

```
flask
    Used to run the web application.

pandas
    Temporarily used to read CSV files during frontend testing.
```

Later, when MariaDB and MongoDB are connected, requirements.txt may become:

```
flask
pandas
mysql-connector-python
pymongo
python-dotenv
werkzeug
```

Purpose of future packages:

```
mysql-connector-python
    Used to connect Flask to MariaDB.

pymongo
    Used to connect Flask to MongoDB.

python-dotenv
    Used to load database credentials from a .env file.

werkzeug
    Used for admin password hashing.
```

Pandas may be removed from the final website runtime if it is no longer needed. However, pandas may still be useful for import scripts.

---

## 10. .gitignore

Current .gitignore:

```
__pycache__/
*.pyc
*.pyo
*.pyd

venv/

.env

instance/

.vscode/

.DS_Store
Thumbs.db

data/*.csv

*.db
*.sqlite3
```

Important:

```
CSV files are ignored because dataset files can be large.
.env is ignored because it will contain database credentials.
venv is ignored because each team member should create their own virtual environment.
```

---

## 11. Dataset Files

Place the cleaned dataset files inside the data folder:

```
data/product_info_matched_clean.csv
data/productreviews_clean.csv
```

The review form may create:

```
data/user_reviews.csv
```

Do not push CSV files to GitHub.

Each team member should place their own CSV files inside the data folder after cloning the project.

---

## 12. CSV Encoding Note

The cleaned CSV files may not be UTF-8 encoded.

If pandas gives a UnicodeDecodeError, use latin1 encoding.

Current CSV reading code:

```
products_df = pd.read_csv("data/product_info_matched_clean.csv", encoding="latin1")
reviews_df = pd.read_csv("data/productreviews_clean.csv", encoding="latin1")
```

If latin1 does not work, try cp1252:

```
products_df = pd.read_csv("data/product_info_matched_clean.csv", encoding="cp1252")
reviews_df = pd.read_csv("data/productreviews_clean.csv", encoding="cp1252")
```

---

## 13. How To Run The Application

Make sure you are inside the glowbase folder.

### Windows

Activate virtual environment:

```
venv\Scripts\activate
```

Run Flask:

```
python app.py
```

Open in browser:

```
http://127.0.0.1:5000
```

---

### macOS

Activate virtual environment:

```
source venv/bin/activate
```

Run Flask:

```
python app.py
```

If needed:

```
python3 app.py
```

Open in browser:

```
http://127.0.0.1:5000
```

---

### Useful Pages

```
http://127.0.0.1:5000/
http://127.0.0.1:5000/products
http://127.0.0.1:5000/reviews
http://127.0.0.1:5000/submit-review
http://127.0.0.1:5000/analytics
http://127.0.0.1:5000/admin/login
```

Temporary admin login:

```
Username: admin
Password: admin123
```

---

## 14. Current Temporary Backend

The current backend uses pandas.

Examples of current pandas-based logic:

```
Product listing reads from product_info_matched_clean.csv.
Review listing reads from productreviews_clean.csv.
User-submitted reviews are saved into user_reviews.csv.
Admin add product saves into product_info_matched_clean.csv.
Admin delete product removes from product_info_matched_clean.csv.
Analytics are calculated using pandas.
```

This is only temporary.

The final project should not depend on CSV files for the main application.

---

## 15. What To Do After MariaDB and MongoDB Are Ready

After the real databases are created, the current CSV-based backend will be replaced with database queries.

---

### 15.1 Install Database Packages

Update requirements.txt to include:

```
flask
pandas
mysql-connector-python
pymongo
python-dotenv
werkzeug
```

Then run:

Windows/macOS:

```
pip install -r requirements.txt
```

Document this command in this README after running it.

---

### 15.2 Create .env File

Create a .env file.

Windows:

```
type nul > .env
```

macOS:

```
touch .env
```

Example .env content:

```
FLASK_SECRET_KEY=change-this-secret-key

MARIADB_HOST=localhost
MARIADB_USER=root
MARIADB_PASSWORD=your_password
MARIADB_DATABASE=glowbase

MONGODB_URI=mongodb://localhost:27017/
MONGODB_DATABASE=glowbase
```

Important:

```
Do not push .env to GitHub.
.env is already included in .gitignore.
```

---

### 15.3 Add db.py

Create db.py.

Windows:

```
type nul > db.py
```

macOS:

```
touch db.py
```

Purpose of db.py:

```
Store MariaDB connection code.
Store MongoDB connection code.
Keep database connection logic separate from app.py.
```

Expected future use:

```
app.py imports database connection functions from db.py.
```

---

### 15.4 Add queries.py

Create queries.py.

Windows:

```
type nul > queries.py
```

macOS:

```
touch queries.py
```

Purpose of queries.py:

```
Store reusable SQL statements for MariaDB.
Keep SQL statements separate from app.py.
Make the code easier to maintain.
```

Expected future use:

```
app.py imports SQL statements from queries.py.
```

---

### 15.5 Replace Product CSV Code With MariaDB

Current product data source:

```
products_df = pd.read_csv("data/product_info_matched_clean.csv", encoding="latin1")
```

Final product data source:

```
MariaDB products, brands, categories, ingredients, and highlights tables.
```

Routes that should change from pandas to MariaDB:

```
/products
/product/<product_id>
/analytics
/admin/products
/admin/products/add
/admin/products/delete/<product_id>
```

Expected final behaviour:

```
Product listing uses SQL SELECT.
Product detail uses SQL SELECT with joins.
Admin add product uses SQL INSERT.
Admin delete product uses SQL DELETE.
Admin edit product, if added, uses SQL UPDATE.
Analytics uses SQL aggregation, views, nested queries, and indexes.
```

After this is done, product pages should no longer depend on products_df.

---

### 15.6 Replace Review CSV Code With MongoDB

Current review data source:

```
reviews_df = pd.read_csv("data/productreviews_clean.csv", encoding="latin1")
user_reviews.csv
```

Final review data source:

```
MongoDB reviews collection.
```

Routes that should change from pandas to MongoDB:

```
/reviews
/submit-review
/product/<product_id>
/analytics
```

Expected final behaviour:

```
Reviews page uses MongoDB find.
Product detail related reviews use MongoDB find by product_id.
Submit review uses MongoDB insert.
Review analytics uses MongoDB aggregation.
```

After this is done, review pages should no longer depend on reviews_df or user_reviews.csv.

---

### 15.7 Remove pandas From app.py

When MariaDB and MongoDB are fully connected:

Remove this kind of code from app.py:

```
import pandas as pd
```

Remove CSV loading code:

```
products_df = pd.read_csv(...)
reviews_df = pd.read_csv(...)
```

Remove helper functions that save to CSV:

```
load_user_reviews()
save_user_review()
```

Replace them with database functions from db.py.

Expected final app.py:

```
Flask routes only.
MariaDB queries are called through db.py and queries.py.
MongoDB queries are called through db.py.
No direct CSV reading for the main website.
```

---

### 15.8 Decide Whether To Keep pandas

Pandas can be removed from the main website if it is no longer used.

Remove pandas from requirements.txt only if:

```
app.py does not import pandas.
db.py does not import pandas.
No website route uses pandas.
```

Pandas can still be kept if import scripts use it.

Recommended final approach:

```
Website runtime:
    flask
    mysql-connector-python
    pymongo
    python-dotenv
    werkzeug

Data import scripts:
    pandas can still be used
```

So pandas may stay in requirements.txt if the team wants one shared requirements file for both website and import scripts.

---

## 16. What To Add After Database Integration

### MariaDB Product Features

Product data should support:

```
Product listing
Product details
Search
Filtering
Admin add product
Admin delete product
Admin edit product
Analytics dashboard
```

This helps demonstrate SQL CRUD:

```
Create → Admin add product
Read → Product listing and product detail
Update → Admin edit product
Delete → Admin delete product
```

---

### MongoDB Review Features

Review data should support:

```
Reviews page
Product-related reviews
Submit review form
Review analytics
```

This helps demonstrate NoSQL CRUD:

```
Create → User submits review
Read → Reviews page and product detail page
Update → Optional admin edit review
Delete → Optional admin delete review
```

---

### Admin Login

Current version:

```
Hardcoded username and password.
```

Final version:

```
Admin accounts should be stored in MariaDB.
Passwords should be hashed.
Flask session should be used after successful login.
```

Recommended future table:

```
admins
```

---

### Admin Edit Product

Recommended future route:

```
/admin/products/edit/<product_id>
```

Recommended future template:

```
templates/admin_edit_product.html
```

Windows command to create it:

```
type nul > templates\admin_edit_product.html
```

macOS command to create it:

```
touch templates/admin_edit_product.html
```

Purpose:

```
Demonstrates SQL UPDATE.
```

---

### Analytics Page

The Analytics page should show advanced database features.

Possible analytics sections:

```
Top rated products
Most loved products
Best performing brands
Out-of-stock products
Products above category average
Category-level performance
Review recommendation summary
Review rating by brand
Review count by skin type
```

Advanced database features can be shown here:

```
Nested query results
SQL view results
SQL trigger/audit results
SQL index-supported filtering
MongoDB aggregation results
```

---

## 17. Required Project Components Checklist

Final project should include:

```
Flask web application
MariaDB database
MongoDB database
Real-world dataset
ER diagram
At least 3 relational tables
Different relationship types
SQL CRUD operations
NoSQL CRUD operations
Nested SQL query
SQL trigger
SQL view
SQL indexes
MongoDB aggregation
Product listing page
Product detail page
Reviews page
Submit review form
Admin login
Admin add product
Admin delete product
Analytics dashboard
README setup instructions
GenAI reflection
```

---

## 18. Cross-Platform Notes

* The project should work on both Windows and macOS.

* Do not hardcode Windows-only paths in Python code.

* Use relative paths such as:

  data/product_info_matched_clean.csv

* Avoid full local paths such as:

  C:\Users\USER\Documents...

* The Flask app should be run from inside the glowbase folder.

* Each team member should create their own virtual environment.

* Each team member should run pip install -r requirements.txt.

* The venv folder should not be pushed to GitHub.

* Dataset CSV files should not be pushed to GitHub.

* Team members must place their own CSV files inside the data folder.

---

## 19. Notes For Team Members

* Do not push CSV dataset files to GitHub.
* Do not push .env to GitHub.
* Each team member should create their own virtual environment.
* Each team member should run pip install -r requirements.txt.
* The current app uses pandas and CSV only for frontend testing.
* The final app should use MariaDB and MongoDB.
* SQL statements should be written in code, not typed manually by website users.
* HTML pages only display data.
* Flask routes run the backend logic.
* MariaDB handles product data.
* MongoDB handles review data.
* Admin product management should become SQL CRUD.
* Submit review should become MongoDB Create.
* Analytics should show advanced database features.
* Database implementation is more important than website design for this project.

---

## 20. Development Log

### Windows Commands Used So Far

```
mkdir glowbase
cd glowbase
mkdir templates static static\css static\js data

type nul > app.py
type nul > requirements.txt
type nul > .gitignore
type nul > README.md
type nul > templates\base.html
type nul > templates\index.html
type nul > templates\products.html
type nul > templates\product_detail.html
type nul > templates\reviews.html
type nul > templates\analytics.html
type nul > static\css\style.css
type nul > static\js\app.js

type nul > templates\submit_review.html
type nul > templates\admin_login.html
type nul > templates\admin_dashboard.html
type nul > templates\admin_products.html
type nul > templates\admin_add_product.html

python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

---

### macOS Equivalent Commands

```
mkdir glowbase
cd glowbase
mkdir -p templates static/css static/js data

touch app.py
touch requirements.txt
touch .gitignore
touch README.md
touch templates/base.html
touch templates/index.html
touch templates/products.html
touch templates/product_detail.html
touch templates/reviews.html
touch templates/analytics.html
touch templates/submit_review.html
touch templates/admin_login.html
touch templates/admin_dashboard.html
touch templates/admin_products.html
touch templates/admin_add_product.html
touch static/css/style.css
touch static/js/app.js

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

If needed:

```
python3 app.py
```

---

### Future Windows Commands After Database Integration

```
pip install -r requirements.txt
type nul > .env
type nul > db.py
type nul > queries.py
type nul > import_mariadb.py
type nul > import_mongodb.py
type nul > templates\admin_edit_product.html
```

---

### Future macOS Commands After Database Integration

```
pip install -r requirements.txt
touch .env
touch db.py
touch queries.py
touch import_mariadb.py
touch import_mongodb.py
touch templates/admin_edit_product.html
```

---

## 21. Current Temporary Reminder

This project currently looks like a complete website, but it is still only a prototype because it reads from CSV files using pandas.

Final submission should connect the same website to:

```
MariaDB for product data
MongoDB for review data
```

The main files to update later are:

```
app.py
requirements.txt
```

The main files to add later are:

```
.env
db.py
queries.py
import_mariadb.py
import_mongodb.py
```

The HTML and CSS files can mostly stay the same.
