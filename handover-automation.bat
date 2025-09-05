@echo off
REM Repository Handover Automation Script for Windows
REM Implements the SOP for secure repository mirroring and handover

setlocal EnableDelayedExpansion

REM Configuration
set "DATE=%date:~-4,4%%date:~-10,2%%date:~-7,2%"
set "HANDOVER_TAG=handover-%date:~-4,4%-%date:~-10,2%-%date:~-7,2%"

echo [INFO] Starting repository handover process...
echo [INFO] Working directory: %CD%
echo [INFO] Process started: %date% %time%

REM Check dependencies
echo [INFO] Checking dependencies...
git --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Git is required but not installed
    exit /b 1
)

REM Check for secret scanners
where gitleaks >nul 2>&1
if !errorlevel! equ 0 (
    echo [SUCCESS] gitleaks found - will use for secret scanning
    set "SCANNER=gitleaks"
) else (
    where trufflehog >nul 2>&1
    if !errorlevel! equ 0 (
        echo [SUCCESS] truffleHog found - will use for secret scanning
        set "SCANNER=trufflehog"
    ) else (
        echo [WARNING] No secret scanner found. Manual scanning required.
        set "SCANNER=manual"
    )
)

REM Step 0: Forensic backup
echo [INFO] Step 0: Creating forensic backup...
if not exist "forensic-backup" mkdir "forensic-backup"

echo [INFO] Creating bare clone...
git clone --bare . "forensic-backup\forensic-backup-%DATE%.git"

echo [INFO] Creating git bundle...
cd "forensic-backup\forensic-backup-%DATE%.git"
git bundle create "..\forensic-backup-%DATE%.bundle" --all
cd ..\..

echo [INFO] Generating SHA-256 hash...
certutil -hashfile "forensic-backup\forensic-backup-%DATE%.bundle" SHA256 > "forensic-backup\forensic-backup-%DATE%.sha256"

echo [SUCCESS] Forensic backup created: forensic-backup\forensic-backup-%DATE%.bundle

REM Step 1: Secret scan
echo [INFO] Step 1: Performing secret scan...
set "SCAN_REPORT=secret-scan-%DATE%.txt"

if "%SCANNER%" == "gitleaks" (
    echo [INFO] Running gitleaks scan...
    gitleaks detect --source . --verbose --report-path "%SCAN_REPORT%" 2>&1
    if !errorlevel! equ 0 (
        echo [INFO] No secrets detected by gitleaks
        set "CLEANUP_NEEDED=false"
    ) else (
        echo [WARNING] Secrets detected! See report: %SCAN_REPORT%
        set "CLEANUP_NEEDED=true"
    )
) else if "%SCANNER%" == "trufflehog" (
    echo [INFO] Running truffleHog scan...
    trufflehog git file://. --only-verified > "%SCAN_REPORT%" 2>&1
    for %%A in ("%SCAN_REPORT%") do if %%~zA gtr 0 (
        echo [WARNING] Secrets detected! See report: %SCAN_REPORT%
        set "CLEANUP_NEEDED=true"
    ) else (
        echo [INFO] No secrets detected by truffleHog
        set "CLEANUP_NEEDED=false"
    )
) else (
    echo [INFO] Performing manual secret scan...
    echo === Manual Secret Scan Report === > "%SCAN_REPORT%"
    echo Date: %date% %time% >> "%SCAN_REPORT%"
    echo Repository: %CD% >> "%SCAN_REPORT%"
    echo. >> "%SCAN_REPORT%"
    echo === Searching for common secret patterns === >> "%SCAN_REPORT%"
    
    REM Search for secrets in common file types
    findstr /s /i /c:"password" /c:"secret" /c:"key" /c:"token" /c:"api" *.py *.js *.env *.yaml *.yml *.json 2>nul >> "%SCAN_REPORT%"
    
    findstr /c:"password" /c:"secret" /c:"key" /c:"token" "%SCAN_REPORT%" >nul 2>&1
    if !errorlevel! equ 0 (
        echo [WARNING] Potential secrets found! Manual review required: %SCAN_REPORT%
        set "CLEANUP_NEEDED=true"
    ) else (
        echo [INFO] Manual scan completed - no obvious secrets found
        set "CLEANUP_NEEDED=false"
    )
)

if "%CLEANUP_NEEDED%" == "true" (
    echo [INFO] Secrets found - cleanup process required
    echo.
    echo [CRITICAL] Before proceeding, ensure you have:
    echo    1. Rotated ALL found credentials in their respective systems
    echo    2. Updated the HEAD code to use environment variables
    echo    3. Created .env.example with placeholder values
    echo.
    set /p "CONFIRM=Have you completed credential rotation? (y/N): "
    if /i not "!CONFIRM!" == "y" (
        echo [ERROR] Please complete credential rotation before proceeding
        exit /b 1
    )
    echo [SUCCESS] Credential rotation confirmed
    
    REM Create working copy
    echo [INFO] Creating working copy for cleanup...
    set "WORK_DIR=handover-work-%DATE%"
    git clone . "!WORK_DIR!"
    cd "!WORK_DIR!"
    
    echo [INFO] Manual history cleanup required
    echo Please use git-filter-repo or BFG Repo Cleaner to clean history
    echo After cleanup, manually verify no secrets remain in history
    pause
    
) else (
    echo [INFO] No secrets found - proceeding with direct mirror
)

REM Create handover repository
echo [INFO] Step 4: Creating handover repository...
echo [INFO] Manual step: Create new private repository for handover
echo Repository name suggestion: %~n0-handover
echo.
set /p "HANDOVER_REPO_URL=Enter handover repository URL: "

if "!HANDOVER_REPO_URL!" == "" (
    echo [ERROR] Handover repository URL required
    exit /b 1
)

REM Add handover remote and push
git remote add handover "!HANDOVER_REPO_URL!"
git tag -a "%HANDOVER_TAG%" -m "Repository handover %date%"

echo [INFO] Pushing to handover repository...
git push handover --all
git push handover --tags

echo [SUCCESS] Handover repository created and pushed

REM Generate final documentation
echo [INFO] Step 6: Generating handover documentation...
for /f %%i in ('git rev-parse HEAD') do set "COMMIT_HASH=%%i"

echo # Repository Handover Receipt > HANDOVER_RECEIPT_FINAL.md
echo. >> HANDOVER_RECEIPT_FINAL.md
echo **Repository**: %~n0 >> HANDOVER_RECEIPT_FINAL.md
echo **Date**: %date% >> HANDOVER_RECEIPT_FINAL.md
echo **Time**: %time% >> HANDOVER_RECEIPT_FINAL.md
echo **Handover Tag**: %HANDOVER_TAG% >> HANDOVER_RECEIPT_FINAL.md
echo **HEAD Commit**: !COMMIT_HASH! >> HANDOVER_RECEIPT_FINAL.md
echo. >> HANDOVER_RECEIPT_FINAL.md
echo ## Verification >> HANDOVER_RECEIPT_FINAL.md
echo ```bash >> HANDOVER_RECEIPT_FINAL.md
echo git clone !HANDOVER_REPO_URL! >> HANDOVER_RECEIPT_FINAL.md
echo cd %~n0 >> HANDOVER_RECEIPT_FINAL.md
echo git log --oneline -5 >> HANDOVER_RECEIPT_FINAL.md
echo git tag --list >> HANDOVER_RECEIPT_FINAL.md
echo ``` >> HANDOVER_RECEIPT_FINAL.md
echo. >> HANDOVER_RECEIPT_FINAL.md
echo **Handover completed**: %date% %time% >> HANDOVER_RECEIPT_FINAL.md

echo [SUCCESS] Repository handover process completed!
echo [INFO] Next steps:
echo [INFO] 1. Configure read-only access (SSH deploy key or collaborator)
echo [INFO] 2. Share handover repository URL with recipient
echo [INFO] 3. Provide HANDOVER_RECEIPT_FINAL.md as proof of completion

pause
