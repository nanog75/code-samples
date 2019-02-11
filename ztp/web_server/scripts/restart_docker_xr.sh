#!/bin/bash

# Source xr utilties to access different planes (admin, host)
source /pkg/bin/ztp_helper.sh

# Restart docker daemon on the host
echo -ne "run ssh 10.0.2.16 service docker restart\n" | xrcmd "admin"
sleep 30

# Pull the required docker image
docker pull akshshar/openr-xr
