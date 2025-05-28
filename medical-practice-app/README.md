# Medical Practice Management Desktop Application

Version: 2.0.0

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
