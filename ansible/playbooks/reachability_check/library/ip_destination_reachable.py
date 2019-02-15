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
    - The module relies on NETCONF/YANG to execute a Ping RPC.
author: "Santiago Alvarez (@111pontes)"

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

from ydk.services import ExecutorService
from ydk.providers import NetconfServiceProvider
from ydk.models.cisco_ios_xr import Cisco_IOS_XR_ping_act as xr_ping_act

def ping(host="", 
         destination="", 
         repeat_count=5, 
         vrf_name="", 
         source_ip="",
         netconf_port=830,
         username="",
         password=""):
    """Execute Ping RPC over NETCONF."""

    # create NETCONF provider
    provider = NetconfServiceProvider(address=host,
                                      port=int(netconf_port),
                                      username=username,
                                      password=password,
                                      protocol='ssh')
    executor = ExecutorService()  # create executor service

    ping = xr_ping_act.Ping()  # create ping RPC object

    ping.input.destination.destination = destination
    ping.input.destination.repeat_count = repeat_count
    ping.input.destination.vrf_name = vrf_name
    ping.input.destination.source = source_ip

    ping.output = executor.execute_rpc(provider, ping, ping.output)

    rtt_min = ping.output.ping_response.ipv4[0].rtt_min
    rtt_avg = ping.output.ping_response.ipv4[0].rtt_avg
    rtt_max = ping.output.ping_response.ipv4[0].rtt_max

    return dict(success_rate=int(str(ping.output.ping_response.ipv4[0].success_rate)),
                rtt_min=int(0 if rtt_min is None else str(rtt_min)),
                rtt_avg=int(0 if rtt_avg is None else str(rtt_avg)),
                rtt_max=int(0 if rtt_max is None else str(rtt_max)))


def main():
    """Ansible module to verify IP reachability using Ping RPC over NETCONF."""
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            destination=dict(type='str', required=True),
            repeat_count=dict(type='int', default=5),
            vrf_name=dict(type='str', default="default"),
            source_ip=dict(type='str'),
            netconf_port=dict(type='str'),
            username=dict(type='str', required=True),
            password=dict(type='str', required=True, no_log=True),
            min_success_rate=dict(type='int', default=100)
        ),
        supports_check_mode=True
    )

    if module.check_mode:
        module.exit_json(changed=False)

    try:
        retvals = ping(module.params['host'],
                    module.params['destination'],
                    module.params['repeat_count'],
                    module.params['vrf_name'],
                    module.params['source_ip'],
                    module.params['netconf_port'],
                    module.params['username'],
                    module.params['password'])
    except Exception as exc:
        module.fail_json(msg='Reachability validation failed ({})'.format(exc))

    retvals['changed'] = False

    if retvals['success_rate'] >= module.params['min_success_rate']:
        module.exit_json(**retvals)
    else:
        module.fail_json(msg=('Success rate lower than expected ({}<{})').
                              format(retvals['success_rate'],
                                     module.params['min_success_rate']))


if __name__ == '__main__':
    """Execute main program."""
    main()
# End of module
