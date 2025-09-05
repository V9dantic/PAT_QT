# SOP: Repository Mirroring & Read-Only Handover

## Ziel
Ein Read-Only-Übergabe-Repository bereitstellen mit optionaler Bereinigung sensibler Informationen.

## Grundsätze
- ✅ Original-Repo niemals umschreiben - nur Kopien bearbeiten
- ✅ Keine fremden Tokens/Passwörter verwenden
- ✅ Nur Arbeitgeber-Artefakte übergeben
- ✅ Nachweisbare, revisionssichere Durchführung

## Ablauf (Decision Tree)

### 0️⃣ Forensische Sicherung (IMMER)
```bash
# Vollständige Bare-Kopie erstellen
git clone --bare <source-repo> forensic-backup.git
cd forensic-backup.git
git bundle create ../forensic-backup-$(date +%Y%m%d).bundle --all

# SHA-256 Hash für Beweissicherung
sha256sum ../forensic-backup-$(date +%Y%m%d).bundle > ../forensic-backup-$(date +%Y%m%d).sha256
```

### 1️⃣ Secret-Scan (Erkennungsphase)
```bash
# Mit gitleaks (empfohlen)
gitleaks detect --source . --verbose

# Mit truffleHog (alternative)
trufflehog git file://. --only-verified

# Manuelle Suche nach bekannten Mustern
grep -r -i "password\|secret\|key\|token" . --include="*.py" --include="*.js" --include="*.env"
```

**Entscheidung:**
- **Fall A**: Keine sensiblen Daten → Springe zu Schritt 4 (Mirror)
- **Fall B**: Sensible Daten gefunden → Fahre mit Schritt 2 fort

### 2️⃣ Sofortmaßnahmen bei Funden
- [ ] Credentials in den jeweiligen Systemen rotieren
- [ ] HEAD-Stand bereinigen (Umstellung auf Umgebungsvariablen)
- [ ] `.env.example` Datei erstellen

### 3️⃣ Historie bereinigen (nur wenn nötig)
```bash
# Mit BFG Repo-Cleaner
java -jar bfg.jar --replace-text passwords.txt repo-copy.git

# Mit git-filter-repo
git filter-repo --replace-text passwords.txt

# Sanity-Check
git log --all --full-history -- "*" | grep -i "password\|secret\|key"
```

### 4️⃣ Übergabe-Repository erstellen
```bash
# Neues privates Repo anlegen (GitHub/GitLab)
gh repo create handover-PAT --private

# Mirror push
git clone --mirror <bereinigte-quelle> temp-mirror
cd temp-mirror
git remote set-url origin <handover-repo-url>
git push --mirror

# Übergabe-Tag setzen
git tag -a "handover-$(date +%Y-%m-%d)" -m "Repository handover $(date +%Y-%m-%d)"
git push --tags
```

### 5️⃣ Read-Only-Freigabe
**Bevorzugt: SSH Deploy Key**
```bash
# SSH Key generieren
ssh-keygen -t ed25519 -C "handover-readonly-$(date +%Y%m%d)" -f handover_readonly_key

# Public Key im Repo als Deploy Key hinzufügen (Read-Only)
# Private Key sicher an Empfänger übermitteln
```

**Alternativ: Kollaborator mit Read-Zugriff**

### 6️⃣ Handover-Beleg & Dokumentation
Siehe: `HANDOVER_RECEIPT.md` und begleitende Dateien

## Tools & Dependencies
```bash
# Secret Scanner installieren
brew install gitleaks
# oder
pip install truffleHog

# BFG Repo Cleaner (Java)
wget https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar

# git-filter-repo
pip install git-filter-repo

# GitHub CLI (optional)
brew install gh
```

## Checkliste DoD (Definition of Done)
- [ ] Forensische Sicherung erstellt und verifiziert
- [ ] Secret-Scan durchgeführt und dokumentiert
- [ ] Bei Funden: Credentials rotiert
- [ ] Historie bereinigt (falls nötig)
- [ ] Übergabe-Repository erstellt und gespiegelt
- [ ] Read-Only-Zugriff konfiguriert
- [ ] Handover-Beleg erstellt
- [ ] Begleitdokumentation vollständig
- [ ] Sanity-Check erfolgreich

## Sicherheitshinweise
⚠️ **WICHTIG**: Original-Repository niemals direkt bearbeiten
⚠️ **WICHTIG**: Alle gefundenen Credentials SOFORT rotieren
⚠️ **WICHTIG**: Keine privaten Access-Tokens verwenden oder weitergeben

---
*Erstellt: $(date +%Y-%m-%d)*
*Version: 1.0*
