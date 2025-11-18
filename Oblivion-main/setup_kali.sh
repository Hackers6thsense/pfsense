#!/bin/bash

set -e

echo "[*] Updating package lists..."
sudo apt update

echo "[*] Installing Metasploit Framework, nmap, and python3-pip..."
sudo apt install -y metasploit-framework nmap python3-pip

echo "[*] Upgrading pip..."
python3 -m pip install --upgrade pip

echo "[*] Installing Python dependencies from requirements.txt..."
pip3 install -r requirements.txt

echo "[*] Starting msfrpcd Metasploit RPC daemon..."
MSF_RPC_USER=msf
MSF_RPC_PASS=msf
MSF_RPC_HOST=127.0.0.1
MSF_RPC_PORT=55553

# Start msfrpcd in background (no SSL, default creds)
msfrpcd -U $MSF_RPC_USER -P $MSF_RPC_PASS -a $MSF_RPC_HOST -p $MSF_RPC_PORT -n -S >/dev/null 2>&1 &
MSF_PID=$!

echo "[*] Waiting for msfrpcd to listen on port $MSF_RPC_PORT (up to 10 seconds)..."
for i in {1..10}; do
    if lsof -iTCP:$MSF_RPC_PORT -sTCP:LISTEN >/dev/null 2>&1 || nc -z $MSF_RPC_HOST $MSF_RPC_PORT; then
        echo "[+] msfrpcd is running."
        break
    fi
    sleep 1
done

if ! lsof -iTCP:$MSF_RPC_PORT -sTCP:LISTEN >/dev/null 2>&1 && ! nc -z $MSF_RPC_HOST $MSF_RPC_PORT; then
    echo "[!] Warning: msfrpcd did not start successfully or port $MSF_RPC_PORT is not listening."
fi

echo
echo "You may want to add these lines to your ~/.bashrc for convenience:"
echo "  export MSF_RPC_HOST=$MSF_RPC_HOST"
echo "  export MSF_RPC_PORT=$MSF_RPC_PORT"
echo "  export MSF_RPC_USER=$MSF_RPC_USER"
echo "  export MSF_RPC_PASS=$MSF_RPC_PASS"
echo
echo "[*] Setup complete. You can now run the Oblivion tool."