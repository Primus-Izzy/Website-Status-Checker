@echo off
REM Health Check Script for Website Status Checker (Windows)
REM Usage: scripts\health_check.bat [url]

setlocal enabledelayedexpansion

set "URL=%~1"
if "%URL%"=="" set "URL=http://localhost:8000"

echo.
echo 🏥 Health Check for Website Status Checker
echo 🔗 URL: %URL%
echo.

REM Basic health check
echo 1️⃣  Basic Health Check...
curl -s "%URL%/health" > temp_health.txt 2>&1
findstr /C:"healthy" temp_health.txt >nul 2>&1
if %errorlevel%==0 (
    echo ✅ Basic health: OK
) else (
    echo ❌ Basic health: FAILED
    del temp_health.txt
    exit /b 1
)
del temp_health.txt

REM Detailed health check
echo.
echo 2️⃣  Detailed Health Check...
curl -s "%URL%/health/detailed" > temp_detailed.txt 2>&1
findstr /C:"status" temp_detailed.txt >nul 2>&1
if %errorlevel%==0 (
    echo ✅ Detailed health: OK
    echo.
    echo 📊 Health Details:
    type temp_detailed.txt
) else (
    echo ❌ Detailed health: FAILED
)
del temp_detailed.txt

REM Liveness probe
echo.
echo 3️⃣  Liveness Probe...
for /f %%i in ('curl -s -o nul -w "%%{http_code}" "%URL%/health/live"') do set LIVE=%%i
if "%LIVE%"=="200" (
    echo ✅ Liveness: OK (HTTP %LIVE%)
) else (
    echo ❌ Liveness: FAILED (HTTP %LIVE%)
)

REM Readiness probe
echo.
echo 4️⃣  Readiness Probe...
for /f %%i in ('curl -s -o nul -w "%%{http_code}" "%URL%/health/ready"') do set READY=%%i
if "%READY%"=="200" (
    echo ✅ Readiness: OK (HTTP %READY%)
) else (
    echo ❌ Readiness: FAILED (HTTP %READY%)
)

REM Metrics endpoint
echo.
echo 5️⃣  Metrics Endpoint...
for /f %%i in ('curl -s -o nul -w "%%{http_code}" "%URL%/metrics"') do set METRICS=%%i
if "%METRICS%"=="200" (
    echo ✅ Metrics: OK (HTTP %METRICS%)
) else (
    echo ⚠️  Metrics: Not available (HTTP %METRICS%)
)

echo.
echo 🎉 Health check completed!

endlocal
