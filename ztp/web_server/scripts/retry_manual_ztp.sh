#!/bin/bash

# Quick bash script to restart ZTP cleanly
# This script is unique for the setup for Nanog75
#
# Typically invoking "ztp initiate noprompt" from CLI
# is enough. But with a single IP address allocated per 
# router on the current setup, the DHCP server will not
# respond as long as the ip address on Mgmt interface
# post a previous successful run matches the address to be
# assigned in the DHCPOFFER. 
#
# So, the workaround is to clean up mgmt interface config
# and then invoke the necessary CLI command. 
#
# Put this bash script in the bash shell of the IOS-XR router
# and execute. It will cleanly restart ZTP for you and save you some typing!

source /pkg/bin/ztp_helper.sh
set -x

read -r -d '' mgmt_clean_config << EOF
!
interface MgmtEth0/RP0/CPU0/0
 no ipv4 address
 shutdown
!
!
end
EOF

xrapply_string "$mgmt_clean_config"
xrcmd "ztp initiate noprompt"
