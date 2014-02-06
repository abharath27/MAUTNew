import paramiko
import os
import shlex
from Tkinter import *

def diskFull(ssh, threshold, listboxDisk, host):
     diskList=[]
     stdin,stdout,stderr = ssh.exec_command("df -h|awk '{print $1; print $4}'")
     lines = stdout.readlines()
     i=0
     flag = 0
     while i < len(lines):
          if '/dev/' in lines[i]:
               if lines[i+1].find('G') == -1:
                   if flag != 1:
                       flag = 1
                       listboxDisk.insert(END, host)
                       listboxDisk.insert(END, "")

                   diskList.append(lines[i][:-1] + " " + lines[i+1])
                   listboxDisk.insert(END,lines[i][:-1] + " " + lines[i+1] + "\n" + "\n")
                   listboxDisk.insert(END, "")
               else:
                   available = float(lines[i+1][:-2])

                   if available < threshold:
                       if flag != 1:
                           flag = 1
                           listboxDisk.insert(END,  host )
                           listboxDisk.insert(END, "")
                       diskList.append(lines[i][:-1] + " " + lines[i+1] + "\n" + "\n")
                       listboxDisk.insert(END,lines[i][:-1] + " " + lines[i+1] + "\n" + "\n")
                       listboxDisk.insert(END, "")

          i=i+1
     print diskList
     return diskList


#sshConnect = ssh.connect(host1,uname,passwd)
#if sshConnect =='':
    #print 'skipping'
#else:
    #print " logged into" + host1
#dskFullInfo = diskSpace.diskFull(sshConnect, 80)

