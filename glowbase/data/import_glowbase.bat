@echo off
cd /d C:\Users\USER\Documents\GitHub\INF2003-Database-Project\glowbase\data

echo ==============================
echo GlowBase MariaDB Import Script
echo ==============================

set DB_NAME=glowbase
set SQL_FILE=glowbasev1.sql
set MARIADB_EXE=C:\Program Files\MariaDB 12.2\bin\mariadb.exe

echo.
echo [1] Checking SQL file...

if not exist "%SQL_FILE%" (
    echo ERROR: Cannot find %SQL_FILE%
    echo Make sure this file is inside:
    echo C:\Users\USER\Documents\GitHub\INF2003-Database-Project\glowbase\data
    pause
    exit /b
)

echo SQL file found.

echo.
echo [2] Checking MariaDB...

if not exist "%MARIADB_EXE%" (
    echo ERROR: Cannot find MariaDB executable.
    echo Expected path:
    echo %MARIADB_EXE%
    pause
    exit /b
)

echo MariaDB found.

echo.
echo [3] Creating database if not exists...

"%MARIADB_EXE%" -u root -p -e "CREATE DATABASE IF NOT EXISTS %DB_NAME%;"

if errorlevel 1 (
    echo ERROR: Failed to create database.
    pause
    exit /b
)

echo.
echo [4] Importing SQL file into MariaDB...

"%MARIADB_EXE%" -u root -p %DB_NAME% < "%SQL_FILE%"

if errorlevel 1 (
    echo ERROR: Failed to import SQL file.
    pause
    exit /b
)

echo.
echo [5] Checking imported tables...

"%MARIADB_EXE%" -u root -p %DB_NAME% -e "SHOW TABLES;"

echo.
echo ==============================
echo MariaDB import finished.
echo ==============================
pause