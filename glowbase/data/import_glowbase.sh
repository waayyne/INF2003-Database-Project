#!/bin/bash

cd "/c/Users/USER/Documents/GitHub/INF2003-Database-Project/glowbase/data" || exit

echo "=============================="
echo "GlowBase MariaDB Import Script"
echo "=============================="

DB_NAME="glowbase"
SQL_FILE="glowbasev1.sql"
MARIADB_EXE="/c/Program Files/MariaDB 12.2/bin/mariadb.exe"

echo ""
echo "[1] Checking SQL file..."

if [ ! -f "$SQL_FILE" ]; then
    echo "ERROR: Cannot find $SQL_FILE"
    echo "Make sure this file is inside:"
    echo "C:/Users/USER/Documents/GitHub/INF2003-Database-Project/glowbase/data"
    read -p "Press Enter to exit..."
    exit 1
fi

echo "SQL file found."

echo ""
echo "[2] Checking MariaDB..."

if [ ! -f "$MARIADB_EXE" ]; then
    echo "ERROR: Cannot find MariaDB executable."
    echo "Expected path:"
    echo "$MARIADB_EXE"
    read -p "Press Enter to exit..."
    exit 1
fi

echo "MariaDB found."

echo ""
echo "[3] Creating database if not exists..."

"$MARIADB_EXE" -u root -p -e "CREATE DATABASE IF NOT EXISTS $DB_NAME;"

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to create database."
    read -p "Press Enter to exit..."
    exit 1
fi

echo ""
echo "[4] Importing SQL file into MariaDB..."

"$MARIADB_EXE" -u root -p "$DB_NAME" < "$SQL_FILE"

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to import SQL file."
    read -p "Press Enter to exit..."
    exit 1
fi

echo ""
echo "[5] Checking imported tables..."

"$MARIADB_EXE" -u root -p "$DB_NAME" -e "SHOW TABLES;"

echo ""
echo "=============================="
echo "MariaDB import finished."
echo "=============================="

read -p "Press Enter to exit..."