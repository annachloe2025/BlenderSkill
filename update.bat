@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ==============================================
REM  BlenderSkill - update and publish
REM  Double-click this file.
REM ==============================================

cd /d C:\Users\hoeho\Documents\Claude\BlenderSkill

echo.
echo ==============================================
echo   BlenderSkill - update and publish
echo ==============================================
echo.

REM --- setup: install MkDocs + Material if needed ---
echo [setup] Checking MkDocs + Material ...
pip install --quiet --upgrade mkdocs mkdocs-material pymdown-extensions
if errorlevel 1 (
    echo.
    echo   ERROR: pip install failed.
    echo   Make sure Python and pip are installed.
    echo.
    pause
    exit /b 1
)

REM --- commit message input (default on Enter) ---
set "MSG="
set /p MSG=Commit message (press Enter for default):
if "!MSG!"=="" set "MSG=Update docs"

echo.
echo [1/4] Staging changes ...
git add .

echo.
echo [2/4] Committing ...
git commit -m "!MSG!"
if errorlevel 1 echo   (nothing to commit, or commit skipped)

echo.
echo [3/4] Pushing to GitHub ...
git push
if errorlevel 1 (
    echo.
    echo   ERROR: git push failed.
    echo.
    pause
    exit /b 1
)

echo.
echo [4/4] Deploying site to GitHub Pages ...
python -m mkdocs gh-deploy --force
if errorlevel 1 (
    echo.
    echo   ERROR: mkdocs gh-deploy failed.
    echo.
    pause
    exit /b 1
)

echo.
echo ==============================================
echo   Done!
echo   Site: https://annachloe2025.github.io/BlenderSkill/
echo   (reflection takes 1-2 minutes)
echo ==============================================
echo.
pause
