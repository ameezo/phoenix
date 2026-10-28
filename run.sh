#!/bin/bash
# ==============================================================================
# PROJECT PHOENIX - Lab Server & Automatic Network Capture Startup Script
# ==============================================================================
# This script:
# 1. Sets up the Python virtual environment and dependencies.
# 2. Automatically launches tcpdump / tshark / wireshark in the background to record
#    all lab traffic into a .pcap file ready for digital forensic analysis.
# 3. Starts the Flask web server (hosting DocumentHelper / lab files & receiving uploads).
# 4. Gracefully stops the packet capture upon exit (Ctrl+C) and outputs the PCAP path.
# ==============================================================================

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# 1. Python Environment Setup
if [ ! -d ".venv" ]; then
    echo "[*] Creating virtual environment (.venv)..."
    python3 -m venv .venv
fi

echo "[*] Installing/verifying dependencies..."
./.venv/bin/pip install -q -r requirements.txt

# 2. Check if Port 5001 is already in use and free it if needed
EXISTING_PID=$(lsof -ti :5001 2>/dev/null || true)
if [ -n "$EXISTING_PID" ]; then
    echo "[*] Freeing port 5001 (stopping existing process PID: $EXISTING_PID)..."
    kill "$EXISTING_PID" 2>/dev/null || true
    sleep 0.8
fi

# 3. Network Capture Configuration
CAPTURES_DIR="$PROJECT_DIR/captures"
mkdir -p "$CAPTURES_DIR"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
PCAP_FILE="$CAPTURES_DIR/traffic_${TIMESTAMP}.pcap"
SYMLINK_FILE="$CAPTURES_DIR/phoenix_traffic.pcap"

# Detect capture interface
if [ -n "$CAPTURE_INTERFACE" ]; then
    IFACE="$CAPTURE_INTERFACE"
elif tcpdump -D 2>&1 | grep -q "[0-9]\.any"; then
    IFACE="any"
elif tcpdump -D 2>&1 | grep -E -q "[0-9]\.eth0"; then
    IFACE="eth0"
else
    # Auto-detect default routing interface (cross-platform macOS / Linux)
    IFACE=$(route get default 2>/dev/null | awk '/interface:/ {print $2}')
    [ -z "$IFACE" ] && IFACE=$(ip route show default 2>/dev/null | awk '/dev/ {print $5}')
    [ -z "$IFACE" ] && IFACE="any"
fi

# Filter: Port 5001 (Flask server), Port 80/8080 (HTTP), ICMP, or custom CAPTURE_FILTER
FILTER="${CAPTURE_FILTER:-tcp port 5001 or port 8080 or port 80 or icmp}"

echo "=========================================================="
echo "           PROJECT PHOENIX FORENSIC LAB SERVER            "
echo "=========================================================="
echo "[+] Capture Interface: $IFACE"
echo "[+] Capture Filter   : ${FILTER:-<all traffic>}"
echo "[+] Output PCAP      : $PCAP_FILE"
echo "=========================================================="

TCPDUMP_PID=""

cleanup() {
    echo ""
    echo "[*] Stopping Project Phoenix services..."
    if [ -n "$TCPDUMP_PID" ] && kill -0 "$TCPDUMP_PID" 2>/dev/null; then
        echo "[*] Terminating packet capture (PID $TCPDUMP_PID)..."
        kill -SIGINT "$TCPDUMP_PID" 2>/dev/null || kill "$TCPDUMP_PID" 2>/dev/null
        wait "$TCPDUMP_PID" 2>/dev/null || true
        
        # Create/update symlink to latest capture for easy investigator access
        rm -f "$SYMLINK_FILE"
        ln -sf "$PCAP_FILE" "$SYMLINK_FILE" 2>/dev/null || cp "$PCAP_FILE" "$SYMLINK_FILE" 2>/dev/null || true
        
        if [ -s "$PCAP_FILE" ]; then
            SIZE=$(ls -lh "$PCAP_FILE" | awk '{print $5}')
            echo "=========================================================="
            echo "✅ PCAP capture successfully saved: $PCAP_FILE ($SIZE)"
            echo "   Symlinked as: $SYMLINK_FILE"
            echo "   Ready to be analyzed in Wireshark!"
            echo "=========================================================="
        else
            echo "ℹ️  Packet capture file created at: $PCAP_FILE"
        fi
    fi
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# 4. Start Packet Capture (tcpdump or tshark)
if command -v tcpdump >/dev/null 2>&1; then
    # Attempt to start tcpdump
    if [ "$EUID" -ne 0 ] && command -v sudo >/dev/null 2>&1 && sudo -n true 2>/dev/null; then
        sudo tcpdump -i "$IFACE" -w "$PCAP_FILE" $FILTER -U -q >/dev/null 2>&1 &
        TCPDUMP_PID=$!
    else
        tcpdump -i "$IFACE" -w "$PCAP_FILE" $FILTER -U -q >/dev/null 2>&1 &
        TCPDUMP_PID=$!
    fi

    # Check if tcpdump started successfully or exited due to permission/interface error
    sleep 0.6
    if kill -0 "$TCPDUMP_PID" 2>/dev/null; then
        echo "[+] Background packet capture active (PID $TCPDUMP_PID)."
    else
        TCPDUMP_PID=""
        echo "⚠️  NOTE: tcpdump requires root privileges to capture packets."
        echo "   👉 Run with 'sudo ./run.sh' to record network traffic into PCAP automatically."
        echo "   (Continuing Flask server launch without automated PCAP)..."
    fi
elif command -v tshark >/dev/null 2>&1; then
    tshark -i "$IFACE" -w "$PCAP_FILE" -f "$FILTER" -q >/dev/null 2>&1 &
    TCPDUMP_PID=$!
    sleep 0.6
    if kill -0 "$TCPDUMP_PID" 2>/dev/null; then
        echo "[+] Background tshark capture active (PID $TCPDUMP_PID)."
    else
        TCPDUMP_PID=""
    fi
else
    echo "⚠️  Neither 'tcpdump' nor 'tshark' was found on this system."
    echo "   Install tcpdump via: sudo apt install tcpdump (Linux) or brew install wireshark (macOS)"
fi

# Optional: Launch Wireshark GUI if requested via flag or environment variable
if [ "$1" = "--wireshark" ] || [ "$OPEN_WIRESHARK" = "1" ]; then
    if command -v wireshark >/dev/null 2>&1 && [ -n "$DISPLAY" -o "$(uname)" = "Darwin" ]; then
        echo "[+] Launching Wireshark GUI on interface $IFACE..."
        wireshark -k -i "$IFACE" &
    fi
fi

# 5. Start Project Phoenix Flask App
echo "[*] Starting Flask web server on port 5001..."
echo "    Access URLs:"
echo "      - Web Portal:       http://0.0.0.0:5001/"
echo "      - Upload Directory: http://0.0.0.0:5001/uploaded"
echo "----------------------------------------------------------"
echo "Press Ctrl+C to stop the server and finalize the PCAP recording."
echo "----------------------------------------------------------"

./.venv/bin/python3 app.py
