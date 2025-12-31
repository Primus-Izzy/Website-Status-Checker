@echo off
REM Database Backup Script for Website Status Checker (Windows)
REM Usage: scripts\backup.bat [backup_directory]

setlocal enabledelayedexpansion

set "BACKUP_DIR=%~1"
if "%BACKUP_DIR%"=="" set "BACKUP_DIR=.\backups"

REM Get timestamp
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set DATE=%%c%%a%%b)
for /f "tokens=1-2 delims=: " %%a in ('time /t') do (set TIME=%%a%%b)
set "TIMESTAMP=%DATE%_%TIME::=%"
set "BACKUP_FILE=%BACKUP_DIR%\website_checker_%TIMESTAMP%.sql"

REM Create backup directory
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

echo.
echo 🔄 Starting database backup...
echo 📁 Backup location: %BACKUP_FILE%

REM Check if Docker Compose is available
docker-compose ps db >nul 2>&1
if %errorlevel%==0 (
    echo 🐳 Using Docker Compose...
    docker-compose exec -T db pg_dump -U checker website_checker > "%BACKUP_FILE%"
) else (
    echo 💻 Using local PostgreSQL...
    pg_dump -h localhost -U checker website_checker > "%BACKUP_FILE%"
)

if %errorlevel%==0 (
    echo ✅ Backup completed successfully!
    echo 📦 File: %BACKUP_FILE%
    dir "%BACKUP_FILE%" | findstr /C:".sql"
) else (
    echo ❌ Backup failed!
    exit /b 1
)

echo.
echo 🧹 Note: Manual cleanup of old backups recommended

endlocal
