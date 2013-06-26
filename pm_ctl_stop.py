#!/usr/bin/python
# -*- coding: utf-8 -*-

# pm_ctl_stop.py : Script of stop pacemaker in target node
#
# Copyright (C) 2011 NIPPON TELEGRAPH AND TELEPHONE CORPORATION
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

import time
import os
import sys
from optparse import OptionParser
import commands
import signal
import subprocess

# list of using node
list_node = []
crpm_resource = ""
crpm_node = ""
crpm_grp = ""

# user of ssh
SSH_USER = "root"

# one node timeout(sec)
NODE_TIMEOUT = 120

class Crm:

    # timeout handler for overtime kill
    def timeout_handler(self,signum,frame):

        try:
            # check child process waiting status
            # 0:child process normal stop
            # !0:overtime child process exist
            if self.sub_pro.poll() == None:
                # child process kill
                self.sub_pro.kill()
                print "timeout occurred in stop process"

        except Exception:
            print "Error occured in timeout_handler!",sys.exc_info()[0]

        sys.exit(1)

    # option setting for stop pacemaker service
    def optionParser(self):

        parser = OptionParser()
        parser.add_option("-n",default="",dest="node",help="setup node in cluster")

        try:
            (crpm,args) = parser.parse_args()
        except SystemExit:
            sys.exit(1)

        try:
            if crpm.node == "":
                parser.print_help()
                sys.exit(1)

            self.crpm_node = crpm.node

            if self.crpm_node.endswith(",") == True:
                print "requires not include comma with node name"
                sys.exit(1)

            for node_num in self.crpm_node.split(','):
                list_node.append(node_num)
                self.list_node = list_node

            # set of cluster timeout
            self.cls_timeout = len(list_node) * NODE_TIMEOUT

            # set handler and alarm
            signal.signal(signal.SIGALRM, self.timeout_handler)
            signal.alarm(self.cls_timeout)

            # stop pacemaker
            self.stop_pm(self.list_node)

        except Exception:
            print "Error occured in option!",sys.exc_info()[0]
            sys.exit(1)

    # stop pacemaker service
    def stop_pm(self,list_node):

        try:

            for stop_node in list_node:
                cmd_stop_pm = "ssh %s@%s service heartbeat stop" % (SSH_USER,stop_node)

                # run of heartbeat stop command
                self.sub_pro = subprocess.Popen(cmd_stop_pm,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
                self.sub_pro.wait()

                if self.sub_pro.returncode == 0:
                    continue
                else:
                    print "Failed to \"%s\". [%s]" % (cmd_stop_pm, self.sub_pro.stdout.read().rstrip())
                    sys.exit(1)

        except Exception:
            print "Error stop function!",sys.exc_info()[0]
            sys.exit(1)

# main process
if __name__ == '__main__':

    Crm().optionParser()
