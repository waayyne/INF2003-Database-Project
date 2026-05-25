# CosmiQ - Beauty Product Sentiment Analyzer

An intelligent web application that analyzes beauty product reviews to provide sentiment-based recommendations and insights.

## 📋 Table of Contents
- [Features](#features)
- [System Requirements](#system-requirements)
- [Installation Guide](#installation-guide)
  - [Windows Installation](#windows-installation)
  - [Mac Installation](#mac-installation)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Usage Guide](#usage-guide)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## ✨ Features

- **Sentiment Analysis**: Automatically analyzes review text to determine positive, neutral, or negative sentiment
- **Product Search**: Search and filter products by rating, brand, price, and skin type
- **Interactive Dashboard**: Visualize review data with interactive charts and graphs
- **Recommendation Engine**: Get product recommendations based on your preferences
- **Multi-platform Support**: Works on both Windows and Mac

## 💻 System Requirements

### Minimum Requirements
- **RAM**: 4GB (8GB recommended)
- **Storage**: 2GB free space
- **Internet**: Required for initial setup only
- **Python**: Version 3.8 - 3.11 (3.12+ may have compatibility issues)

### Supported Operating Systems
- **Windows**: Windows 10 or 11 (64-bit)
- **Mac**: macOS 10.15 (Catalina) or newer

## 📥 Installation Guide

### Windows Installation

#### Step 1: Install Python
1. Download Python from [python.org](https://www.python.org/downloads/)
2. **IMPORTANT**: Check ✅ "Add Python to PATH" during installation
3. Verify installation:
```powershell
python --version
Step 2: Open Command Prompt
Press Win + R, type cmd, press Enter

Or search for "Command Prompt" in Start Menu

Step 3: Navigate to Project Folder
powershell
cd C:\Users\YourUsername\Desktop\cosmiq_project
Step 4: Create Virtual Environment
powershell
python -m venv venv
Step 5: Activate Virtual Environment
powershell
venv\Scripts\activate
You should see (venv) appear at the beginning of your command line.

Step 6: Install Required Packages
powershell
pip install --upgrade pip
pip install pandas streamlit plotly numpy seaborn nltk textblob scikit-learn
Mac Installation
Step 1: Install Python
Option A: Using Homebrew (Recommended)

bash
# Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python@3.11
Option B: Download from Python.org

Download Python from python.org

Run the installer package

Follow the installation wizard

Step 2: Open Terminal
Press Cmd + Space, type Terminal, press Enter

Or find Terminal in Applications > Utilities

Step 3: Navigate to Project Folder
bash
cd /Users/YourUsername/Desktop/cosmiq_project
Step 4: Create Virtual Environment
bash
python3 -m venv venv
Step 5: Activate Virtual Environment
bash
source venv/bin/activate
You should see (venv) appear at the beginning of your command line.

Step 6: Install Required Packages
bash
pip install --upgrade pip
pip install pandas streamlit plotly numpy seaborn nltk textblob scikit-learn
🚀 Quick Start
Step 1: Prepare Your Data
First, create a Python script called data_prep.py:

python
import pandas as pd

print("Loading data...")

# Load your CSV files (adjust filenames as needed)
try:
    products = pd.read_csv('product_info.csv')
    print(f"✅ Loaded {len(products)} products")
except:
    print("❌ product_info.csv not found")

try:
    reviews = pd.read_csv('reviews.csv')
    print(f"✅ Loaded {len(reviews)} reviews")
except:
    print("❌ reviews.csv not found")
    
# Create a sample for testing
if 'reviews' in locals():
    sample = reviews.head(5000)
    sample.to_csv('sample_reviews_5000.csv', index=False)
    print("✅ Created sample_reviews_5000.csv with 5000 reviews")
Run it:

bash
# Windows
python data_prep.py

# Mac
python3 data_prep.py
Step 2: Run Sentiment Analysis
Create simple_sentiment.py (included in project files) and run:

bash
# Windows
python simple_sentiment.py

# Mac
python3 simple_sentiment.py
Step 3: Launch the Dashboard
bash
# Windows & Mac both use:
streamlit run dashboard_simple.py
The dashboard will automatically open in your web browser at http://localhost:8501

📁 Project Structure
text
cosmiq_project/
│
├── data/                      # Your data files (create this folder)
│   ├── product_info.csv      # Product information
│   └── reviews.csv           # Review data
│
├── dashboard_simple.py       # Main dashboard application
├── data_explorer.py          # Data exploration script
├── simple_sentiment.py       # Sentiment analysis script
├── test_setup.py             # Environment test script
├── requirements.txt          # Package dependencies
├── README.md                 # This file
│
├── venv/                     # Virtual environment (created by you)
│
└── output/                   # Generated files
    ├── analyzed_reviews.csv  # Analysis results
    └── sample_reviews_5000.csv
📖 Usage Guide
Basic Navigation
Open Dashboard: streamlit run dashboard_simple.py

Use Filters: Left sidebar to filter by rating, sentiment, brand, skin type

View Charts: Interactive visualizations update automatically

Search Products: Use dropdown to see specific product reviews

Keyboard Shortcuts (In Dashboard)
R - Refresh data

Ctrl + F - Search within page

Ctrl + + - Zoom in

Ctrl + - - Zoom out

Sample Queries to Try
"Find highly rated products for dry skin"

Set Minimum Rating to 4

Select Skin Type: "dry"

"Show me products with mostly positive reviews"

In Sentiment filter, select only "positive"

"What do people say about expensive foundations?"

Set Price Range higher ($50+)

Look at sample reviews section

🔧 Troubleshooting
Common Windows Issues
Issue	Solution
'python' is not recognized	Reinstall Python and check "Add to PATH"
ModuleNotFoundError	Run pip install [package_name]
Permission errors	Run Command Prompt as Administrator
Virtual environment won't activate	Run Set-ExecutionPolicy Unrestricted -Scope Process
Common Mac Issues
Issue	Solution
command not found: python	Use python3 instead of python
pip3: command not found	Run python3 -m ensurepip
SSL Certificate errors	Run /Applications/Python\ 3.x/Install\ Certificates.command
Virtual environment won't activate	Run chmod +x venv/bin/activate
General Issues
Issue: "No module named 'matplotlib'"
bash
pip install matplotlib
Issue: Dashboard won't start
bash
# Check if port is in use
# Windows:
netstat -ano | findstr :8501

# Mac:
lsof -i :8501

# Kill the process or use different port
streamlit run dashboard.py --server.port 8502
Issue: Out of Memory Error
bash
# Process smaller sample first
# In data_prep.py, change:
sample = reviews.head(1000)  # Instead of 5000
Issue: Slow Performance
Use smaller dataset (1000-2000 reviews)

Close other applications

Restart your computer

📝 Creating requirements.txt
Run this to create a requirements file for easy installation:

bash
# Windows
pip freeze > requirements.txt

# Mac
pip3 freeze > requirements.txt
Then others can install with:

bash
pip install -r requirements.txt
🎯 Quick Commands Reference
Windows
powershell
# Activate environment
venv\Scripts\activate

# Deactivate environment
deactivate

# Run dashboard
streamlit run dashboard_simple.py

# Run Python script
python script_name.py
Mac
bash
# Activate environment
source venv/bin/activate

# Deactivate environment
deactivate

# Run dashboard
streamlit run dashboard_simple.py

# Run Python script
python3 script_name.py
📞 Getting Help
Check Python version: python --version (Windows) or python3 --version (Mac)

List installed packages: pip list

View Streamlit logs: Add --logger.level=debug to run command

Check this README for common solutions

🔄 Updating the Project
bash
# Pull latest changes (if using git)
git pull

# Update packages
pip install --upgrade -r requirements.txt

# Clear cache
streamlit cache clear
📄 License
This project is for educational purposes.

🙏 Acknowledgments
Built with Streamlit, Pandas, and Plotly

Dataset: Sephora product reviews

Happy analyzing! 🎉

text

## Also create a `requirements.txt` file:

```txt
pandas>=1.3.0
streamlit>=1.25.0
plotly>=5.14.0
numpy>=1.21.0
seaborn>=0.12.0
nltk>=3.7
textblob>=0.17.0
scikit-learn>=1.0.0
Create a setup.bat for Windows users:
batch
@echo off
echo ========================================
echo CosmiQ Setup for Windows
echo ========================================
echo.

echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python from python.org
    echo Make sure to check "Add Python to PATH"
    pause
    exit /b 1
)

echo Creating virtual environment...
python -m venv venv

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing packages...
pip install pandas streamlit plotly numpy seaborn nltk textblob scikit-learn

echo.
echo ========================================
echo Setup complete!
echo ========================================
echo.
echo Next steps:
echo 1. Place your CSV files in this folder
echo 2. Run: python data_prep.py
echo 3. Run: streamlit run dashboard_simple.py
echo.
pause
Create a setup.sh for Mac users:
bash
#!/bin/bash

echo "========================================"
echo "CosmiQ Setup for Mac"
echo "========================================"
echo ""

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 not found!"
    echo "Please install Python from python.org or run: brew install python@3.11"
    exit 1
fi

echo "Creating virtual environment..."
python3 -m venv venv

echo "Activating virtual environment..."
source venv/bin/activate

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing packages..."
pip install pandas streamlit plotly numpy seaborn nltk textblob scikit-learn

echo ""
echo "========================================"
echo "Setup complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Place your CSV files in this folder"
echo "2. Run: python3 data_prep.py"
echo "3. Run: streamlit run dashboard_simple.py"
echo ""
Make the Mac script executable:

bash
chmod +x setup.sh