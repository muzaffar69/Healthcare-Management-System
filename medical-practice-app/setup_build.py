#!/usr/bin/env python3
"""
Build script for Medical Practice Management Desktop Application
Creates a Windows executable using PyInstaller
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# Application information
APP_NAME = "Medical Practice Management"
APP_VERSION = "2.0.0"
APP_ICON = "assets/icon.ico"
MAIN_SCRIPT = "main.py"

def create_project_structure():
    """Create the necessary project structure."""
    print("Creating project structure...")
    
    directories = [
        "backend",
        "templates",
        "static",
        "static/css",
        "static/js",
        "assets",
        "logs",
        "config"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    # Create __init__.py files
    Path("backend/__init__.py").touch()
    
    print("✓ Project structure created")

def create_requirements_file():
    """Create requirements.txt file."""
    requirements = """# Medical Practice Management - Requirements
pywebview>=4.0.0
azure-cosmos>=4.5.0
azure-identity>=1.14.0
azure-storage-blob>=12.19.0
azure-mgmt-resource>=23.0.0
azure-mgmt-cosmosdb>=9.3.0
azure-mgmt-storage>=21.1.0
requests>=2.31.0
cryptography>=41.0.0
python-dotenv>=1.0.0

# Development dependencies
pyinstaller>=6.0.0
"""
    
    with open("requirements.txt", "w") as f:
        f.write(requirements)
    
    print("✓ requirements.txt created")

def create_pyinstaller_spec():
    """Create PyInstaller spec file."""
    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['{MAIN_SCRIPT}'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
        ('assets', 'assets'),
    ],
    hiddenimports=[
        'azure.cosmos',
        'azure.identity',
        'azure.storage.blob',
        'azure.mgmt.resource',
        'azure.mgmt.cosmosdb',
        'azure.mgmt.storage',
        'cryptography',
        'dotenv',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{APP_NAME}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version_info.txt',
    icon='{APP_ICON}' if os.path.exists('{APP_ICON}') else None,
)
"""
    
    with open("medical_practice.spec", "w") as f:
        f.write(spec_content)
    
    print("✓ PyInstaller spec file created")

def create_version_info():
    """Create version information file for Windows."""
    version_info = f"""# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx

VSVersionInfo(
  ffi=FixedFileInfo(
    # filevers and prodvers should be always a tuple with four items: (1, 2, 3, 4)
    # Set not needed items to zero 0.
    filevers=(2, 0, 0, 0),
    prodvers=(2, 0, 0, 0),
    # Contains a bitmask that specifies the valid bits 'flags'r
    mask=0x3f,
    # Contains a bitmask that specifies the Boolean attributes of the file.
    flags=0x0,
    # The operating system for which this file was designed.
    # 0x4 - NT and there is no need to change it.
    OS=0x4,
    # The general type of file.
    # 0x1 - the file is an application.
    fileType=0x1,
    # The function of the file.
    # 0x0 - the function is not defined for this fileType
    subtype=0x0,
    # Creation date and time stamp.
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'Medical Practice Solutions'),
        StringStruct(u'FileDescription', u'{APP_NAME}'),
        StringStruct(u'FileVersion', u'{APP_VERSION}'),
        StringStruct(u'InternalName', u'medical_practice'),
        StringStruct(u'LegalCopyright', u'Copyright (c) 2024 Medical Practice Solutions'),
        StringStruct(u'OriginalFilename', u'{APP_NAME}.exe'),
        StringStruct(u'ProductName', u'{APP_NAME}'),
        StringStruct(u'ProductVersion', u'{APP_VERSION}')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""
    
    with open("version_info.txt", "w") as f:
        f.write(version_info)
    
    print("✓ Version info file created")

def create_run_script():
    """Create a development run script."""
    run_script = """#!/usr/bin/env python3
\"\"\"
Development run script for Medical Practice Management
\"\"\"

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the main application
from main import main

if __name__ == '__main__':
    main()
"""
    
    with open("run_dev.py", "w") as f:
        f.write(run_script)
    
    if os.name != 'nt':
        os.chmod("run_dev.py", 0o755)
    
    print("✓ Development run script created")

def create_batch_files():
    """Create Windows batch files for easy execution."""
    
    # Install dependencies batch file
    install_bat = """@echo off
echo Installing dependencies for Medical Practice Management...
echo.
pip install -r requirements.txt
echo.
echo Dependencies installed successfully!
pause
"""
    
    with open("install_dependencies.bat", "w") as f:
        f.write(install_bat)
    
    # Run development batch file
    run_dev_bat = """@echo off
echo Starting Medical Practice Management (Development Mode)...
echo.
python run_dev.py
pause
"""
    
    with open("run_development.bat", "w") as f:
        f.write(run_dev_bat)
    
    # Build executable batch file
    build_bat = """@echo off
echo Building Medical Practice Management executable...
echo.
pyinstaller medical_practice.spec --clean
echo.
echo Build complete! Check the 'dist' folder for the executable.
pause
"""
    
    with open("build_executable.bat", "w") as f:
        f.write(build_bat)
    
    print("✓ Batch files created")

def create_readme():
    """Create README file."""
    readme_content = f"""# Medical Practice Management Desktop Application

Version: {APP_VERSION}

## Overview
A modern desktop application for managing medical practice operations including doctor accounts, pharmacy accounts, laboratory accounts, and subscriptions.

## Setup Instructions

### 1. Install Python
- Download and install Python 3.8 or higher from https://www.python.org/
- Make sure to check "Add Python to PATH" during installation

### 2. Install Dependencies
Run the following command or double-click `install_dependencies.bat`:
```
pip install -r requirements.txt
```

### 3. Configure Azure Connection
1. Copy `config.example.json` to `config.json`
2. Update the configuration with your Azure credentials:
   - Azure Tenant ID
   - Azure Client ID and Secret
   - Cosmos DB endpoint and key
   - Storage account details

### 4. Run the Application

#### Development Mode
Double-click `run_development.bat` or run:
```
python run_dev.py
```

#### Build Executable
Double-click `build_executable.bat` or run:
```
pyinstaller medical_practice.spec
```

The executable will be created in the `dist` folder.

## Features
- Secure admin authentication
- Doctor account management
- Pharmacy and laboratory account tracking
- Subscription management
- Data export functionality
- Dark/Light theme support
- Keyboard shortcuts

## Keyboard Shortcuts
- `Ctrl+N`: New Doctor
- `Ctrl+R` or `F5`: Refresh Data
- `Ctrl+F`: Focus Search
- `Ctrl+E`: Export Current View
- `Ctrl+L`: Sign Out
- `F1`: Show Help

## Initial Login
On first run, the application will create initial admin credentials.
Check the console output or the file:
`~/.medical_practice/initial_credentials.txt`

**Important**: Delete this file after noting the credentials!

## Support
For technical support, please contact your system administrator.

## License
Copyright (c) 2024 Medical Practice Solutions. All rights reserved.
"""
    
    with open("README.md", "w") as f:
        f.write(readme_content)
    
    print("✓ README.md created")

def create_config_example():
    """Create example configuration file."""
    config_example = """{
    "azure_tenant_id": "your-tenant-id-here",
    "azure_client_id": "your-client-id-here",
    "azure_client_secret": "your-client-secret-here",
    "subscription_id": "your-subscription-id-here",
    "cosmos_endpoint": "https://your-cosmos-account.documents.azure.com:443/",
    "cosmos_key": "your-cosmos-primary-key-here",
    "cosmos_database": "medical_practice",
    "cosmos_users_container": "users",
    "cosmos_patients_container": "patients",
    "storage_account_name": "your-storage-account",
    "storage_account_key": "your-storage-key",
    "default_subscription_period": 365
}
"""
    
    with open("config.example.json", "w") as f:
        f.write(config_example)
    
    print("✓ config.example.json created")

def create_gitignore():
    """Create .gitignore file."""
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.venv
pip-log.txt
pip-delete-this-directory.txt

# PyInstaller
*.manifest
*.spec
build/
dist/
*.exe

# Configuration
config.json
.env
*.key

# Credentials
admin_credentials.json
initial_credentials.txt
.medical_practice/

# Logs
logs/
*.log

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Temporary files
*.tmp
*.temp
*.cache
"""
    
    with open(".gitignore", "w") as f:
        f.write(gitignore_content)
    
    print("✓ .gitignore created")

def main():
    """Main build setup function."""
    print("\n" + "="*60)
    print("Medical Practice Management - Build Setup")
    print("="*60 + "\n")
    
    # Create all necessary files and structure
    create_project_structure()
    create_requirements_file()
    create_pyinstaller_spec()
    create_version_info()
    create_run_script()
    create_batch_files()
    create_readme()
    create_config_example()
    create_gitignore()
    
    print("\n" + "="*60)
    print("Setup Complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. Place your application files in the appropriate directories:")
    print("   - main.py in the root directory")
    print("   - Backend modules in the 'backend' folder")
    print("   - HTML template in the 'templates' folder")
    print("   - JavaScript in the 'static/js' folder")
    print("   - CSS in the 'static/css' folder")
    print("\n2. Configure your Azure credentials in config.json")
    print("\n3. Install dependencies:")
    print("   Run: install_dependencies.bat")
    print("\n4. Run the application:")
    print("   Development: run_development.bat")
    print("   Build EXE: build_executable.bat")
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    main()