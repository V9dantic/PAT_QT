#!/bin/bash
# Repository Handover Automation Script
# Implements the SOP for secure repository mirroring and handover

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATE=$(date +%Y%m%d)
DATETIME=$(date +%Y-%m-%d_%H-%M-%S)
HANDOVER_TAG="handover-$(date +%Y-%m-%d)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Check dependencies
check_dependencies() {
    log "Checking dependencies..."
    
    command -v git >/dev/null 2>&1 || error "git is required but not installed"
    command -v sha256sum >/dev/null 2>&1 || command -v shasum >/dev/null 2>&1 || error "sha256sum or shasum is required"
    
    if command -v gitleaks >/dev/null 2>&1; then
        success "gitleaks found - will use for secret scanning"
        SCANNER="gitleaks"
    elif command -v truffleHog >/dev/null 2>&1; then
        success "truffleHog found - will use for secret scanning"
        SCANNER="truffleHog"
    else
        warn "No secret scanner found. Install gitleaks or truffleHog for automated scanning"
        SCANNER="manual"
    fi
}

# Step 0: Forensic backup
forensic_backup() {
    log "Step 0: Creating forensic backup..."
    
    BACKUP_DIR="${SCRIPT_DIR}/forensic-backup"
    mkdir -p "$BACKUP_DIR"
    
    # Create bare clone
    log "Creating bare clone..."
    git clone --bare . "${BACKUP_DIR}/forensic-backup-${DATE}.git"
    
    # Create bundle
    log "Creating git bundle..."
    cd "${BACKUP_DIR}/forensic-backup-${DATE}.git"
    git bundle create "../forensic-backup-${DATE}.bundle" --all
    cd "$SCRIPT_DIR"
    
    # Generate hash
    log "Generating SHA-256 hash..."
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "${BACKUP_DIR}/forensic-backup-${DATE}.bundle" > "${BACKUP_DIR}/forensic-backup-${DATE}.sha256"
    else
        shasum -a 256 "${BACKUP_DIR}/forensic-backup-${DATE}.bundle" > "${BACKUP_DIR}/forensic-backup-${DATE}.sha256"
    fi
    
    success "Forensic backup created: ${BACKUP_DIR}/forensic-backup-${DATE}.bundle"
    log "SHA-256 hash: $(cat "${BACKUP_DIR}/forensic-backup-${DATE}.sha256")"
}

# Step 1: Secret scan
secret_scan() {
    log "Step 1: Performing secret scan..."
    
    SCAN_REPORT="${SCRIPT_DIR}/secret-scan-${DATE}.txt"
    
    case "$SCANNER" in
        "gitleaks")
            log "Running gitleaks scan..."
            if gitleaks detect --source . --verbose --report-path "$SCAN_REPORT" 2>&1; then
                log "No secrets detected by gitleaks"
                return 0
            else
                warn "Secrets detected! See report: $SCAN_REPORT"
                return 1
            fi
            ;;
        "truffleHog")
            log "Running truffleHog scan..."
            if trufflehog git file://. --only-verified > "$SCAN_REPORT" 2>&1; then
                if [ -s "$SCAN_REPORT" ]; then
                    warn "Secrets detected! See report: $SCAN_REPORT"
                    return 1
                else
                    log "No secrets detected by truffleHog"
                    return 0
                fi
            else
                error "truffleHog scan failed"
            fi
            ;;
        "manual")
            log "Performing manual secret scan..."
            {
                echo "=== Manual Secret Scan Report ==="
                echo "Date: $(date)"
                echo "Repository: $(pwd)"
                echo ""
                echo "=== Searching for common secret patterns ==="
                grep -r -i "password\|secret\|key\|token\|api" . \
                    --include="*.py" --include="*.js" --include="*.env" \
                    --include="*.yaml" --include="*.yml" --include="*.json" \
                    --exclude-dir=".git" --exclude-dir="node_modules" \
                    --exclude-dir=".venv" --exclude-dir="venv" 2>/dev/null || true
            } > "$SCAN_REPORT"
            
            if [ -s "$SCAN_REPORT" ] && grep -q "password\|secret\|key\|token" "$SCAN_REPORT"; then
                warn "Potential secrets found! Manual review required: $SCAN_REPORT"
                return 1
            else
                log "Manual scan completed - no obvious secrets found"
                return 0
            fi
            ;;
    esac
}

# Create working copy for cleanup
create_working_copy() {
    log "Creating working copy for cleanup..."
    
    WORK_DIR="${SCRIPT_DIR}/handover-work-${DATE}"
    git clone . "$WORK_DIR"
    cd "$WORK_DIR"
    
    success "Working copy created: $WORK_DIR"
}

# Interactive credential rotation reminder
credential_rotation() {
    log "Step 2: Credential rotation checkpoint"
    
    echo ""
    echo "🔴 CRITICAL: Before proceeding, ensure you have:"
    echo "   1. Rotated ALL found credentials in their respective systems"
    echo "   2. Updated the HEAD code to use environment variables"
    echo "   3. Created .env.example with placeholder values"
    echo ""
    
    read -p "Have you completed credential rotation? (y/N): " -r
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        error "Please complete credential rotation before proceeding"
    fi
    
    success "Credential rotation confirmed"
}

# History cleanup
history_cleanup() {
    log "Step 3: History cleanup..."
    
    # Create patterns file for cleanup
    cat > cleanup-patterns.txt << 'EOF'
password***REMOVED***
secret***REMOVED***
key***REMOVED***
token***REMOVED***
regex:password\s*=\s*["'][^"']+["']===password="***REMOVED***"
regex:host\s*=\s*["'][^"']+["']===host="***REMOVED***"
EOF
    
    log "Cleaning git history with git filter-repo..."
    
    if command -v git-filter-repo >/dev/null 2>&1; then
        git filter-repo --replace-text cleanup-patterns.txt --force
    else
        warn "git-filter-repo not found. Manual history cleanup required."
        echo "Install with: pip install git-filter-repo"
        echo "Then run: git filter-repo --replace-text cleanup-patterns.txt --force"
        read -p "Press Enter after manual cleanup completion..."
    fi
    
    # Sanity check
    log "Performing sanity check..."
    if git log --all --full-history -p | grep -i "password.*=" | head -5; then
        warn "Potential credential patterns still found in history!"
        read -p "Continue anyway? (y/N): " -r
        [[ ! $REPLY =~ ^[Yy]$ ]] && error "History cleanup incomplete"
    fi
    
    success "History cleanup completed"
}

# Create handover repository
create_handover_repo() {
    log "Step 4: Creating handover repository..."
    
    # This would typically involve creating a new remote repository
    log "Manual step: Create new private repository for handover"
    echo "Repository name suggestion: ${PWD##*/}-handover"
    echo ""
    read -p "Enter handover repository URL: " HANDOVER_REPO_URL
    
    if [ -z "$HANDOVER_REPO_URL" ]; then
        error "Handover repository URL required"
    fi
    
    # Add handover remote and push
    git remote add handover "$HANDOVER_REPO_URL"
    
    # Create handover tag
    git tag -a "$HANDOVER_TAG" -m "Repository handover $(date +%Y-%m-%d)"
    
    log "Pushing to handover repository..."
    git push handover --all
    git push handover --tags
    
    success "Handover repository created and pushed"
}

# Generate final documentation
generate_documentation() {
    log "Step 6: Generating handover documentation..."
    
    # Update handover receipt with actual values
    COMMIT_HASH=$(git rev-parse HEAD)
    
    # Create final handover receipt
    cat > HANDOVER_RECEIPT_FINAL.md << EOF
# Repository Handover Receipt

**Repository**: ${PWD##*/}
**Date**: $(date +%Y-%m-%d)
**Time**: $(date +%H:%M:%S)
**Handover Tag**: $HANDOVER_TAG
**HEAD Commit**: $COMMIT_HASH

## Verification
\`\`\`bash
git clone $HANDOVER_REPO_URL
cd ${PWD##*/}
git log --oneline -5
git tag --list
\`\`\`

## Files Included
- README.md
- .env.example
- SECURITY_CLEANUP.md (if applicable)
- Source code (cleaned)

**Handover completed**: $(date +'%Y-%m-%d %H:%M:%S')
EOF
    
    success "Documentation generated"
}

# Main execution
main() {
    log "Starting repository handover process..."
    log "Working directory: $(pwd)"
    log "Process started: $(date)"
    
    check_dependencies
    
    # Step 0: Always do forensic backup
    forensic_backup
    
    # Step 1: Secret scan
    if secret_scan; then
        log "No secrets found - proceeding with direct mirror"
        CLEANUP_NEEDED=false
    else
        log "Secrets found - cleanup process required"
        CLEANUP_NEEDED=true
        
        # Create working copy for cleanup
        create_working_copy
        
        # Step 2: Credential rotation
        credential_rotation
        
        # Step 3: History cleanup
        history_cleanup
    fi
    
    # Step 4: Create handover repository
    create_handover_repo
    
    # Step 6: Generate documentation
    generate_documentation
    
    success "Repository handover process completed!"
    log "Next steps:"
    log "1. Configure read-only access (SSH deploy key or collaborator)"
    log "2. Share handover repository URL with recipient"
    log "3. Provide HANDOVER_RECEIPT_FINAL.md as proof of completion"
}

# Script execution
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi
