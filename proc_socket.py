#!/usr/bin/python
#
###
#
import struct, socket
import errno
import os
import re
import array

#Index of Network sockets
sl,local_address,rem_address,st, tx_rx_queue, tr_tm_when, retrnsmt, uid, timeout, inode, ref, pointer, drops = range(13)
#Index of Unix sockets 
Num,RefCount,Protocol,Flags,Type, u_St, u_Inode = range(7)
#Status of the socket connection
#TCP_ESTABLISHED,TCP_SYN_SENT,TCP_SYN_RECV,TCP_FIN_WAIT1,TCP_FIN_WAIT2,TCP_TIME_WAIT,TCP_CLOSE,TCP_CLOSE_WAIT,TCP_LAST_ACK,TCP_LISTEN,TCP_CLOSING,TCP_MAX_STATES
#Both for TCP anc UDP
Socket_states =[
        'TCP_ESTABLISHED',
        'TCP_SYN_SENT',
        'TCP_SYN_RECV',
        'TCP_FIN_WAIT1',
        'TCP_FIN_WAIT2',
        'TCP_TIME_WAIT',
        'TCP_CLOSE',
        'TCP_CLOSE_WAIT',
        'TCP_LAST_ACK',
        'TCP_LISTEN',
        'TCP_CLOSING',    #/* Now a valid state */

        'TCP_MAX_STATES'  #/* Leave at the end! */
]
debug = 0

hex2ip = lambda h: '.'.join([str(h >> (i << 3) & 0xFF) for i in range(0, 4)])


class ProcSockets(object):
  """
  Module for retrieving opened sockets for a pcocess.
  """
  def __init__(self):
    self.name = "ProcSockets"
    self.opened_sockets_by_process = {}
    #
    self.print_socket = {'tcp' :self.print_tcp,
                         'tcp6':self.print_tcp6,
                         'udp' :self.print_udp,
                         'udp6':self.print_udp6,
                         'unix':self.print_unix,
    }
    # Get all sockets on the host
    self.Find_System_Sockets()


  def Find_System_Sockets(self):
    # TCP
    self.sk_tcp = self.Net_socket('tcp')
    self.sk_tcp6 = self.Net_socket('tcp6')
    # UDP
    self.sk_udp = self.Net_socket('udp')
    self.sk_udp6 = self.Net_socket('udp6')
    #Unix
    self.sk_unix = self.Net_socket('unix')
    # 
    if(debug > 0):
       self.print_socket['tcp'](-1)
       self.print_socket['udp'](-1)

  def print_tcp(self,inum):
    print "TCP sockets:"
    print "   Inode   ", "           Local:Port     ","        Remote:Port        "," State "
    for link in self.sk_tcp:
       if(inum < 0 or inum == link[inode]):
          (laddr, lport)=link[local_address].split(":")
          (raddr, rport)=link[rem_address].split(":")
          print "%10s"%link[inode],"%18s:%7d"%(hex2ip(int(laddr,16)),int(lport,16))," %18s:%7d"%(hex2ip(int(raddr,16)), int(rport,16)),"%6s"%Socket_states[int(link[st],16)]

  def print_tcp6(self,inum):
    pass

  def print_udp(self,inum):
    print "UDP sockets:"
    print "   Inode   ", "           Local:Port     ","        Remote:Port        "," State "
    for link in self.sk_udp:
       if(inum < 0 or inum == link[inode]):
          (laddr, lport)=link[local_address].split(":")
          (raddr, rport)=link[rem_address].split(":")
          print "%10s"%link[inode],"%18s:%7d"%(hex2ip(int(laddr,16)),int(lport,16))," %18s:%7d"%(hex2ip(int(raddr,16)), int(rport,16)),"%6s"%Socket_states[int(link[st],16)]


  def print_udp6(self,inum):
    pass

  def print_unix(self):
    pass

  def Net_socket(self,protocol):
      # Find all open sockets,TCP(6), UDP(6), and UNIX, opened on the host
      var = []
      firstline=1
      try:
        for line in open('/proc/net/'+protocol):
            if(firstline == 1):
               firstline=0  #ignore the first line of the file.
            else:
               vl = line.split()
               var.append(vl)
      except IOError:
        var = [] #return empty list when error
      return var

  #Find the sockets opened by the process
  def Find_Open_Socket(self,process):
      # Find the opened sockets of a process
      opened_fd = [file for file in os.listdir('/proc/%d/fd' % int(process))]
      self.opened_sockets_by_process[str(process)]=[]
      for linkfile in opened_fd:
         path = '/proc/%d/fd' % int(process)
         result = os.readlink(path+'/'+linkfile)
         #absolute path check
         result = os.path.join(os.path.dirname(path), result)
         if('socket:[' in result):
            self.opened_sockets_by_process[str(process)].append(result.split("[")[1].strip("]"))
      if(debug > 0):
         print self.opened_sockets_by_process[str(process)]

if __name__ == '__main__':
   import sys
   process = -1
   if len(sys.argv) > 1 and sys.argv[1] > 0:
      process = sys.argv[1]
      #Init the opened socket list
      obj = ProcSockets()
      #Find the socket opened by the process
      obj.Find_Open_Socket(process)
      #Loop to find related connections
      for key in obj.opened_sockets_by_process[process]:
         found = 0
         #TCP?
         for link in  obj.sk_tcp:
            if(key == link[inode]):
                obj.print_tcp(key)
                found = 1
                break
         if(found <=0):
            #UDP?
            for link in  obj.sk_udp:
               if(key == link[inode]):
                  obj.print_udp(key)
                  found = 1
                  break
         # no socket related to the process
         if(found <=0 and debug > 0):
            print "Cannot find the socket connection ", key, process
