#!/usr/bin/env python

import sys, subprocess
sys.path.append("/pkg/bin")
from ztp_helper import ZtpHelpers
import json
from pprint import pprint
import time

from ctypes import cdll

libc = cdll.LoadLibrary('libc.so.6')
_setns = libc.setns
CLONE_NEWNET = 0x40000000

class BashUtilities(ZtpHelpers):

    def admincmd(self, cmd=None, root_lr_user=None):
        """Issue an admin exec cmd and obtain the output
           :param cmd: Dictionary representing the XR exec cmd
                       and response to potential prompts
                       { 'exec_cmd': '', 'prompt_response': '' }
           :type cmd: string 
           :return: Return a dictionary with status and output
                    { 'status': 'error/success', 'output': '' }
           :rtype: string
        """

        if cmd is None:
            return {"status" : "error", "output" : "No command specified"}

        if root_lr_user is None:
            return {"status" : "error", "output" : "No root-lr user specified"}

        status = "success"


        if self.debug:
            self.logger.debug("Received admin exec command request: \"%s\"" % cmd)

        cmd = "export AAA_USER="+root_lr_user+" && source /pkg/bin/ztp_helper.sh && echo -ne \""+cmd+"\\n \" | xrcmd \"admin\""

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        out, err = process.communicate()


        if process.returncode:
            status = "error"
            output = "Failed to get command output"
        else:
            output_list = []
            output = ""

            for line in out.splitlines():
                fixed_line= line.replace("\n", " ").strip()
                output_list.append(fixed_line)
                if "syntax error: expecting" in fixed_line:
                    status = "error"
                output = filter(None, output_list)    # Removing empty items

        if self.debug:
            self.logger.debug("Exec command output is %s" % output)

        return {"status" : status, "output" : output}

    def run_bash(self, cmd=None, vrf="global-vrf", pid=1):
        """User defined method in Child Class
           Wrapper method for basic subprocess.Popen to execute 
           bash commands on IOS-XR.
           :param cmd: bash command to be executed in XR linux shell. 
           :type cmd: str 
           
           :return: Return a dictionary with status and output
                    { 'status': '0 or non-zero', 
                      'output': 'output from bash cmd' }
           :rtype: dict
        """

        with open(self.get_netns_path(nsname=vrf,nspid=pid)) as fd:
            self.setns(fd, CLONE_NEWNET)

            if self.debug:
                self.logger.debug("bash cmd being run: "+cmd)
            ## In XR the default shell is bash, hence the name
            if cmd is not None:
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                out, err = process.communicate()
                if self.debug:
                    self.logger.debug("output: "+out)
                    self.logger.debug("error: "+err)
            else:
                self.logger.info("No bash command provided")
                return {"status" : 1, "output" : "", "error" : "No bash command provided"}

            status = process.returncode

            return {"status" : status, "output" : out, "error" : err}



if __name__ == "__main__":

    # Create an Object of the child class, syslog parameters are optional. 
    # If nothing is specified, then logging will happen to local log rotated file.

    bash_util = BashUtilities(syslog_file="/root/ztp_python.log")

    print("\n####### Restart the docker daemon to make sure changes take effect######\n")
    result = bash_util.admincmd(cmd = "run ssh 10.0.2.16 service docker restart", root_lr_user="ztp-user")    

    if result["status"] == "success":
        print("\n###### Successfully restarted the docker daemon, response: ######\n")
        pprint(result["output"])
        print("\n###### return value in json: ######\n")
        print json.dumps(result["output"],sort_keys=True, indent=4)
    else:
        print("Failed to run admincmd, aborting ...")
        pprint(result["output"])
        sys.exit(1)


    print("Sleeping for about 30 seconds, waiting for the docker daemon to be up")
    time.sleep(30)
   
    print("\n#######Pulling the docker image for Open/R ######\n")
    result = bash_util.run_bash(cmd = "export DOCKER_HOST=unix:///misc/app_host/docker.sock && ip netns exec global-vrf docker pull  akshshar/openr-xr")

    if result["status"]:
        print("Failed to pull docker image")
        sys.exit(1)
    else:
        print("Successfully downloaded the docker image")
        print(result["output"])
        sys.exit(0)
