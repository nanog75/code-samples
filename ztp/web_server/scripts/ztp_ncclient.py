#!/usr/bin/env python

import sys, os, warnings
import time
sys.path.append("/pkg/bin")
from ztp_helper import ZtpHelpers
warnings.simplefilter("ignore", DeprecationWarning)
from ncclient import manager
import logging, json, subprocess
from lxml import etree

from ctypes import cdll

libc = cdll.LoadLibrary('libc.so.6')
_setns = libc.setns
CLONE_NEWNET = 0x40000000

rootLogger = logging.getLogger('ncclient.transport.session')
rootLogger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
rootLogger.addHandler(handler)

WEB_SERVER_URL = "http://100.96.0.20/"
PIP_RPM_URL = WEB_SERVER_URL + "packages/python-pip-7.1.0-r0.0.core2_64.rpm"
SERVER_XML_URL = WEB_SERVER_URL+"xml/"
SYSLOG_SERVER = "100.96.0.20"
SYSLOG_PORT = "514"
HTTPS_PROXY = ""

# List of XML files to be downloaded and applied as configuration 
# through ncclient onbox. 
# Hint: Add to this list on the server and download and use with ncclient
# appropriately for each router to achieve your final configuration 
XML_FILE_LIST =  ['lldp_config_oc.xml', 
                  'interface_config_oc.xml']

# Use this Serial Number map to figure out the router specific URL
# to use for downloads based on the local router's Serial Number
SERIAL_NO_MAP = {'FGE00050000': 'rtr1',
                 'FGE00080000': 'rtr2',
                 'FGE000b0000': 'rtr3',
                 'FGE00170000': 'rtr4'}

def install_and_import(package):
    import importlib
    try:
        importlib.import_module(package)
    except ImportError:
        try:
          from pip import main as pipmain
        except:
          from pip._internal import main as pipmain
        pipmain(['install', '--proxy='+HTTPS_PROXY, package])
    finally:
        globals()[package] = importlib.import_module(package)

class ZtpFunctions(ZtpHelpers):
    def ncclient_connect(self, host, duration=120):
        """User defined method in Child Class
           Method to connect to the netconf agent in IOS-XR
           using ncclient and return the ncclient manager handle.
           Since the netconf agent takes time to initialize,
           this method retries on failure for max specified duration
           until the connection succeeds.
           :param host: The local loopback ip to connect to (setup
                        using netconf_init()
           :type cmd: str 
           :param duration: maximum amount of time till which the method
                            retries to achieve a successful connection
           :type duration: str

           :return: Returns ncclient.manager() object on success
                    and None on failure
           :rtype: object 
        """
        connected = False
        t_start = time.time()
        t_end = t_start + duration 
        while time.time() < t_end:
            try:
                ncclient_manager = manager.connect(host=host, 
                                           port=830, 
                                           username="ztp-user", 
                                           device_params={'name':'iosxr'}, 
                                           hostkey_verify=False,
                                           look_for_keys=False,
                                           key_filename="/root/.ssh/id_rsa",
                                           allow_agent=False)
                connected = True 
                break
            except Exception as e:
                self.syslogger.info("Failed to connect to netconf agent")
                self.syslogger.info(e)
                self.syslogger.info("Trying to connect again, time elapsed: "+str(time.time()-t_start))
                time.sleep(5)

        if connected:
            self.syslogger.info("ncclient session established!, time elapsed: "+str(time.time()-t_start))
            return ncclient_manager
        else:
            return None 


    def run_bash(self, cmd=None, vrf="global-vrf", pid=1):
        """User defined method in Child Class
           Wrapper method for basic subprocess.Popen to execute 
           bash commands on IOS-XR in specified vrf (or global-vrf 
           by default).
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
            if cmd is not None:
                process = subprocess.Popen(cmd, 
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE,
                                           shell=True)
                out, err = process.communicate()
                if self.debug:
                    self.logger.debug("output: "+out)
                    self.logger.debug("error: "+err)
            else:
                self.syslogger.info("No bash command provided")
                return {"status" : 1, "output" : "",
                        "error" : "No bash command provided"}

            status = process.returncode

            return {"status" : status, "output" : out, "error" : err}


    def get_serial_number(self):
        """User defined method in Child Class
           Method to fetch the serial number of the router
           that this script is running on. Can be useful in
           invoking router/device specific URLs to take specific
           action based on the router.
           :return: Returns Serial number of the device (also used
                    by ZTP DHCP requests) on success
                    Returns empty string on failure
           :rtype: str 
        """
        cmd = "dmidecode -s system-serial-number | grep -v -e \"^#\""        
        response = self.run_bash(cmd)
        if not response["status"]:
            self.syslogger.info("Successfully fetched Serial Number:")
            if self.debug:
                self.logger.debug(response["output"])
            return response["output"]
        else:
            self.syslogger.info("Failed to fetch Serial Number:")
            if self.debug:
                self.logger.debug(response["output"])
                self.logger.debug(response["error"])
            return ""


if __name__ == '__main__':

    # ZtpFunctions is a child class that inherits capabilities from
    # the ZtpHelpers library native to the OS.
    # A couple of methods(see above) are added to ZtpFunctions on top 
    # of the base functionality.
    # The ZtpHelpers class and consequently the ZtpFunctions class
    # accepts syslog parameters for the __init__() method. 
    #
    # Using the class method ztp_script.syslogger.info(<string>)
    # will automatically send a formatted syslog to the specified
    # syslog server and file (all optional)

    ztp_script = ZtpFunctions(syslog_server=SYSLOG_SERVER,
                              syslog_port=SYSLOG_PORT,
                              syslog_file="/root/ztp_python.log")


    # Let's set up some packages we'll use later in the script

    # Before we fetch the python packages, install pip and 
    # upgrade it.
   
    cmd = "wget " + PIP_RPM_URL + " -O /tmp/pip.rpm"
    if not ztp_script.run_bash(cmd)["status"]:
        ztp_script.syslogger.info("Successfully downloaded python-pip rpm")
 
        cmd = "rpm -ivh --force /tmp/pip.rpm"
        if not ztp_script.run_bash(cmd)["status"]:
            ztp_script.syslogger.info("Successfully installed python-pip rpm")

            cmd = "pip --proxy="+HTTPS_PROXY+" install --upgrade pip"
            if not ztp_script.run_bash(cmd)["status"]:
                ztp_script.syslogger.info("Successfully upgraded pip")
            else:
                ztp_script.syslogger.info("Failed to upgrade pip")
                sys.exit(1)
        else:
            ztp_script.syslogger.info("Failed to install pip")
            sys.exit(1)
    else:
        ztp_script.syslogger.info("Failed to download python-pip rpm")
        sys.exit(1) 
  


    
    # Install packages through pip and import them. Requires internet access
    # through the gateway in your ZTP LAN
    for package in ['xmltodict']:
        try:
          install_and_import(package)
          ztp_script.syslogger.info("Successfully installed and imported "+package)
        except:
          ztp_script.syslogger.info("Failed to install/import "+package)
          sys.exit(1)


    # Choose any ip you need for the host value
    # This will be set up as a local loopback(/32) that the onbox ncclient will connect 
    # to through the ncclient_init() method. 
    # It will be cleaned up as part of ncclient_cleanup() method
    host = "172.16.20.1"

    # Initialize the basic configuration for ncclient to work
    # Sets up local loopback as host to connect to and enable netconf on port 830.
    # Also imports the local key (/root/.ssh/id_rsa.pub) for password free operation
    result = ztp_script.ncclient_init(host_ip=host)
    if result["status"] == "error":
        ztp_script.syslogger.info("Failed to initialize configuration for ncclient, aborting....")

        # sys.exit() used judiciously is quite important. ZTP will retry if your script returns a
        # non zero exit code. In production, this ensures the box continuously looks to download and
        # execute a working script by retrying on failure.
        sys.exit(1)


    # Connects to IOS-XR netconf agent and returns a manager handle for ncclient
    # This is a method of the child class defined above that retries the connection
    # during initial boot for a specified maximum duration (default = 120seconds)
    nc_mgr = ztp_script.ncclient_connect(host=host)
   
    if nc_mgr is None:
        ztp_script.syslogger.info("ncclient Manager not initialized, aborting...")
        sys.exit(1)    
    else:
        # From here on, the operation is just normal ncclient usage
        response = nc_mgr.get_config(source="running")
        print(response)
        response_dict=xmltodict.parse(str(response))
        print json.dumps(response_dict, indent=4)

        nc_mgr.close_session()


    # Cleaning up the internal loopback configuration created as part of the
    # ncclient_init() configuration is good practice. This is optional however.
    result = ztp_script.ncclient_cleanup()
    if result["status"] == "error":
        ztp_script.syslogger.info("Failed to cleanup ncclient dependencies, aborting...")
        sys.exit(1)
