@echo off
REM Migration script for Website Status Checker
REM This script flattens the nested directory structure and preserves git history

echo Starting migration...
echo.

REM Create backup branch (already done manually)
echo Backup branch created: backup-before-migration
echo.

REM Move directories from nested location to root
echo Moving directories to root level...
git mv Website-Status-Checker\src .\src
git mv Website-Status-Checker\tests .\tests
git mv Website-Status-Checker\docs .\docs
git mv Website-Status-Checker\examples .\examples

REM Move configuration files
echo Moving configuration files...
git mv Website-Status-Checker\pyproject.toml .\pyproject.toml
git mv Website-Status-Checker\setup.py .\setup.py
git mv Website-Status-Checker\requirements.txt .\requirements.txt

REM Move documentation files
echo Moving documentation files...
git mv Website-Status-Checker\CHANGELOG.md .\CHANGELOG.md
git mv Website-Status-Checker\CONTRIBUTING.md .\CONTRIBUTING.md
git mv Website-Status-Checker\QUICKSTART.md .\QUICKSTART.md
git mv Website-Status-Checker\SETUP_INFO_NEEDED.md .\SETUP_INFO_NEEDED.md

REM Remove duplicate README from nested directory
echo Removing duplicate files...
git rm Website-Status-Checker\README.md
git rm Website-Status-Checker\LICENSE

REM Remove empty nested directory
echo Removing empty nested directory...
git rm -r Website-Status-Checker\

echo.
echo Migration complete!
echo Please review changes with: git status
echo Then commit with: git commit -m "Restructure: Move core directories to root level"
