# phoenix

the lab scenario : "Student / employee downloaded a file `DocumentHelper.zip` the does the work instead of him , after a while noticed that the project files were gone , so what is happening here ?"

## lab objectives :
- [ ] investigate the modifications processes occurs on the VM
- [ ] understand `DocumentHelper.zip` behaviour
- [ ] Exfiltration Validation and recover them
- [ ] collect evidences (artifacts)
- [ ] differentiate between the "Account Attribution" vs. "Person Attribution"
- [ ] understand the networking between Workstation and Server


## Requirements
- [ ] Windows VM
- [ ] Linux VM
- [ ] basic understanding of technology

## tools :
1. Sysmon is now actively intercepting every single file deletion across the system and archiving a forensic copy of the deleted files
2. FTK Imager : Acquire the training data volume and inspect/export relevant evidence
3. Wireshark : monitor the network traffic


## walkthrough
1. install the repo on the server and run the script `bash run.sh`
2. browse and navigate to the server page to complete the tasks
3. start investigation using the listed tools
4. submit the result and solve the CTF questions




## solution

step-by-step solution :

1. install the repo
```bash
git clone <URL>
```
2. run the script
```bash
bash run.sh
```
3. navigate to the Workstation Windows PC
4. install the required documents

