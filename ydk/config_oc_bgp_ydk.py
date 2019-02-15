#!/usr/bin/env python

import logging,os
from argparse import ArgumentParser
from ydk.gnmi.providers import gNMIServiceProvider
from ydk.gnmi.services import gNMIService
from ydk.path import Repository
from ydk.models.openconfig import openconfig_network_instance as oc_ni
from ydk.services import CRUDService
from ydk.providers import NetconfServiceProvider
from ydk.models.openconfig import openconfig_policy_types as oc_policy_types
from ydk.models.openconfig import openconfig_bgp_types as oc_bgp_types



def config_oc_bgp_ipv4():

    ni = oc_ni.NetworkInstances.NetworkInstance()
    ni.name = "default"
    
    protocol = ni.protocols.Protocol()

    protocol.identifier =  oc_policy_types.BGP()
    protocol.name = "default"
    protocol.config.identifier = oc_policy_types.BGP()
    protocol.config.name = "default"

    protocol.bgp.global_.config.as_ = 65000
    protocol.bgp.global_.config.router_id = "172.16.1.1"

    afi_safi = protocol.bgp.global_.afi_safis.AfiSafi()
    afi_safi.afi_safi_name = oc_bgp_types.IPV4UNICAST()
    afi_safi.config.afi_safi_name = oc_bgp_types.IPV4UNICAST()
    afi_safi.config.enabled = True
    protocol.bgp.global_.afi_safis.afi_safi.append(afi_safi)


    peer_group = protocol.bgp.peer_groups.PeerGroup()                    
    peer_group.peer_group_name = "IBGP"
    peer_group.config.peer_group_name = "IBGP"
    peer_group.config.peer_as = 65000 
    peer_group.transport.config.local_address = "172.16.1.1"

    afi_safi = peer_group.afi_safis.AfiSafi()   
    afi_safi.afi_safi_name = oc_bgp_types.IPV4UNICAST()
    afi_safi.config.afi_safi_name = oc_bgp_types.IPV4UNICAST()
    afi_safi.config.enabled = True                            
    peer_group.afi_safis.afi_safi.append(afi_safi) 
    protocol.bgp.peer_groups.peer_group.append(peer_group)

    neighbor = protocol.bgp.neighbors.Neighbor()
    
    neighbor.neighbor_address = "172.16.4.1"
    neighbor.config.neighbor_address = "172.16.4.1"
    neighbor.config.peer_group = "IBGP"
    afi_safi = neighbor.afi_safis.AfiSafi()
    afi_safi.afi_safi_name = oc_bgp_types.IPV4UNICAST()
    afi_safi.config.afi_safi_name = oc_bgp_types.IPV4UNICAST()
    afi_safi.config.enabled = True                            
    neighbor.afi_safis.afi_safi.append(afi_safi)
    
    protocol.bgp.neighbors.neighbor.append(neighbor)

    ni.protocols.protocol.append(protocol)

    return ni


if __name__ == "__main__":
    """Execute main program."""
    parser = ArgumentParser()
    parser.add_argument("-v", "--verbose", help="print debugging messages",
                        action="store_true")
    parser.add_argument('-i', '--grpc-ip', action='store', dest='grpc_ip',
                    help='Specify the IOS-XR GRPC server IP address', required=True)
    parser.add_argument('-g', '--grpc-port', action='store', dest='grpc_port',
                    help='Specify the IOS-XR GRPC server port', required=True)
    parser.add_argument('-u', '--username', action='store', dest='username',
                    help='Specify username to connect to gRPC server on XR', required=True)
    parser.add_argument('-p', '--password', action='store', dest='password',
                    help='Specify password to connect to gRPC server on XR', required=True)
    parser.add_argument('-y', '--yang-repo-path', action='store', dest='yang_repo_location',
                    help='Specify yang repo path', required=True)
    parser.add_argument('-e', '--extra-verbose', action='store_true',
                    help='Extra Verbose logs')
    args = parser.parse_args()

    # log debug messages if verbose argument specified
    if args.verbose:
        logger = logging.getLogger("ydk")
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(("%(asctime)s - %(name)s - "
                                      "%(levelname)s - %(message)s"))
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        if args.extra_verbose:
            os.environ['GRPC_TRACE'] = 'all'
            os.environ['GRPC_VERBOSITY'] = 'DEBUG'

    repository = Repository(args.yang_repo_location)
    provider = gNMIServiceProvider(repo=repository, 
                                   address=args.grpc_ip,
                                   port=int(args.grpc_port), 
                                   username=args.username, 
                                   password=args.password)
    gnmi_service = gNMIService()

    crud = CRUDService()

    bgp_ni = config_oc_bgp_ipv4()

    crud.create(provider, bgp_ni)
