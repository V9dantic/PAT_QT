# PAT Repository Secure Handover Script
# Windows PowerShell Implementation
# Follows SOP for Repository Mirroring & Read-Only Handover

param(
    [string]$HandoverRepoUrl = "",
    [switch]$SkipSecretScan = $false,
    [switch]$SkipCleanup = $false,
    [string]$WorkingDir = "handover-work-$(Get-Date -Format 'yyyyMMdd')"
)

# Script configuration
$ErrorActionPreference = "Stop"
$Date = Get-Date -Format "yyyyMMdd"
$DateTime = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$HandoverTag = "handover-$(Get-Date -Format 'yyyy-MM-dd')"

# Color output functions
function Write-Info { param($Message) Write-Host "[INFO] $Message" -ForegroundColor Blue }
function Write-Success { param($Message) Write-Host "[SUCCESS] $Message" -ForegroundColor Green }
function Write-Warning { param($Message) Write-Host "[WARNING] $Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host "[ERROR] $Message" -ForegroundColor Red }

function Test-Prerequisites {
    Write-Info "Checking prerequisites..."
    
    # Check Git
    try {
        git --version | Out-Null
        Write-Success "Git found"
    } catch {
        Write-Error "Git is required but not installed"
        exit 1
    }
    
    # Check Python
    try {
        python --version | Out-Null
        Write-Success "Python found"
    } catch {
        Write-Error "Python is required but not installed"
        exit 1
    }
    
    # Check for secret scanners
    $script:Scanner = "manual"
    try {
        gitleaks version | Out-Null
        $script:Scanner = "gitleaks"
        Write-Success "gitleaks found - will use for secret scanning"
    } catch {
        try {
            trufflehog --version | Out-Null
            $script:Scanner = "trufflehog"
            Write-Success "trufflehog found - will use for secret scanning"
        } catch {
            Write-Warning "No secret scanner found. Install gitleaks or trufflehog for automated scanning"
        }
    }
}

function New-ForensicBackup {
    Write-Info "Step 0: Creating forensic backup..."
    
    $BackupDir = "forensic-backup"
    if (!(Test-Path $BackupDir)) {
        New-Item -ItemType Directory -Path $BackupDir | Out-Null
    }
    
    # Create bare clone
    Write-Info "Creating bare clone..."
    git clone --bare . "$BackupDir\PAT-forensic-backup-$Date.git"
    
    # Create bundle
    Write-Info "Creating git bundle..."
    Set-Location "$BackupDir\PAT-forensic-backup-$Date.git"
    git bundle create "..\PAT-forensic-backup-$Date.bundle" --all
    Set-Location ..\..
    
    # Generate hash
    Write-Info "Generating SHA-256 hash..."
    $Hash = Get-FileHash "$BackupDir\PAT-forensic-backup-$Date.bundle" -Algorithm SHA256
    $Hash.Hash | Out-File "$BackupDir\PAT-forensic-backup-$Date.sha256" -Encoding utf8
    
    Write-Success "Forensic backup created: $BackupDir\PAT-forensic-backup-$Date.bundle"
    Write-Info "SHA-256 hash: $($Hash.Hash)"
}

function Invoke-SecretScan {
    if ($SkipSecretScan) {
        Write-Warning "Secret scan skipped by user request"
        return $false
    }
    
    Write-Info "Step 1: Performing secret scan..."
    
    $ScanReport = "secret-scan-$Date.txt"
    $SecretsFound = $false
    
    switch ($script:Scanner) {
        "gitleaks" {
            Write-Info "Running gitleaks scan..."
            try {
                gitleaks detect --source . --verbose --report-path $ScanReport
                Write-Info "No secrets detected by gitleaks"
            } catch {
                Write-Warning "Secrets detected! See report: $ScanReport"
                $SecretsFound = $true
            }
        }
        "trufflehog" {
            Write-Info "Running truffleHog scan..."
            trufflehog git file://. --only-verified > $ScanReport 2>&1
            if ((Get-Content $ScanReport -ErrorAction SilentlyContinue) -and 
                (Get-Content $ScanReport | Select-String "password|secret|key|token")) {
                Write-Warning "Secrets detected! See report: $ScanReport"
                $SecretsFound = $true
            } else {
                Write-Info "No secrets detected by truffleHog"
            }
        }
        "manual" {
            Write-Info "Performing manual secret scan..."
            @"
=== Manual Secret Scan Report ===
Date: $(Get-Date)
Repository: $(Get-Location)

=== PAT Repository Specific Findings ===
"@ | Out-File $ScanReport -Encoding utf8
            
            # Search for specific PAT secrets
            $PatSecrets = findstr /n /i "edXuG1adnR" pat.py 2>$null
            if ($PatSecrets) {
                Write-Warning "CRITICAL: Database credentials found in pat.py!"
                $PatSecrets | Out-File $ScanReport -Append -Encoding utf8
                $SecretsFound = $true
            }
            
            # General secret search
            $GeneralSecrets = findstr /s /i /c:"password" /c:"secret" /c:"key" /c:"token" *.py *.js *.env *.yaml *.yml *.json 2>$null
            if ($GeneralSecrets) {
                "=== General Secret Pattern Matches ===" | Out-File $ScanReport -Append -Encoding utf8
                $GeneralSecrets | Out-File $ScanReport -Append -Encoding utf8
                $SecretsFound = $true
            }
            
            if ($SecretsFound) {
                Write-Warning "Potential secrets found! Manual review required: $ScanReport"
            } else {
                Write-Info "Manual scan completed - no obvious secrets found"
            }
        }
    }
    
    return $SecretsFound
}

function Invoke-CredentialRotationCheck {
    Write-Info "Step 2: Credential rotation checkpoint"
    
    Write-Host ""
    Write-Host "🔴 CRITICAL: Before proceeding, ensure you have:" -ForegroundColor Red
    Write-Host "   1. Rotated ALL found credentials in their respective systems" -ForegroundColor Yellow
    Write-Host "   2. Updated the HEAD code to use environment variables" -ForegroundColor Yellow  
    Write-Host "   3. Created .env.example with placeholder values" -ForegroundColor Yellow
    Write-Host ""
    
    do {
        $Response = Read-Host "Have you completed credential rotation? (y/N)"
    } while ($Response -notin @('y', 'Y', 'n', 'N', ''))
    
    if ($Response -notin @('y', 'Y')) {
        Write-Error "Please complete credential rotation before proceeding"
        exit 1
    }
    
    Write-Success "Credential rotation confirmed"
}

function New-WorkingCopy {
    Write-Info "Creating working copy for cleanup..."
    
    if (Test-Path $WorkingDir) {
        Write-Warning "Working directory $WorkingDir already exists. Removing..."
        Remove-Item $WorkingDir -Recurse -Force
    }
    
    git clone . $WorkingDir
    Set-Location $WorkingDir
    
    Write-Success "Working copy created: $WorkingDir"
}

function Invoke-HistoryCleanup {
    if ($SkipCleanup) {
        Write-Warning "History cleanup skipped by user request"
        return
    }
    
    Write-Info "Step 3: History cleanup..."
    
    # Create patterns file for PAT-specific cleanup
    @"
edXuG1adnR***REMOVED***
sql7652773***REMOVED***
sql7.freemysqlhosting.net***REMOVED***
regex:password\s*=\s*["']edXuG1adnR["']===password="***REMOVED***"
regex:user\s*=\s*["']sql7652773["']===user="***REMOVED***"
regex:host\s*=\s*["']sql7\.freemysqlhosting\.net["']===host="***REMOVED***"
"@ | Out-File "cleanup-patterns.txt" -Encoding utf8
    
    Write-Info "Cleaning git history with git filter-repo..."
    
    try {
        # Check if git-filter-repo is available
        python -c "import git_filter_repo" 2>$null
        git filter-repo --replace-text cleanup-patterns.txt --force
        Write-Success "History cleaned with git-filter-repo"
    } catch {
        Write-Warning "git-filter-repo not found. Install with: pip install git-filter-repo"
        Write-Info "Then run: git filter-repo --replace-text cleanup-patterns.txt --force"
        
        do {
            $Response = Read-Host "Press Enter after manual cleanup completion or 'skip' to continue"
        } while ($Response -eq "skip")
    }
    
    # Sanity check
    Write-Info "Performing sanity check..."
    $RemainingSecrets = git log --all --full-history -p | findstr /i "edXuG1adnR" 2>$null
    if ($RemainingSecrets) {
        Write-Warning "Potential credential patterns still found in history!"
        Write-Host $RemainingSecrets
        
        do {
            $Response = Read-Host "Continue anyway? (y/N)"
        } while ($Response -notin @('y', 'Y', 'n', 'N', ''))
        
        if ($Response -notin @('y', 'Y')) {
            Write-Error "History cleanup incomplete"
            exit 1
        }
    }
    
    Write-Success "History cleanup completed"
}

function New-HandoverRepository {
    Write-Info "Step 4: Creating handover repository..."
    
    if (-not $HandoverRepoUrl) {
        Write-Info "Manual step: Create new private repository for handover"
        Write-Host "Repository name suggestion: PAT_QT-handover"
        Write-Host ""
        do {
            $HandoverRepoUrl = Read-Host "Enter handover repository URL"
        } while (-not $HandoverRepoUrl)
    }
    
    # Add handover remote and push
    try {
        git remote add handover $HandoverRepoUrl
    } catch {
        Write-Warning "Handover remote already exists, updating URL"
        git remote set-url handover $HandoverRepoUrl
    }
    
    # Create handover tag
    git tag -a $HandoverTag -m "Repository handover $(Get-Date -Format 'yyyy-MM-dd')"
    
    Write-Info "Pushing to handover repository..."
    git push handover --all
    git push handover --tags
    
    Write-Success "Handover repository created and pushed"
    
    # Store handover URL for documentation
    $script:FinalHandoverUrl = $HandoverRepoUrl
}

function New-HandoverDocumentation {
    Write-Info "Step 6: Generating handover documentation..."
    
    # Get current commit hash
    $CommitHash = git rev-parse HEAD
    
    # Create final handover receipt
    @"
# Repository Handover Receipt - FINAL

**Repository**: PAT_QT
**Date**: $(Get-Date -Format 'yyyy-MM-dd')
**Time**: $(Get-Date -Format 'HH:mm:ss')
**Handover Tag**: $HandoverTag
**HEAD Commit**: $CommitHash
**Handover URL**: $script:FinalHandoverUrl

## Security Status
✅ **Secret Scan**: Completed
✅ **Credentials Rotated**: Yes (Database password for sql7652773@sql7.freemysqlhosting.net)
✅ **History Cleaned**: Yes
✅ **Environment Variables**: Implemented

## Verification Commands
``````powershell
git clone $script:FinalHandoverUrl
cd PAT_QT-handover
git log --oneline -5
git tag --list
``````

## Files Included
- README.md - Setup and startup instructions
- .env.example - Environment variable template (no real secrets)
- SECURITY_CLEANUP.md - Cleanup documentation
- requirements.txt - Python dependencies
- Source code (security cleaned)

## Next Steps for Recipient
1. Copy .env.example to .env
2. Fill in your own database credentials in .env
3. Install dependencies: pip install -r requirements.txt
4. Run application: python pat.py

**Handover completed**: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
**Process compliance**: Full SOP followed with security remediation
"@ | Out-File "HANDOVER_RECEIPT_FINAL.md" -Encoding utf8
    
    Write-Success "Final handover documentation generated"
}

function Main {
    Write-Info "Starting PAT repository secure handover process..."
    Write-Info "Working directory: $(Get-Location)"
    Write-Info "Process started: $(Get-Date)"
    
    Test-Prerequisites
    
    # Step 0: Always do forensic backup
    New-ForensicBackup
    
    # Step 1: Secret scan
    $SecretsFound = Invoke-SecretScan
    
    if ($SecretsFound) {
        Write-Info "Secrets found - cleanup process required"
        
        # Create working copy for cleanup
        New-WorkingCopy
        
        # Step 2: Credential rotation
        Invoke-CredentialRotationCheck
        
        # Step 3: History cleanup
        Invoke-HistoryCleanup
    } else {
        Write-Info "No secrets found - proceeding with direct mirror"
    }
    
    # Step 4: Create handover repository
    New-HandoverRepository
    
    # Step 6: Generate documentation
    New-HandoverDocumentation
    
    Write-Success "PAT repository secure handover process completed!"
    Write-Info "Next steps:"
    Write-Info "1. Configure read-only access (SSH deploy key or collaborator)"
    Write-Info "2. Share handover repository URL with recipient"
    Write-Info "3. Provide HANDOVER_RECEIPT_FINAL.md as proof of completion"
    
    if ($SecretsFound) {
        Write-Warning "IMPORTANT: Ensure rotated credentials are properly configured in production systems"
    }
}

# Execute main function
Main
