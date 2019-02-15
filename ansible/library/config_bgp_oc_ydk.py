#!/usr/bin/env python3
#
# Copyright 2019 Cisco Systems, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

ANSIBLE_METADATA = {
    'metadata_version': '1.0',
    'supported_by': 'community',
    'status': ['preview']
}

DOCUMENTATION = """
---
module: ip_destination_reachable
short_description: Verify rechability of an IP destination
description:
    - Uses IP ICMP echo messages to probe the reachability of an IP prefix.
    - The module relies on GNMI to execute configure BGP on a router
author: "Akshat Sharma (@irakshat)"

options:
    host:
        description:
            - IP source to send rechability probes from
        type: str
        required: true
        default: null
        choices: []
        aliases: []

    destination:
        description:
            - IP destination to send reachability probes to
        type: str
        required: true
        default: null
        choices: []
        aliases: []

    repeat_count:
        description:
            - Number of probes to test for reachability
        type: int
        required: false
        default: 5
        choices: []
        aliases: []

    vrf_name:
        description:
            - Name of VRF used as context for reachability test
        type: str
        required: false
        default: null
        choices: []
        aliases: []

    min_success_rate:
        description:
            - Percentage threshold to declare destination as reachable
        type: int
        required: true
        default: null
        choices: []
        aliases: []

requirements:
    - ydk 0.6.3 (python)
    - ydk-models-cisco-ios-xr 6.3.1 (python)
"""

EXAMPLES = """
- ip_destination_reachable:
    host: '10.0.0.1'
    destination: '10.0.0.2'
    min_success_rate: 100
    vrf_name: 'default'
"""

RETURN = """
success_rate:
  description: Percentage of successful reachability probes
  returned: ping RPC succeeds
  type: int
rtt_min:
  description: minimum round trip time of all probes
  returned: ping RPC succeeds
  type: int
rtt_avg:
  description: average round trip time of all probes
  returned: ping RPC succeeds
  type: int
rtt_max:
  description: maximum round trip time of all probes
  returned: ping RPC succeeds
  type: int
"""


from ansible.module_utils.basic import AnsibleModule

from ydk.gnmi.providers import gNMIServiceProvider
from ydk.gnmi.services import gNMIService
from ydk.path import Repository
from ydk.models.openconfig import openconfig_network_instance as oc_ni
from ydk.services import CRUDService
from ydk.models.openconfig import openconfig_policy_types as oc_policy_types
from ydk.models.openconfig import openconfig_bgp_types as oc_bgp_types
import sys

def config_bgp_ipv4(yang_repo="",
                    address="",
                    grpc_port="",
                    username="",
                    password="",
                    crud_op="add",
                    bgp={}):

     repository = Repository(yang_repo)
     provider = gNMIServiceProvider(repo=repository, 
                                    address=address, 
                                    port=int(grpc_port), 
                                    username=username, 
                                    password=password)

     gnmi_service = gNMIService()
     crud = CRUDService()

     ni = oc_ni.NetworkInstances.NetworkInstance()

     if "vrf" in list(bgp.keys()):
       ni.name = bgp["vrf"]
     else:
         print("Vrf for network Instance not specified")
         sys.exit(1)

     protocol = ni.protocols.Protocol()

     protocol.identifier =  oc_policy_types.BGP()
     protocol.name = "default"
     protocol.config.identifier = oc_policy_types.BGP()
     protocol.config.name = "default"

     if "as" in list(bgp.keys()):
         protocol.bgp.global_.config.as_ = int(bgp["as"])
     else:
         print("AS for BGP instance not specified")
         sys.exit(1)

     if "router_id" in list(bgp.keys()):
         protocol.bgp.global_.config.router_id = bgp["router_id"]

     afi_safi = protocol.bgp.global_.afi_safis.AfiSafi()
     afi_safi.afi_safi_name = oc_bgp_types.IPV4UNICAST()
     afi_safi.config.afi_safi_name = oc_bgp_types.IPV4UNICAST()
     afi_safi.config.enabled = True
     protocol.bgp.global_.afi_safis.afi_safi.append(afi_safi)


     if "peer-group-name" in list(bgp.keys()):
         peer_group = protocol.bgp.peer_groups.PeerGroup()
         peer_group.peer_group_name = bgp["peer-group-name"]
         peer_group.config.peer_group_name = bgp["peer-group-name"]
         if "peer-as" in list(bgp.keys()):
             peer_group.config.peer_as = int(bgp["peer-as"])
         if "peer-group-local-address" in list(bgp.keys()):
             peer_group.transport.config.local_address = bgp["peer-group-local-address"]
         
         afi_safi = peer_group.afi_safis.AfiSafi()   
         afi_safi.afi_safi_name = oc_bgp_types.IPV4UNICAST()
         afi_safi.config.afi_safi_name = oc_bgp_types.IPV4UNICAST()
         afi_safi.config.enabled = True                            
         peer_group.afi_safis.afi_safi.append(afi_safi) 
         protocol.bgp.peer_groups.peer_group.append(peer_group)


     if "neighbor" in list(bgp.keys()):
         neighbor = protocol.bgp.neighbors.Neighbor()
         neighbor.neighbor_address = bgp["neighbor"]
         neighbor.config.neighbor_address = bgp["neighbor"]
         #neighbor.config.peer_as = bgp["peer-as"]
         if "peer-group-name" in list(bgp.keys()):
             neighbor.config.peer_group = bgp["peer-group-name"]

         afi_safi = neighbor.afi_safis.AfiSafi()
         afi_safi.afi_safi_name = oc_bgp_types.IPV4UNICAST()
         afi_safi.config.afi_safi_name = oc_bgp_types.IPV4UNICAST()
         afi_safi.config.enabled = True                            
         neighbor.afi_safis.afi_safi.append(afi_safi)

         protocol.bgp.neighbors.neighbor.append(neighbor)

     ni.protocols.protocol.append(protocol)


     if crud_op == "add":
         response = crud.create(provider, ni)
     elif crud_op == "delete":
         response = crud.delete(provider, ni)
     elif crud_op is "update":
         response = crud.update(provider, ni)
     else:
         print("Invalid operation requested, allowed values =  add, update, delete")
         return False
     return response


def main():
    """Ansible module to configure BGP using the Openconfig Network Instances model"""
    module = AnsibleModule(
        argument_spec=dict(
            yang_repo_location=dict(type='str', required=True),
            host=dict(type='str', required=True),
            grpc_port=dict(type='str', required=True),
            username=dict(type='str', required=True),
            password=dict(type='str', required=True, no_log=True),
            crud_op=dict(type='str', required=True),
            bgp_params=dict(type='dict',required=True)
        ),
        supports_check_mode=True
    )

    if module.check_mode:
        module.exit_json(changed=False)

    try:
        retvals = config_bgp_ipv4(module.params['yang_repo_location'],
                                  module.params['host'],
                                  module.params['grpc_port'],
                                  module.params['username'],
                                  module.params['password'],
                                  module.params['crud_op'],
                                  module.params['bgp_params'])
    except Exception as exc:
        module.fail_json(msg='Failed to configure BGP ({})'.format(exc))

    if (retvals):
        module.exit_json(changed=True)
    else: 
        module.exit_json(changed=False)

if __name__ == '__main__':
    """Execute main program."""
    main()
# End of module
