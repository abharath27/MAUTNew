import paramiko, os, string, pprint, socket, traceback, sys

def connect(host,uname,passwd):
    port= 22
    try:
        ssh=paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host,port,username=uname,password=passwd)
    except paramiko.AuthenticationException:
        print "We had an authentication exception! on "+host+'\n'
        ssh=''
    except socket.error, e:
        print "Comunication problem    -- Server: ", host 
        ssh=''
    return ssh

