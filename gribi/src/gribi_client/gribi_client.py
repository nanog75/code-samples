import json
import os
import threading
import argparse
import pprint

import sys
sys.path.append("../")
from gribi_api import GrpcClient
from genpy import gribi_pb2
from util import util
#from gribi_api import serializers
#
#
#
class clientClass():
    json_params = None
    client = None
    global_notif = None
    is_ut_running = False

    ut_mutex = threading.Lock()

    def is_running():
        # if unit test is done return false
        # otherwise return true
        # release lock if it has been acquired
        if clientClass.ut_mutex.acquire(False):
            check_ut_status = clientClass.is_ut_running
            clientClass.ut_mutex.release()
            if check_ut_status == False:
                return False
            return True
        else:
            return True

    def set_ut_running(running):
        clientClass.ut_mutex.acquire()
        clientClass.is_ut_running = running
        clientClass.ut_mutex.release()

#
#
#
def setUpModule(file_name, server_ip, server_port):
    clientClass.set_ut_running(True)

    # Read the .json template
    filepath = os.path.join(os.path.dirname(__file__), file_name)

    with open(filepath) as fp:
        clientClass.json_params = json.loads(fp.read())
        #print(clientClass.json_params)
    # Setup GRPC channel for RPC tests
    #host, port = util.get_server_ip_port()
    clientClass.client = GrpcClient(server_ip, server_port)

    # GRPC channel used for Global notifications
    # Setup a channel for the Global notification thread
    clientClass.global_notif = GrpcClient(server_ip, server_port)

def tearDownModule():
    clientClass.set_ut_running(False)

def mpls_parse(labels, op, show):
   # mpls labels
    for elem in labels:
        print ("Mpls")
        response, success = clientClass.client.gribi_op_mpls([elem], op, show)
        print (response)
        print (success)
    return

def routes_parse(routes, op, show):
    # routes, v4 and v6
    for elem in routes:
        print ("Route")
        response, success = clientClass.client.gribi_op_routes([elem], op, show)
        print (response)
        print (success)
    return

def nhgs_parse(nhgs, op, show):
    # next hop groups
    for elem in nhgs:
        print ("Next Hop Group")
        response, success = clientClass.client.gribi_op_nh_group([elem], op, show)
        print (response)
        print (success)
    return

def nhs_parse(nhs, op, show):
    # next hops
    for elem in nhs:
        print ("Next Hop")
        response, success = clientClass.client.gribi_op_nh([elem], op, show)
        print (response)
        print (success)
    return

def main():

    # Instantiate the parser
    usage = ("This is the gribi client.")
    parser = argparse.ArgumentParser(description= usage)

    parser.add_argument('-j','--json', type= str, required = True, help = "Full json path and name")
    parser.add_argument('-ip', '--server_ip', type=str, required = True, help = "Server host ip")
    parser.add_argument('-port', '--server_port', type=int, default = 57344, help = "Grpc port")
    parser.add_argument('-d', '--delete', action="store_true", help = "Run file with operation delete")
    parser.add_argument('-p', '--print_out', action="store_true", help = "Print out the modify request")
    args=parser.parse_args()

    op = gribi_pb2.AFTOperation.ADD
    file_name = args.json
    server_ip = args.server_ip
    server_port = args.server_port
    show = False

    if args.delete:
        op = gribi_pb2.AFTOperation.DELETE
    if args.print_out:
        show = True

    setUpModule(file_name, server_ip, server_port)

    nhs = clientClass.json_params["gribi_nhs"]
    nh_groups = clientClass.json_params["gribi_nh_groups"]
    routes = clientClass.json_params["gribi_routes"]
    mpls_path = clientClass.json_params["gribi_mpls"]

    if args.delete:
        mpls_parse(mpls_path, op, show)
        routes_parse(routes, op, show)
        nhgs_parse(nh_groups, op, show)
        nhs_parse(nhs, op, show)

    else:
        nhs_parse(nhs, op, show)
        nhgs_parse(nh_groups, op, show)
        routes_parse(routes, op, show)
        mpls_parse(mpls_path, op, show)

    tearDownModule()

if __name__ == '__main__':
    main()
