import os
import re
from pathlib import Path
import mysql.connector
from pymongo import MongoClient
from bson import json_util
from dotenv import load_dotenv

load_dotenv()

_BOOTSTRAPPED = False


def _as_bool(value, default=True):
    if value is None:
        return default
    return str(value).strip().lower() not in {"0", "false", "no", "off"}


def _project_data_dir():
    default_data_dir = Path(__file__).resolve().parent / "data"
    configured_dir = os.getenv("SEED_DATA_DIR")
    return Path(configured_dir) if configured_dir else default_data_dir


def _normalize_sql_for_compat(sql_text):
    # MariaDB/MySQL versions may not support every collation from dump files.
    sql_text = re.sub(
        r"COLLATE\s*=\s*utf8mb4_uca1400_ai_ci",
        "COLLATE=utf8mb4_general_ci",
        sql_text,
        flags=re.IGNORECASE,
    )
    sql_text = re.sub(
        r"COLLATE\s+utf8mb4_uca1400_ai_ci",
        "COLLATE utf8mb4_general_ci",
        sql_text,
        flags=re.IGNORECASE,
    )
    sql_text = re.sub(
        r"CHARACTER\s+SET\s+utf8mb4\s+COLLATE\s+utf8mb4_uca1400_ai_ci",
        "CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci",
        sql_text,
        flags=re.IGNORECASE,
    )
    sql_text = re.sub(
        r"\bDROP\s+INDEX\s+IF\s+EXISTS\b",
        "DROP INDEX",
        sql_text,
        flags=re.IGNORECASE,
    )

    create_match = re.search(
        r"CREATE\s+TABLE\s+`?([A-Za-z0-9_]+)`?",
        sql_text,
        flags=re.IGNORECASE,
    )
    if create_match:
        table_name = create_match.group(1)
        fk_counter = 0

        def _rename_fk(match):
            nonlocal fk_counter
            fk_counter += 1
            return f"CONSTRAINT `{table_name}_fk_{fk_counter}` FOREIGN KEY"

        sql_text = re.sub(
            r"CONSTRAINT\s+`[^`]+`\s+FOREIGN\s+KEY",
            _rename_fk,
            sql_text,
            flags=re.IGNORECASE,
        )

    return sql_text


def _execute_sql_statement(cursor, statement):
    try:
        cursor.execute(statement)
    except mysql.connector.Error as err:
        normalized_statement = statement.strip().upper()
        is_drop_index = normalized_statement.startswith("DROP INDEX ")

        # Ignore missing-index errors for idempotent startup imports.
        if is_drop_index and err.errno in {1091}:
            return
        raise


def _drain_sql_results(cursor):
    if not cursor.with_rows:
        return

    cursor.fetchall()
    while cursor.nextset():
        if cursor.with_rows:
            cursor.fetchall()


def _run_sql_file(cursor, sql_path, database_name):
    delimiter = ";"
    statement_lines = []

    with open(sql_path, "r", encoding="utf-8") as sql_file:
        for line in sql_file:
            stripped = line.strip()

            if stripped.startswith("--"):
                continue

            if stripped.upper().startswith("DELIMITER "):
                delimiter = stripped.split(maxsplit=1)[1]
                continue

            statement_lines.append(line)

            current_statement = "".join(statement_lines).rstrip()
            if not current_statement.endswith(delimiter):
                continue

            current_statement = current_statement[: -len(delimiter)].strip()
            statement_lines = []

            if not current_statement:
                continue

            if current_statement.upper().startswith("USE "):
                current_statement = f"USE `{database_name}`"

            current_statement = _normalize_sql_for_compat(current_statement)

            _execute_sql_statement(cursor, current_statement)
            _drain_sql_results(cursor)

    remaining = "".join(statement_lines).strip()
    if remaining:
        remaining = _normalize_sql_for_compat(remaining)
        _execute_sql_statement(cursor, remaining)
        _drain_sql_results(cursor)


def _bootstrap_mariadb():
    host = os.getenv("MARIADB_HOST")
    user = os.getenv("MARIADB_USER")
    password = os.getenv("MARIADB_PASSWORD")
    database_name = os.getenv("MARIADB_DATABASE")

    if not all([host, user, password, database_name]):
        raise ValueError("Missing one or more MariaDB environment variables")

    admin_conn = mysql.connector.connect(
        host=host,
        user=user,
        password=password
    )
    admin_cursor = admin_conn.cursor()
    admin_cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database_name}`")
    admin_conn.commit()
    admin_cursor.close()
    admin_conn.close()

    conn = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database_name
    )
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema = %s
        AND table_name = 'products'
        """,
        (database_name,)
    )
    has_products_table = cursor.fetchone()[0] > 0

    data_dir = _project_data_dir()
    main_sql_file = data_dir / "glowbasev1.sql"
    views_indexes_sql_file = data_dir / "sql_features_views_indexes.sql"
    triggers_sql_file = data_dir / "sql_features_triggers.sql"
    product_categories_sql_file = data_dir / "populate_product_categories.sql"

    if product_categories_sql_file.exists():
        print(f"Running product categories population: {product_categories_sql_file}")
        _run_sql_file(cursor, product_categories_sql_file, database_name)
        
    if not has_products_table:
        if not main_sql_file.exists():
            raise FileNotFoundError(f"Missing SQL file: {main_sql_file}")
        _run_sql_file(cursor, main_sql_file, database_name)

    if views_indexes_sql_file.exists():
        _run_sql_file(cursor, views_indexes_sql_file, database_name)

    if triggers_sql_file.exists():
        _run_sql_file(cursor, triggers_sql_file, database_name)

    conn.commit()
    cursor.close()
    conn.close()


def _bootstrap_mongodb():
    mongo_uri = os.getenv("MONGO_URI")
    mongo_database = os.getenv("MONGO_DATABASE")
    reviews_collection_name = os.getenv("MONGO_REVIEWS_COLLECTION")

    if not all([mongo_uri, mongo_database, reviews_collection_name]):
        raise ValueError("Missing one or more MongoDB environment variables")

    client = MongoClient(mongo_uri)
    reviews_collection = client[mongo_database][reviews_collection_name]

    if reviews_collection.count_documents({}, limit=1) == 0:
        reviews_file = _project_data_dir() / "glowbase.reviews.json"
        if reviews_file.exists():
            with open(reviews_file, "r", encoding="utf-8") as file:
                payload = json_util.loads(file.read())

            if isinstance(payload, list) and payload:
                reviews_collection.insert_many(payload, ordered=False)
            elif isinstance(payload, dict):
                reviews_collection.insert_one(payload)

    client.close()


def bootstrap_databases():
    global _BOOTSTRAPPED

    if _BOOTSTRAPPED:
        return

    if not _as_bool(os.getenv("AUTO_BOOTSTRAP", "true")):
        return

    _bootstrap_mariadb()
    _bootstrap_mongodb()
    _BOOTSTRAPPED = True


def get_mariadb_connection():
    return mysql.connector.connect(
        host=os.getenv("MARIADB_HOST"),
        user=os.getenv("MARIADB_USER"),
        password=os.getenv("MARIADB_PASSWORD"),
        database=os.getenv("MARIADB_DATABASE")
    )


def get_mongo_collection():
    client = MongoClient(os.getenv("MONGO_URI"))
    db = client[os.getenv("MONGO_DATABASE")]
    return db[os.getenv("MONGO_REVIEWS_COLLECTION")]