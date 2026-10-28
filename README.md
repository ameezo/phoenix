# Project Phoenix - Digital Forensics & Incident Response (DFIR) Lab

Project Phoenix is a hands-on digital forensics lab designed to simulate a realistic insider threat / trojanized utility attack. An employee downloads a utility (`DocumentHelper`), executes it, and shortly afterward discovers that sensitive project files on their data volume (`G:\`) have vanished.

Students step into the shoes of a DFIR investigator to correlate evidence across **three foundational forensic pillars**:
1. **Host Event Logs (`.evtx`)** via **Sysmon & Event Viewer / EvtxECmd**
2. **Disk & File System Artifacts** via **FTK Imager / MFTECmd**
3. **Network Packet Captures (`.pcap`)** via **tcpdump & Wireshark**

---

## 🏗️ Lab Architecture & Scenario

### The Story
* **09:50 (Delivery):** Employee Sarah downloads `DocumentHelper.zip` (or `code.bat`) from the lab server (`http://192.168.56.20:5001`).
* **09:53 (Execution):** The script executes under Sarah's user session. A decoy document (`DF-Lab1.pdf`) opens to deceive the user.
* **09:55 (Collection/Staging):** In the background, PowerShell bundles sensitive files from `G:\` into a staging archive (`phoenix_staging.zip`).
* **09:57 (Exfiltration):** The staging archive is exfiltrated via HTTP POST to `http://192.168.56.20:5001/uploaded/phoenix_staging.zip`.
* **10:00 (Anti-Forensics / Destruction):** The script wipes the files from `G:\` to conceal activity and disrupt operations.

```
┌─────────────────────────────────────────┐               ┌─────────────────────────────────────────┐
│     Windows Victim Machine (WS-FIN-07)   │               │        Lab Receiver Server (Linux)      │
│     IP: 192.168.56.10                   │               │        IP: 192.168.56.20                │
│                                         │               │                                         │
│   • C:\ (OS Drive - Sysmon Logs)        │   HTTP GET    │   • Flask Web Server (Port 5001)        │
│   • G:\ (1 GB NTFS Data Volume)         │ ────────────► │     Hosts DocumentHelper & decoy PDFs   │
│                                         │               │                                         │
│   Execution:                            │   HTTP POST   │   • Upload Directory:                   │
│   PowerShell archives G:\ to .zip       │ ────────────► │     project_phoenix/uploaded/           │
│   Wipes G:\ (Archived by Sysmon EID 23) │ (Exfiltrate)  │                                         │
│                                         │               │   • Automated tcpdump / Wireshark:      │
│                                         │               │     Captures traffic to captures/*.pcap │
└─────────────────────────────────────────┘               └─────────────────────────────────────────┘
```

---

## 🛠️ Tools Required & System Prerequisites

### 1. Lab Server (Linux VM / Host)
| Tool | Purpose | Installation / Command |
| :--- | :--- | :--- |
| **Python 3.10+** | Runs the Flask server serving downloads & receiving uploads | `sudo apt install python3 python3-venv python3-pip` |
| **Flask & Werkzeug** | Web framework handling dynamic download rewriting & raw uploads | Installed via `pip install -r requirements.txt` in `run.sh` |
| **tcpdump** | Automatic network traffic recorder running in background | `sudo apt install tcpdump` |
| **Wireshark / TShark** | *(Optional on Linux, recommended for analysis)* Packet inspector | `sudo apt install tshark wireshark` |

### 2. Victim Workstation & Forensic Analysis (Windows VM / Host)
| Tool | Purpose | Download / Setup |
| :--- | :--- | :--- |
| **Microsoft Sysmon** | Advanced Windows event logging (Process Create, Network, File Delete Archive) | [Sysinternals Sysmon](https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon) |
| **Exterro / AccessData FTK Imager** | Physical/logical drive imaging (`.E01`), `$MFT` extraction, file recovery from `\Sysmon\` | [FTK Imager Free Download](https://www.exterro.com/ftk-imager) |
| **Wireshark** | Packet capture analysis, HTTP stream reconstruction, and file object carving | [Wireshark Official](https://www.wireshark.org/) |
| **Eric Zimmerman Tools** | High-speed command-line forensic parsers (`MFTECmd.exe`, `EvtxECmd.exe`) | [Eric Zimmerman's Tools](https://ericzimmerman.github.io/#!index.html) |
| **Timeline Explorer** | Forensic spreadsheet viewer for parsed CSVs (preserves millisecond timestamps) | Included in Eric Zimmerman's tool suite |
| **KAPE** | *(Optional)* Kroll Artifact Parser and Extractor for rapid log triage from `C:\` | [KAPE Official](https://www.kroll.com/en/services/cyber-risk/incident-response-litigation-support/kroll-artifact-parser-extractor-kape) |

---

## 🚀 Quick Start Guide

### Step 1: Start the Lab Server & Automatic Packet Capture
On your Linux server (or macOS testing host):

```bash
# Clone the repository
git clone <REPO_URL>
cd phoenix

# Run the startup script (root/sudo recommended to enable automated tcpdump packet capture)
sudo ./run.sh
```

When started, `run.sh`:
1. Activates or creates the Python virtual environment (`.venv`).
2. Automatically identifies the active network interface and starts **`tcpdump`** in the background, writing to `captures/traffic_<timestamp>.pcap` (and symlinked as `captures/phoenix_traffic.pcap`).
3. Starts the Flask server on `http://0.0.0.0:5001`.
4. When you terminate the server with **`Ctrl + C`**, `run.sh` cleanly stops `tcpdump`, flushes packets, and prints the location of your ready-to-analyze `.pcap` file!

### Step 2: Configure the Windows Victim Machine
1. Create a secondary **1 GB NTFS volume** mounted as `G:\` (or `D:\`).
2. Add a few dummy sensitive files to `G:\` (e.g., `secret_budget.xlsx`, `passwords.txt`, `project_falcon.docx`).
3. Install **Sysmon** with File Deletion archiving enabled:
   ```cmd
   sysmon.exe -i -n -accepteula
   ```
   *(Ensure your configuration includes Event ID 23 `FileDelete` with an archive directory, e.g. `Sysmon`)*.

### Step 3: Trigger the Attack
1. On the Windows VM, navigate to `http://<SERVER_IP>:5001/`.
2. Download and execute `code.ps1` (or `malware3.ps1` / `DocumentHelper`).
3. Observe the decoy file opening, followed by files on `G:\` being archived, exfiltrated, and deleted.
4. Stop `run.sh` on the server (`Ctrl + C`) to finalize the `.pcap` recording.

---

## 🔍 Detailed Forensic Tool Usage Guide

### 1. Windows Event Viewer & Sysmon
Sysmon provides high-fidelity host logs that standard Windows logs miss.

* **Where to find logs:**
  `Event Viewer` $\rightarrow$ `Applications and Services Logs` $\rightarrow$ `Microsoft` $\rightarrow$ `Windows` $\rightarrow$ `Sysmon` $\rightarrow$ `Operational`.
* **Key Event IDs to filter:**
  * **Event ID 1 (Process Create):** Shows when `powershell.exe` was invoked, who ran it (`User`), parent process (`ParentImage`), and the full payload command (`CommandLine`).
  * **Event ID 3 (Network Connection):** Records when PowerShell initiated an outbound connection to `http://<SERVER_IP>:5001`. Contains `DestinationIp`, `DestinationPort`, and process ID.
  * **Event ID 11 (File Create):** Shows the creation of temporary staging archives like `phoenix_staging.zip`.
  * **Event ID 23 / 26 (File Delete):** Logs whenever a file is deleted. When archive mode is enabled (Event ID 23), Sysmon saves a forensic copy of the deleted file into `G:\Sysmon\` renamed to its SHA256 hash!
* **Pro Tip with EvtxECmd:**
  Instead of clicking through Event Viewer, export `Microsoft-Windows-Sysmon%4Operational.evtx` and run:
  ```powershell
  .\EvtxECmd.exe -f Sysmon_Operational.evtx --csv . --csvf sysmon_parsed.csv
  ```
  Open `sysmon_parsed.csv` in **Timeline Explorer** to filter by `EventId` or search for `.zip`.

---

### 2. FTK Imager
FTK Imager allows you to preserve and analyze physical or logical disks without altering evidence.

* **Creating a Forensic Image of the Data Volume (`G:`):**
  1. Open FTK Imager as Administrator.
  2. Click **File $\rightarrow$ Create Disk Image...**
  3. Select **Logical Drive** $\rightarrow$ choose `G:\`.
  4. Choose Image Destination: **E01 (Expert Witness Format)**.
  5. Fill in Case Information, set compression (default 6), and set destination (e.g., `C:\Forensics\Drive_G.E01`).
  6. Check **Verify images after they are created** to generate cryptographic verification hashes (MD5 & SHA1).
* **Why `.E01` over `.raw`?**
  * `.raw` (`dd`) produces an uncompressed 1:1 image (a 1 GB drive is always 1 GB on disk).
  * `.E01` compresses zero-blocks (shrinks a 1 GB nearly empty drive to ~15 MB) and embeds case metadata and integrity checksums directly into the file container.
* **Exploring the Evidence Tree:**
  * Click **File $\rightarrow$ Add Evidence Item...** $\rightarrow$ **Image File** $\rightarrow$ select `Drive_G.E01`.
  * **`[root]`:** Contains top-level files and NTFS metadata (`$MFT`, `$LogFile`).
  * **`$Extend\$UsnJrnl`:** The NTFS change journal tracking every file creation, renaming, and deletion.
  * **`Sysmon` Folder:** When Sysmon Event ID 23 intercepts deletions, it copies the deleted files into `G:\Sysmon\` named by their SHA256 hash (e.g., `D74B4A8B83D5F64CB512...txt`).
* **Recovering the Deleted File:**
  1. Click on the **`Sysmon`** folder under `[root]`.
  2. In the right pane, locate the hash-named file.
  3. Select the file to view its ASCII / Unicode contents in the hex viewer.
  4. Right-click the file $\rightarrow$ **Export Files...** to save the recovered document.
* **Exporting `$MFT` for Parsing:**
  1. Click `[root]`.
  2. Right-click **`$MFT`** $\rightarrow$ **Export Files...** $\rightarrow$ save to your analysis directory.
  3. Parse it with Eric Zimmerman's tool:
     ```powershell
     .\MFTECmd.exe -f "$MFT" --csv . --csvf mft_parsed.csv
     ```

---

### 3. Wireshark & Network Traffic Analysis
The `.pcap` generated by `run.sh` captures the exact bytes transferred over the network.

* **Opening the Capture:**
  Open `captures/phoenix_traffic.pcap` in Wireshark.
* **Essential Display Filters:**
  * `http`: Displays all HTTP web traffic.
  * `http.request.method == "GET"`: Finds the initial download of the decoy/script.
  * `http.request.method == "POST"`: Isolates the exfiltration request uploading `phoenix_staging.zip`.
  * `tcp.port == 5001`: Filters all traffic destined for the Project Phoenix server.
* **Reconstructing the Conversation:**
  * Right-click any HTTP packet $\rightarrow$ **Follow $\rightarrow$ TCP Stream**.
  * View the full HTTP headers (`POST /uploaded/phoenix_staging.zip HTTP/1.1`) and the raw binary transmission.
* **Carving the Exfiltrated Stolen File from the Network:**
  You don't need to manually cut hex bytes—Wireshark has built-in object carving:
  1. In Wireshark, click **File $\rightarrow$ Export Objects $\rightarrow$ HTTP...**
  2. In the list, locate `phoenix_staging.zip` (or the POST destination object).
  3. Click **Save** to export the archive.
  4. Unzip the carved file to inspect the exact company files that were exfiltrated!

---

## ⚖️ Core Forensic Concept: Account Attribution vs. Person Attribution

One of the most critical lessons in DFIR:
* **Account Attribution:** Proving *which computer account* performed an action.
  * *Example:* Sysmon Event ID 1 proves that `WS-FIN-07\emp_sarah` executed PowerShell.
* **Person Attribution ("Fingers on Keyboard"):** Proving *which physical human being* was present and knowingly committed the act.
  * *Did Sarah walk away from an unlocked workstation to grab coffee?*
  * *Was Sarah tricked into running a trojanized utility believing it was legitimate?*
  * *Were her credentials compromised over the network?*

**Forensically Sound Conclusion Example:**
> *"Forensic evidence confirms that local user account `WS-FIN-07\emp_sarah` executed `code.ps1`, resulting in the archiving, exfiltration, and deletion of project documents on volume `G:`. However, establishing malicious human intent versus social-engineering deception requires corroborating evidence such as badge logs, physical CCTV, or interview records."*

---

## 🎯 Investigation Checklist & CTF Questions

| # | Question | Evidence Source | Investigation Method |
| :-: | :--- | :--- | :--- |
| **1** | What was the URL and IP address from which the initial script was downloaded? | Network / Sysmon | Wireshark GET filter or Sysmon Event ID 3 |
| **2** | What exact command line was executed to launch the attack? | Host Logs | Sysmon Event ID 1 (`CommandLine`) |
| **3** | What was the name of the staging archive created on disk? | Disk / Sysmon | Sysmon Event ID 11 or FTK Imager `$MFT` |
| **4** | What network endpoint received the exfiltrated staging archive? | Network | Wireshark POST request (`/uploaded/phoenix_staging.zip`) |
| **5** | Can you extract and inspect the contents of the exfiltrated ZIP from the packet capture? | Network | Wireshark `File > Export Objects > HTTP` |
| **6** | Which files were deleted from volume `G:\`? | Disk / Host Logs | Sysmon Event ID 23/26 or MFTECmd (`InUse = False`) |
| **7** | Recover the deleted file from the `\Sysmon` directory in FTK Imager. What is its SHA256 hash? | Disk Image | FTK Imager `\Sysmon` folder hash filename |
| **8** | Does the evidence prove that the employee acted with malicious intent? Justify your answer. | Analysis | Account vs. Person Attribution analysis |
