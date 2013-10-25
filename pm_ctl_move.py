#!/usr/bin/python
# -*- coding: utf-8 -*-

# pm_ctl_move.py : Moving the resource with cluster envirment
#
# Copyright (C) 2011 NIPPON TELEGRAPH AND TELEPHONE CORPORATION
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

import time
import os
import sys
from optparse import OptionParser
import commands
import re

# list of using node
crpm_resource = ""
crpm_node = ""
crpm_grp = ""
SSH_USER = "root"
# information of node status
# by using crm_mon
tbl_crm_mon_total = {}
# list of using resource group
list_reso = []
# information of resource for each node
rsc_tbl = {}

class Crm:
    # moving resource with option arguments
    def optionParser(self):

        parser = OptionParser()
        parser.add_option("-r",default="",dest="resource",help="setup resource in cluster")
        parser.add_option("-n",default="",dest="node",help="setup node in cluster")

        try:
            (crpm,args) = parser.parse_args()
        except SystemExit:
            sys.exit(1)

        try:
            if crpm.resource == "" or crpm.node == "":
                parser.print_help()
                sys.exit(1)

            self.crpm_resource = crpm.resource
            self.crpm_node = crpm.node
                
            crpm_node = self.crpm_node
            obj_crpm_node = str(crpm_node)

            crpm_resource = self.crpm_resource
            obj_crpm_resource = str(crpm_resource)
            list_reso.append(crpm_resource)

            self.move_pm(obj_crpm_node,obj_crpm_resource)

        except Exception:
            print "Error occured in option!",sys.exc_info()[0]
            sys.exit(1)


    def crm_msec(self,t):
        '''
        See lib/common/utils.c:crm_get_msec().
        '''
        convtab = {
            'ms': (1,1),
            'msec': (1,1),
            'us': (1,1000),
            'usec': (1,1000),
            '': (1000,1),
            's': (1000,1),
            'sec': (1000,1),
            'm': (60*1000,1),
            'min': (60*1000,1),
            'h': (60*60*1000,1),
            'hr': (60*60*1000,1),
        }
        if not t:
            return -1
        r = re.match("\s*(\d+)\s*([a-zA-Z]+)?", t)
        if not r:
            return -1
        if not r.group(2):
            q = ''
        else:
            q = r.group(2).lower()
        try:
            mult,div = convtab[q]
        except:
            return -1
        return (int(r.group(1))*mult)/div

    # get resource information from crm_mon
    def parse_rsc_info(self):
        try:

            for node in tbl_crm_mon_total.keys():
                grp_flg = False
                rsc_list = list()

                for line in tbl_crm_mon_total[node].split('\n'):
                    # primitive


                    if len(line) > 0 and line.split()[0] == list_reso[0]:
                        rsc_list.append((list_reso[0], None))
                        rsc_list.append((list_reso[0], " ".join(line.split()[2:])))
                        break
                        
                    # group
                    elif line.endswith(" Resource Group: " + list_reso[0]):
                        rsc_list.append((list_reso[0], None))
                        grp_flg = True
                        
                    elif grp_flg:
                        if line.startswith("     "):
                            rsc_list.append((line.split()[0], " ".join(line.split()[2:])))
                        else:
                            break

                # The following are examples of setting "rsc_tbl"
                #  - primitive resource:
                #    { srv01 : [ ("prm1", None), ("prm1",   "Started srv01") ] }
                #  - group resource:
                #    { srv01 : [ ("grp1", None), ("prm1-1", "Started srv01"), ("prm1-2", "Started srv01") ] }
                rsc_tbl[node] = list(rsc_list)

        except Exception:
              print "Error occured in process of parsing resource information!",sys.exc_info()[0]
              sys.exit(1)

    # execute resource move
    def move_pm(self,mv_node,crpm_resource):

        try:

            fl_loop = 0
            #move target node
            cmd_move_pm = "ssh %s@%s crm resource move %s %s force" % (SSH_USER,mv_node,crpm_resource,mv_node)
            status,output = commands.getstatusoutput(cmd_move_pm)
            if status !=0:
                print "Failed to \"%s\". [%s]" % (cmd_move_pm, output.rstrip())
                sys.exit(1)

            #sleep for transition-delay
            cmd_sleep = "ssh %s@%s crm_attribute -Gq -t crm_config -n crmd-transition-delay" % (SSH_USER,mv_node)
            status,delay = commands.getstatusoutput(cmd_sleep)

            if delay:
                delaymsec = self.crm_msec(delay)

                if 0 < delaymsec:
                    time.sleep(delaymsec / 1000)

            # look up DC node
            cmd_crmadminD = "ssh %s@%s crmadmin -D | awk '{print $4}'" % (SSH_USER,mv_node)
            s_crmadminD,out_crmadminD = commands.getstatusoutput(cmd_crmadminD)

            # status of node
            cmd_crmadminS = "ssh %s@%s crmadmin -S %s" % (SSH_USER,mv_node,out_crmadminD)
            s_crmadminS,out_crmadminS = commands.getstatusoutput(cmd_crmadminS)

            # loop for while status node is S_IDLE
            if out_crmadminS.find("S_IDLE (ok)") == -1:
                while True :
                    time.sleep(2)
                    cmd_crmadminSS = "ssh %s@%s crmadmin -S %s" % (SSH_USER,mv_node,out_crmadminD)
                    s_crmadminSS,out_crmadminSS = commands.getstatusoutput(cmd_crmadminSS)

                    if out_crmadminSS.find("S_IDLE (ok)") != -1:
                        break

            # run crm_mon command for checking the resource status
            cmd_crm_mon = "ssh %s@%s crm_mon -r1" % (SSH_USER,out_crmadminD)

            crm_status,crm_output = commands.getstatusoutput(cmd_crm_mon)

            tbl_crm_mon_total[out_crmadminD]=crm_output

            self.parse_rsc_info()

            for rsc_name, rsc_stat in rsc_tbl[out_crmadminD]:

                if rsc_stat == None:
                    continue

                #if not rsc_stat.find("Started"):
                if rsc_stat.find("Started") != 0:
                    print "It is not exist active resources %s" % out_crmadminD
                    sys.exit(1)

            # run unmove command
            cmd_unmove = "ssh %s@%s crm resource unmove %s" % (SSH_USER,mv_node,crpm_resource)

            unmv_status,unmv_output = commands.getstatusoutput(cmd_unmove)
            if unmv_status != 0:
                print "unmove to %s is fail" % (mv_node)
                sys.exit(1)

        except Exception:
            print "Error move function!",sys.exc_info()[0]
            sys.exit(1)

# main process
if __name__ == '__main__':

    Crm().optionParser()
