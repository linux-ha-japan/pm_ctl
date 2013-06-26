#!/usr/bin/python
# -*- coding: utf-8 -*-

# pm_ctl_status.py : Script for Status information of cluster group and each node
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

import threading
import time
import os
import sys
from optparse import OptionParser
import commands
import re

# list of using node
list_node = []

# list of using resource group
list_reso = []

# list of DC node
list_dc = set()

crpm_resource = ""
crpm_node = ""

# information of node status
# by using crm_mon
tbl_crm_mon_total = {}

# information of resource status
# by using ptest
tbl_ptest_total = {}

# information of resource status
# by using ptest
n_check_tbl ={}

# table of node status
# 0:Online,1:OFFLINE,2:UNCLEAN
node_status_tbl = {}

# table of active node status
# 0:node is active, 1:node is standby
node_act_tbl = {}

# table of resource status using ptest command
# 0:resource is available
# 1:resource is not available
node_pt_tbl = {}

# set the result of node status
judge_dic = {}

# display of active node
SET_ACT ="ACT"

# display of standby node
SET_SBY ="SBY"

# display of out of service node
SET_OUS ="OUS"

# display of unclean node
SET_UNCLEAN ="UNCLEAN"

# display of offline node
SET_NONE ="NONE"

# minus infinity value 
MINUS_INF = "-1000000"

# user of ssh
SSH_USER = "root"

# information of crm_mon for each node
thread_crm_cmd = "ssh %s@%s crm_mon -r1"

# information of ptest for each node
thread_ptest_cmd= "ssh %s@%s ptest -L -s"

# information of resource for each node
rsc_tbl = {}

class Crm:
    # run thread for each node after setting argument from command
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
            
            crpm_resource = self.crpm_resource

            # the case of more than one group name
            if crpm_resource.find(",") != -1:
                print "requires one resource"
                sys.exit(1)

            # the case of incorrect node argument set
            if self.crpm_node.endswith(",") == True:
                print "requires not include comma with node name"
                sys.exit(1)

            list_reso.append(crpm_resource)
            obj_crpm_resource = str(crpm_resource)

            for node_num in self.crpm_node.split(','):
                list_node.append(node_num)
                self.list_node = list_node
	        
                thread = myThread(SSH_USER,node_num,obj_crpm_resource,tbl_crm_mon_total,tbl_ptest_total)
                # Start new Threads
                thread.start()
                thread.join()

        except Exception:
            print "Error occured in option!",sys.exc_info()[0]
            sys.exit(1)


    # judge of target node status
    def judge(self,d1):

        try:

            str_nstatus = str(node_status_tbl[d1])
            str_nact    = str(node_act_tbl[d1])
            str_pt      = str(node_pt_tbl[d1])
 
            # node is ACT status
            if str_nstatus=="0" and str_nact=="0" and str_pt=="0":
                judge_dic[d1] = SET_ACT

            # node is SBY status
            if str_nstatus=="0" and str_nact=="1" and str_pt=="0":
                judge_dic[d1] = SET_SBY

            # node is OUS status
            if str_nstatus=="0" and str_pt=="1":
                judge_dic[d1] = SET_OUS
            
            # node is NONE status
            if str_nstatus=="1":
                judge_dic[d1] = SET_NONE

            # node is UNCLEAN status
            if str_nstatus=="2":
                judge_dic[d1] = SET_UNCLEAN

        except Exception:
              print "Error occured in judge!",sys.exc_info()[0]
              sys.exit(1)

            
    # judge of target cluster status
    def report(self,dc_node):

        try:

            list_join = []

            for node in list_node:
                list_join.append(node + ":" + judge_dic[node])

            str_result = ",".join(list_join)

            g_status    = 0
            cnt_act     = 0
            cnt_sby     = 0
            cnt_none    = 0
            cnt_ous     = 0
            cnt_unclean = 0

            for node_stat in judge_dic.values():
                if   node_stat == SET_ACT:     cnt_act     = cnt_act     + 1
                elif node_stat == SET_SBY:     cnt_sby     = cnt_sby     + 1
                elif node_stat == SET_OUS:     cnt_ous     = cnt_ous     + 1
                elif node_stat == SET_UNCLEAN: cnt_unclean = cnt_unclean + 1
                elif node_stat == SET_NONE:    cnt_none    = cnt_none    + 1

            #abstract status of each node and judge status of cluster
            #0:every node is available
            #1:just one node available
            #2:every node is not available
            #3:Pacemaker stop
            if cnt_act >= 1 and cnt_none == 0 and cnt_unclean == 0 and cnt_ous == 0:
                g_status = 0
            elif cnt_act >= 1:
                g_status = 1
            elif cnt_none >= 1 and cnt_unclean == 0 and cnt_ous == 0 and cnt_act == 0 and cnt_sby == 0:
                g_status = 3
            else:
                g_status = 2

            n_check_tbl[dc_node] = list_reso[0] + ":" + str(g_status) + "/" + str_result

        except Exception:
            print "Error occured in report!",sys.exc_info()[0]
            sys.exit(1)

    #judge dc node
    def dc_check(self):
        try:

            for node in tbl_crm_mon_total.keys():
                for line in tbl_crm_mon_total[node].split('\n'):
                    if line.startswith("Current DC: "):

                        dc_node = line.split()[2]
                        if dc_node != "NONE":
                            list_dc.add(dc_node)
                        break

        except Exception:
              print "Error occured in check DC!",sys.exc_info()[0]
              sys.exit(1)

    # judge whether cluster is exist or not after script runing commnad
    def check_rsc(self,d1):
        try:

            if len(rsc_tbl[d1]) > 1:
                return True
            else:
                #If there is not resource
                node_status_tbl[d1] = 1
                node_act_tbl[d1] = 1
                node_pt_tbl[d1] = 1
                return False

        except Exception:
              print "Error occured in check resource!",sys.exc_info()[0]
              sys.exit(1)

    # judge the status of target node from crm_mon dictionary
    def pro_crm_mon(self,node,dc_node):
        try:

            for line in tbl_crm_mon_total[dc_node].split('\n'):

                if line.find(node) != -1:

                    if line.startswith("Online:"):
                        node_status_tbl[node] = 0
                        break

                    elif line.find("UNCLEAN") != -1:
                        node_status_tbl[node] = 2
                        node_act_tbl[node] = 1
                        node_pt_tbl[node] = 1
                        break

                    elif \
                        (line.startswith("OFFLINE:")) or \
                        (line.startswith("Node " + node) and line.find("standby") != -1) or \
                        (line.startswith("Node " + node) and line.find("pending") != -1):

                        node_status_tbl[node] = 1
                        node_act_tbl[node] = 1
                        node_pt_tbl[node] = 1
                        break

            node_act_tbl[node] = 0
            for rsc_name, rsc_stat in rsc_tbl[dc_node]:
                if rsc_stat == None:
                    continue
                if not rsc_stat == "Started " + node:
                    node_act_tbl[node] = 1
                    if rsc_stat.endswith(" (unmanaged)"):
                         node_pt_tbl[node] = 1
                         return
                    break

            self.pro_ptest(node,dc_node)

        except Exception:
            print "Error occured in process of crm_mon!",sys.exc_info()[0]
            sys.exit(1)

    # judge the status of resource from ptest dictionary
    def pro_ptest(self,d1,dc_node):
        try:

            node_pt_tbl[d1] = 0

            # primitive or not
            if len(rsc_tbl[dc_node]) > 1 and rsc_tbl[dc_node][0][0] == rsc_tbl[dc_node][1][0]:
                rsc_color = "native_color:"
            else:
                rsc_color = "group_color:"

            for line in tbl_ptest_total[dc_node].split('\n'):

                if \
                    line.startswith(rsc_color) == False or \
                    line.endswith(MINUS_INF)   == False or \
                    line.find(" " + d1 + ": ") == -1:

                    continue

                for rsc_name, rsc_stat in rsc_tbl[dc_node]:

                    if line.startswith(rsc_color + " " + rsc_name + " "):
                        node_pt_tbl[d1] = 1
                        return

        except Exception:
              print "Error occured in process of ptest!",sys.exc_info()[0]
              sys.exit(1)

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

# run threads from each target node
class myThread (threading.Thread):

    def __init__(self, user,node_name,reso,tbl_crm_mon_total,tbl_ptest_total):

        self.user = user
        self.node_name = node_name
        self.crpm_resource = reso
        self.cmd_crm_mon = ""
        self.cmd_ptest = ""
        threading.Thread.__init__(self)

        node_status_tbl[self.node_name]   = 1
        node_act_tbl[self.node_name]      = 1
        node_pt_tbl[self.node_name]       = 1
        tbl_crm_mon_total[self.node_name] = ""
        tbl_ptest_total[self.node_name]   = ""

    def run(self):

        self.cmd_crm_mon = thread_crm_cmd % (self.user,self.node_name)

        status,output = commands.getstatusoutput(self.cmd_crm_mon)
        if status !=0:
           sys.exit()

        tbl_crm_mon_total[self.node_name]=output

        grname= self.crpm_resource

        self.cmd_ptest = thread_ptest_cmd  % (self.user,self.node_name)

        status, output = commands.getstatusoutput(self.cmd_ptest)
        tbl_ptest_total[self.node_name]=output

# main process
if __name__ == '__main__':

    Crm().optionParser()
    Crm().parse_rsc_info()
    Crm().dc_check()

    # set not dc node
    not_dc = list_node[:]
    for dc in list_dc:
        if dc not in list_node: continue
        not_dc.remove(dc)

    sb_no_act = False
    exist_rsc = False
    dc_cnt = len(list_dc)

    # loop for every node which is dc and not dc node
    for report_node in list(list_dc) + not_dc:
        if report_node not in list_node: continue

        # continue that dc is exist but not exist result of crm_mon
        if dc_cnt != 0 and Crm().check_rsc(report_node) == False:
            continue

        exist_rsc = True
        for node in tbl_crm_mon_total.keys():
            Crm().pro_crm_mon(node, report_node)
            Crm().judge(node)

        # create node and cluster status
        Crm().report(report_node)

        # check multi DC node, and not exist ACT.
        if dc_cnt >= 2 and n_check_tbl[report_node].find(SET_ACT) == -1:
            sb_no_act = True
            continue

        # print report
        print n_check_tbl[report_node]
        sys.exit(0)


    if exist_rsc == False:
        print "Not Exist resource \"%s\"." % list_reso[0]
    elif sb_no_act:
        print "Exist two or more DC nodes. And, not exist ACT node."
    else:
        print "Unexpected error occurred."

    sys.exit(1)
