#!/usr/bin/env python

import sys, os, warnings
import time
sys.path.append("/pkg/bin")
from ztp_helper import ZtpHelpers
warnings.simplefilter("ignore", DeprecationWarning)
from ncclient import manager
import logging
from lxml import etree
import json

rootLogger = logging.getLogger('ncclient.transport.session')
rootLogger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
rootLogger.addHandler(handler)


def install_and_import(package):
    import importlib
    try:
        importlib.import_module(package)
    except ImportError:
      try:
        from pip import main as pipmain
      except:
        from pip._internal import main as pipmain
      pipmain(['install', package])
    finally:
        globals()[package] = importlib.import_module(package)

class ZtpFunctions(ZtpHelpers):
    def ncclient_connect(self, host, duration=120):
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

if __name__ == '__main__':

    # ZtpFunctions is a child class that inherits capabilities from
    # the ZtpHelpers library native to the OS.
    # A couple of methods(see above) are added to ZtpFunctions on top of the base functionality.
    ztp_script = ZtpFunctions(syslog_server="100.96.0.20",syslog_port=514)

    # Install packages through pip. Requires internet access
    # through the gateway in your ZTP LAN
    for package in ['xmltodict']: 
        install_and_import(package)

    # Choose any ip you need for the host value
    # This will be set up as a local loopback that ncclient onbox will connect to
    # through the ncclient_init() method. It will be cleaned up as part of ncclient_cleanup() method

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
    # during initial boot as needed.
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
