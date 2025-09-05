# PAT - Prospecting Automation Tool

## Overview
PAT (Prospecting Automation Tool) is a Python-based desktop application built with PyQt5 for automated prospecting workflows. The application includes web automation capabilities using Selenium and database connectivity for data management.

## 🚀 Quick Start

### Prerequisites
- Python 3.7+
- Chrome browser (for Selenium automation)
- MySQL database access

### Installation
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd PAT
   ```

2. Create virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # or
   source .venv/bin/activate  # Linux/Mac
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Environment setup:
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

### Configuration
Copy `.env.example` to `.env` and configure your environment variables:

```env
# Database Configuration
DB_HOST=your-database-host
DB_USER=your-database-user
DB_PASSWORD=your-database-password
DB_NAME=your-database-name

# Optional: Chrome WebDriver path (if not in PATH)
CHROMEDRIVER_PATH=/path/to/chromedriver
```

### Running the Application
```bash
python pat.py
```

## 🏗️ Building Executable

The project includes PyInstaller specifications for creating standalone executables:

```bash
# Build executable
pyinstaller pat.spec

# Find executable in
./build/pat/pat.exe  # Windows
```

## 📁 Project Structure
```
PAT/
├── pat.py              # Main application
├── pat.spec            # PyInstaller build configuration
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
├── images/             # Application assets
│   └── cvr.png
├── sources/            # Data sources
│   └── Branche_Input.xlsx
└── build/              # Build outputs (excluded from git)
```

## 🔧 Features
- **GUI Interface**: Modern PyQt5-based desktop application
- **Web Automation**: Selenium WebDriver integration for browser automation
- **Database Integration**: MySQL connectivity for data persistence
- **Excel Processing**: Pandas integration for Excel file handling
- **Multi-threading**: Background processing capabilities

## 📋 Dependencies
Key Python packages (see `requirements.txt` for complete list):
- PyQt5 - GUI framework
- Selenium - Web automation
- pandas - Data processing
- mysql-connector-python - Database connectivity
- python-dotenv - Environment variable management

## 🔒 Security Notes
- Database credentials are managed via environment variables
- Never commit `.env` files to version control
- The application requires Chrome browser for Selenium automation
- Ensure proper database user permissions (principle of least privilege)

## 🐛 Troubleshooting

### Common Issues
1. **Chrome WebDriver Issues**:
   - Ensure Chrome browser is installed
   - Check ChromeDriver compatibility with your Chrome version
   - Verify ChromeDriver is in PATH or set CHROMEDRIVER_PATH

2. **Database Connection Issues**:
   - Verify database credentials in `.env`
   - Check network connectivity to database host
   - Ensure database user has required permissions

3. **Import Errors**:
   - Activate virtual environment
   - Install all requirements: `pip install -r requirements.txt`

### Build Issues
- Ensure all dependencies are installed in the virtual environment
- Check PyInstaller logs for missing modules
- Verify all resource files are properly included in spec file

## 📞 Support
For technical support or questions about this handover package, contact the repository administrator.

---
*Last updated*: $(date +%Y-%m-%d)
*Version*: Handover Package
