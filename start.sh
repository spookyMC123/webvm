#!/bin/bash

# Clear terminal
clear

echo -e "\e[1;34m"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║   ███╗   ██╗███████╗██╗  ██╗ ██████╗ ██╗  ██╗ ██████╗ ███████╗████████╗"
echo "║   ████╗  ██║██╔════╝╚██╗██╔╝██╔═══██╗██║  ██║██╔═══██╗██╔════╝╚══██╔══╝"
echo "║   ██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████║██║   ██║███████╗   ██║   "
echo "║   ██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║██╔══██║██║   ██║╚════██║   ██║   "
echo "║   ██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝██║  ██║╚██████╔╝███████║   ██║   "
echo "║   ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝   ╚═╝   "
echo "║                                                               ║"
echo "║                    Nexo-VM-Panel                              ║"
echo "║              Welcome to NexoHost! Power Your Future!          ║"
echo "║                                                               ║"
echo "║   Starting server...                                          ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "\e[0m"

# Check if Python is installed
if ! command -v python3 &> /dev/null
then
    echo -e "\e[1;31m[ERROR] Python3 is not installed or not in PATH\e[0m"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null
then
    echo -e "\e[1;33m[WARNING] pip3 is not installed. Attempting to run without dependency check...\e[0m"
else
    # Check if dependencies are installed
    echo -e "\e[1;36m[INFO] Checking dependencies...\e[0m"
    if ! pip3 show Flask &> /dev/null
    then
        echo -e "\e[1;36m[INFO] Installing dependencies...\e[0m"
        pip3 install -r requirements.txt
    fi
fi

# Start the application
echo -e "\e[1;32m[INFO] Starting Nexo-VM-Panel...\e[0m"
echo ""
python3 nexovm.py
