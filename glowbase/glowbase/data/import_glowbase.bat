@echo off
cd /d C:\Users\USER\Documents\GitHub\INF2003-Database-Project\glowbase\data

echo ==============================
echo GlowBase MariaDB Import Script
echo ==============================

set DB_NAME=glowbase
set MARIADB_EXE=C:\Program Files\MariaDB 12.3\bin\mariadb.exe

echo.
echo [1] Checking MariaDB...

if not exist "%MARIADB_EXE%" (
    echo ERROR: Cannot find MariaDB executable.
    echo Expected path:
    echo %MARIADB_EXE%
    pause
    exit /b
)

echo MariaDB found.

echo.
echo [2] Creating database if not exists...

"%MARIADB_EXE%" -u root -p -e "CREATE DATABASE IF NOT EXISTS %DB_NAME%;"

if errorlevel 1 (
    echo ERROR: Failed to create database.
    pause
    exit /b
)

echo.
echo [3] Importing main database file...

if not exist "glowbasev1.sql" (
    echo ERROR: Cannot find glowbasev1.sql
    pause
    exit /b
)

"%MARIADB_EXE%" -u root -p %DB_NAME% < "glowbasev1.sql"

if errorlevel 1 (
    echo ERROR: Failed to import glowbasev1.sql
    pause
    exit /b
)

echo.
echo [4] Importing views and indexes...

if exist "sql_features_views_indexes.sql" (
    "%MARIADB_EXE%" -u root -p %DB_NAME% < "sql_features_views_indexes.sql"

    if errorlevel 1 (
        echo ERROR: Failed to import sql_features_views_indexes.sql
        pause
        exit /b
    )
) else (
    echo WARNING: sql_features_views_indexes.sql not found. Skipping.
)

echo.
echo [5] Importing triggers...

if exist "sql_features_triggers.sql" (
    "%MARIADB_EXE%" -u root -p %DB_NAME% < "sql_features_triggers.sql"

    if errorlevel 1 (
        echo ERROR: Failed to import sql_features_triggers.sql
        pause
        exit /b
    )
) else (
    echo WARNING: sql_features_triggers.sql not found. Skipping.
)

echo.
echo [6] Checking imported tables...

"%MARIADB_EXE%" -u root -p %DB_NAME% -e "SHOW TABLES;"

echo.
echo [7] Checking views...

"%MARIADB_EXE%" -u root -p %DB_NAME% -e "SHOW FULL TABLES WHERE Table_type = 'VIEW';"

echo.
echo [8] Checking triggers...

"%MARIADB_EXE%" -u root -p %DB_NAME% -e "SHOW TRIGGERS;"

echo.
echo [9] Checking indexes...

"%MARIADB_EXE%" -u root -p %DB_NAME% -e "SHOW INDEX FROM products;"

echo.
echo ==============================
echo MariaDB import finished.
echo ==============================
pause