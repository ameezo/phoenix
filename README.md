# Project Phoenix: Digital Forensics Lab

![alt text](<static/Screenshot 2026-11-03 at 11.39.40 PM.png>)
**Project Phoenix** is a hands-on Digital Forensics & Incident Response (DFIR) investigation lab. 

In this lab, the instructor simulates a real-world security incident, captures the evidence, and provides students with two forensic artifacts:
1. 💽 **`zuj_EV009.E01`**: A forensic disk image of the victim's data partition.
2. 🌐 **`traffic.pcap`**: A network packet capture of the workstation's communication.

Students work as forensic analysts using **FTK Imager** and **Wireshark** to reconstruct what happened, carve out stolen data from network traffic, and recover deleted files from the disk image.

---

## 📖 The Incident Scenario

> **Incident Brief:**  
> An employee downloaded a utility called `DocumentHelper` from the internal network. After launching it, a PDF document opened on the screen. Shortly afterward, the employee noticed that sensitive company files stored on their data volume (`S:\`) had completely disappeared.  
>
> **Your Mission:**  
> Investigate the provided disk image and network capture to answer:
> 1. Was data stolen (exfiltrated) over the network? Can you recover the stolen files from the traffic?
> 2. Which files were deleted from the disk? Can you recover them from the forensic disk image?

---

## 🧰 Required Tools for Students

Students only need two industry-standard tools installed on their machine:

| Tool | Purpose | Download Link |
| :--- | :--- | :--- |
| **Exterro FTK Imager** | Opening the disk image (`.E01`), exploring the file system, and recovering deleted files | [Download FTK Imager](https://www.exterro.com/ftk-imager) |
| **Wireshark** | Opening the packet capture (`.pcap`), filtering traffic, and carving exfiltrated files | [Download Wireshark](https://www.wireshark.org/) |

---

## 📁 Evidence Files Provided to Students

Before starting, ensure you have received the following evidence package :
* `zuj_EV009.E01`
* `traffic.pcap`

Download the files via
https://drive.google.com/drive/folders/1ql06dldu3F7uVKpkiOuJTk6Y2P69y_LT?usp=drive_link

---

# 🕵️‍♂️ PART 1: Disk Investigation with FTK Imager

Follow these steps to load and analyze `zuj_EV009.E01`.

---

### Step 1: Open the Evidence Image in FTK Imager
1. Launch **FTK Imager** (run as Administrator if prompted).
2. Click on **File** in the top menu and select **Add Evidence Item...** (or press the **Add Evidence** toolbar icon).
![alt text](<screenshots/Screenshot 2026-11-02 at 8.20.16 AM.png>)
3. In the dialog that appears, select **Image File** and click **Next >**.
4. Click **Browse...**, locate the **`zuj_EV009.E01`** file on your computer, and click **Finish**.
![alt text](<screenshots/Screenshot 2026-11-02 at 8.20.43 AM.png>)

---

### Step 2: Verify Forensic Image Integrity (Hashes)
Forensic soundness requires verifying that the evidence has not been altered or corrupted:
1. In the **Evidence Tree** pane (left side), right-click on the top item **`zuj_EV009.E01`**.
![alt text](<screenshots/Screenshot 2026-11-02 at 8.35.38 AM.png>)
2. Select **Verify Drive/Image...**.
3. FTK Imager will compute the cryptographic hashes (MD5 and SHA-1) of the raw disk sectors.
4. Verify that the **Computed Hash** matches the **Stored Hash** with a green **Match** status.
![alt text](<screenshots/Screenshot 2026-11-02 at 8.36.32 AM.png>)

---

### Step 3: Explore the Evidence Tree
1. In the **Evidence Tree**, expand:
   `zuj_EV009.E01` $\rightarrow$ `New Volume [NTFS]` $\rightarrow$ `[root]`
2. Notice the key NTFS forensic items visible in the tree:
   * **`[root]`**: The base directory of the partition.
   * **`$MFT`**: The Master File Table — the central database of all file metadata on the NTFS drive.
   * **`$Extend\$UsnJrnl`**: The update sequence number change journal tracking all file additions, renames, and deletions.
   * **`Sysmon` Folder**: A protected system folder created when Sysmon file delete archiving is active.
   * **`[unallocated space]`**: Clusters on disk not currently assigned to active files (where wiped file fragments remain).

---

### Step 4: Locate & Recover the Deleted Files from the `Sysmon` Folder
the sysmon automatically archives a copy of every deleted file into a hidden `\Sysmon\` directory, renaming each file to its unique **SHA-256 hash**.

1. Click on the **`Sysmon`** folder under `[root]`.
![alt text](<screenshots/Screenshot 2026-11-02 at 8.42.27 AM.png>)
2. Look at the **File List** pane in the top-right. You will see one or more files named by there hashs SHA-256 string.
3. Click on the file:
   * The **Viewer Pane** at the bottom will display the hex dump and text preview of the file contents.
4. **Recover the file:**
   ![alt text](<screenshots/Screenshot 2026-11-02 at 8.44.59 AM.png>)
   * Right-click the file in the **File List** pane.
   * Select **Export Files...**.
   * Choose a folder on your computer (e.g. `Desktop\Recovered_Evidence`) and click **OK**.
5. You have successfully recovered the deleted file!

also , i can export the SAM , SECURITY , SOFTWARE , SYSTEM, NTuser.dat for later investigations located in :
```
C:\windows\System32\config
C:\Users\user\
```
---

# 🌐 PART 2: Network Investigation with Wireshark

Follow these steps to analyze `traffic.pcap` and reconstruct the exfiltration.

---

### Step 1: Open the Packet Capture
1. Open **Wireshark**.
2. Click **File** $\rightarrow$ **Open...** and select **`traffic.pcap`**. (double click on the pcap file)
3. You will see all recorded communication between the victim workstation and the lab server.

![alt text](<screenshots/Screenshot 2026-11-02 at 10.12.36 AM.png>)
---

### Step 2: Filter and Identify HTTP Traffic
In the display filter bar at the top, apply the following filters to isolate the attacker's activity:

1. **Find the Initial Download:**
   ```wireshark
   http
   http.request.method == "GET"
   ```
   * Look for requests fetching documents or scripts (e.g., `GET /download/DF-Lab1.pdf` or script files).
   * Note the server IP address and request URI.
   ![alt text](<screenshots/Screenshot 2026-11-02 at 10.14.59 AM.png>)
2. **Find the Exfiltration Request:**
   ```wireshark
   http.request.method == "POST"
   ```
   * You will see an HTTP POST request transmitting data to an upload endpoint (e.g., `POST /uploaded/phoenix_staging.zip`).
   * This proves that the data was not merely deleted locally — it was exfiltrated to an external receiver!
   ![alt text](<screenshots/Screenshot 2026-11-02 at 10.19.32 AM.png>)

---

### Step 3: Follow the TCP Stream
To read the full conversation:
1. Right-click on the `POST` packet.
2. Select **Follow** $\rightarrow$ **TCP Stream**.
3. A window opens showing the entire request and response:
   * The HTTP headers (`Host`, `User-Agent`, `Content-Type`).
   * The magic bytes of the payload: Notice the header starts with **`PK`** (indicating a standard `.zip` archive).
4. Close the stream window when finished inspecting.

<!-- SCREENSHOT PLACEHOLDER: Add your screenshot of Follow TCP Stream -->
> 📷 **Screenshot Placeholder: Follow TCP Stream**  
> *(Save your screenshot as `screenshots/05_wireshark_tcp_stream.png`)*  
> ![Follow TCP Stream](screenshots/05_wireshark_tcp_stream.png)

---

### Step 4: Carve and Extract the Stolen ZIP File
Wireshark allows you to extract files transferred over HTTP without manual hex carving:
1. Click **File** in the top menu.
2. Navigate to **Export Objects** $\rightarrow$ **HTTP...**.
3. In the list of transferred objects, find **`phoenix_staging.zip`** (or the object associated with the POST upload).
4. Select it and click **Save**.
5. Save the archive to your analysis folder.
6. Unzip the saved `.zip` archive. You will see the exact company files that were stolen from volume `G:\`!

<!-- SCREENSHOT PLACEHOLDER: Add your screenshot of Wireshark Export Objects -->
> 📷 **Screenshot Placeholder: Export HTTP Objects**  
> *(Save your screenshot as `screenshots/06_wireshark_export_objects.png`)*  
> ![Wireshark Export Objects](screenshots/06_wireshark_export_objects.png)

---

# 📋 Student Investigation Worksheet & CTF Questions

Answer the following questions based on your findings in **FTK Imager** and **Wireshark**:

| # | Question | Tool to Use | Your Answer |
| :-: | :--- | :--- | :--- |
| **1** | What is the SHA-1 or MD5 hash of the `zuj_EV009.E01` disk image? | FTK Imager (`Verify Drive/Image`) | |
| **2** | What is the filename (SHA-256 hash) of the deleted file recovered from `\Sysmon\`? | FTK Imager (`Sysmon` folder) | |
| **3** | What are the contents of the recovered deleted file? | FTK Imager (`Export Files`) | |
| **4** | What is the destination IP address and port that received the stolen data? | Wireshark (`POST` filter) | |
| **5** | What was the HTTP URL path used to exfiltrate the stolen archive? | Wireshark (`Follow TCP Stream`) | |
| **6** | Extract the exfiltrated ZIP file using Wireshark. What files were packaged inside it? | Wireshark (`Export Objects > HTTP`) | |
| **7** | Based on your findings, was the employee a victim of a malicious script, or did they deliberately upload the files? Explain your reasoning. | Forensic Analysis | |

---

# 🛠️ Instructor Guide: Preparing the Lab & Generating Evidence

*(For Instructor use only — do this before the student session)*

### 1. Run the Server & Capture Traffic
On your Linux server / host machine:
```bash
# Clone the repository
git clone https://github.com/ameezo/phoenix.git
cd phoenix

# Start the server with automated packet capture
sudo ./run.sh
```
`run.sh` will start `tcpdump` automatically and save network packets to `captures/traffic_<timestamp>.pcap` (symlinked as `captures/traffic.pcap`).

### 2. Trigger the Incident on the Windows VM
1. On the Windows workstation with volume `G:\` (containing sensitive files), open the browser and navigate to `http://<SERVER_IP>:5001/`.
2. Download and run `project_phoenix/DocumentHelper.bat` (or `code.ps1`).
3. The script will:
   * Open the decoy PDF (`DF-Lab1.pdf`).
   * Compress files from `G:\` into `phoenix_staging.zip`.
   * Upload `phoenix_staging.zip` to the server via HTTP POST.
   * Delete files from `G:\` (Sysmon automatically archives them into `G:\Sysmon\`).

### 3. Stop the Capture
Press **`Ctrl + C`** on the server running `run.sh`. The final `.pcap` will be saved in `captures/traffic.pcap`.

### 4. Image Volume `G:\` with FTK Imager
1. Open FTK Imager on the Windows VM as Administrator.
2. Click **File** $\rightarrow$ **Create Disk Image...** $\rightarrow$ choose **Logical Drive** $\rightarrow$ select `G:\`.
3. Choose format **E01**, name the file `zuj_EV009.E01`, and enable **Verify images after they are created**.

### 5. Take Screenshots for the Lab Manual
As you execute the steps above, take screenshots and save them into the `screenshots/` directory using these file names:
* `screenshots/01_ftk_add_evidence.png`
* `screenshots/02_ftk_verify_hash.png`
* `screenshots/ftk_sysmon_evidence.png` *(already saved)*
* `screenshots/03_wireshark_open.png`
* `screenshots/04_wireshark_http_post.png`
* `screenshots/05_wireshark_tcp_stream.png`
* `screenshots/06_wireshark_export_objects.png`

### 6. Distribute Evidence to Students
Distribute `zuj_EV009.E01` and `traffic.pcap` to students along with this `README.md` guide.
