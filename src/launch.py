import ssh, ping, threading, os

def func(handler, count):
    print 'Command:' + "python eval" + str(count) +".py config" + str(count) + " >" + str(count) + ".txt"
    stdin, stdout, stderr = handler.exec_command("cd MAUTNew/src;python eval" + str(count) +".py config" + str(count) + " >" + str(count) + ".txt")
    if stderr.read() != '':
        print 'stderr from', count, ':', stderr.read()
    #print 'exit status:', handler.recv_exit_status()
    print 'Process', count, 'terminated?'

uname='abharath'
passwd='password27'
networkPart='10.6.15'
startHost='140'
endHost='170'
upList=[]
downList=[]
sshHandlers = []
threads = []
count = 1
flag = 0

#os.system("sh generateEvalFiles.sh")

for i in range(int(startHost), int(endHost)):
    host = networkPart + '.' + str(i)
    c = ping.verbose_ping(host)
    if c > 0:
        upList.append(host)
    else:
        downList.append(host)

if len(upList) < 9:
    print 'Not enough hosts alive. Increase the range'
    exit()
for host1 in upList:
    sshConnect = ssh.connect(host1,uname,passwd)
    #sshConnect = sshConnect.get_transport()
    if sshConnect =='':
        print 'skipping', host1
    else:
        sshHandlers.append(sshConnect)
        print "logged into" , host1
    if len(sshHandlers) == 9:
        break

for handler in sshHandlers:
    #Modification to be done: Run all the commands in parallel
    thread = threading.Thread(target = func, args = (handler,count))
    threads.append(thread)
    thread.start()
    print 'Command executed, count = ', count
    count += 1

[t.join() for t in threads]