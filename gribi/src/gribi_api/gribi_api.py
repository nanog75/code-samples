#
# Copyright (c) 2016 by cisco Systems, Inc.
# All rights reserved.
#
import abc
import os
import ipaddress
import pdb
import pprint

#from . import serializers
from binascii import hexlify, unhexlify
import time
import struct

from genpy import gribi_pb2
from genpy import gribi_aft_pb2
from genpy import enums_pb2
from genpy import ywrapper_pb2

import grpc

def byte_to_mac_str(mac):
    num = 2
    mac_split = [ str[start:start+num] for start in range(0, len(str), num) ]
    result = ''
    for substr in mac_split:
        result = result + elem + ':'
    return result[:-1]

class Operation(object):
    ADD = 1
    UPDATE = 2
    DELETE = 3

class AbstractClient(object, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def gribi_op_routes(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    def gribi_op_nh_group(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    def gribi_op_nh(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    def gribi_op_mpls(self, *args, **kwargs):
        pass

class GrpcClient(AbstractClient):
    TIMEOUT_SECONDS = 20

    def __init__(self, host, port, channel_credentials=None):
        if channel_credentials is None:
            # Instantiate insecure channel object.
            channel = grpc.insecure_channel(str(host)+":"+str(port))
        else:
            # Instantiate secure channel object.
            channel = grpc.secure_channel(str(host)+":"+str(port),
                                                     channel_credentials)
        #self._stub = gribi_pb2.beta_create_gRIBI_stub(channel)
        self._stub = gribi_pb2.gRIBIStub(channel)


    def gribi_op_routes(self, routes, op, show = False):
        success = True
        gribi_msgs = gen_gribi_route_msgs(routes, op, show)

        responses = self._stub.Modify(gribi_msgs, self.TIMEOUT_SECONDS)
        try:
            for response in responses:
                for result in response.result:
                    if result.status != 1:
                        success = False
        except Exception as err:
            print(("Exception Received:", str(err)))
        return responses, success

    def gribi_op_mpls(self, routes, op, show = False):
        success = True
        gribi_msgs = gen_gribi_mpls_msgs(routes, op, show)

        responses = self._stub.Modify(gribi_msgs, self.TIMEOUT_SECONDS)
        try:
            for response in responses:
                print ("Got a response!")
                print (response)
                for result in response.result:
                    if result.status != 1:
                        success = False
        except Exception as err:
            print(("Exception Received:", str(err)))
        return responses, success

    def gribi_op_nh_group(self, nh_groups, op, show = False):
        success = True
        gribi_msgs = gen_gribi_nh_group_msgs(nh_groups, op, show)

        responses = self._stub.Modify(gribi_msgs, self.TIMEOUT_SECONDS)
        try:
            for response in responses:
                for result in response.result:
                    if result.status != 1:
                        success = False
        except Exception as err:
            print(("Exception Received:", str(err)))
        return responses, success

    def gribi_op_nh(self, nhs, op, show = False):
        success = True
        gribi_msgs = gen_gribi_nh_msgs(nhs, op, show)

        responses = self._stub.Modify(gribi_msgs, self.TIMEOUT_SECONDS)
        try:
            for response in responses:
                for result in response.result:
                    if result.status != 1:
                        success = False
        except Exception as err:
            print(("Exception Received:", str(err)))
        return responses, success

def gen_gribi_route_msgs(routes, op, show):
    for route in routes:
        encap_header = getattr(enums_pb2, route["entry"]["encap_header_type"])

        parent_message = gribi_pb2.ModifyRequest()
        aft = gribi_pb2.AFTOperation()
        aft.id = route["id"]
        aft.network_instance = route["inst_name"]
        aft.op = op
        aft_entry_key = {
            "v4": gribi_aft_pb2.Afts.Ipv4EntryKey(),
            "v6": gribi_aft_pb2.Afts.Ipv6EntryKey(),
        }[route["entry"]["type"]]
        aft_entry_key.prefix = route["entry"]["prefix"]
        aft_entry = {
            "v4": gribi_aft_pb2.Afts.Ipv4Entry(),
            "v6": gribi_aft_pb2.Afts.Ipv6Entry(),
        }[route["entry"]["type"]]

        aft_entry.decapsulate_header = encap_header

        aft_nh_group = ywrapper_pb2.UintValue()
        aft_nh_group.value = route["entry"]["next_hop_group"]

        aft_octets_forwarded = ywrapper_pb2.UintValue()
        aft_octets_forwarded.value = route["entry"]["octets_forwarded"]

        aft_packets_forwarded = ywrapper_pb2.UintValue()
        aft_packets_forwarded.value = route["entry"]["packets_forwarded"]

        aft_entry.next_hop_group.CopyFrom(aft_nh_group)
        aft_entry.octets_forwarded.CopyFrom(aft_octets_forwarded)
        aft_entry.packets_forwarded.CopyFrom(aft_packets_forwarded)
        if route["entry"]["type"] == "v4":
             aft_entry_key.ipv4_entry.CopyFrom(aft_entry)
             aft.ipv4.CopyFrom(aft_entry_key)
        elif route["entry"]["type"] == "v6":
             aft_entry_key.ipv6_entry.CopyFrom(aft_entry)
             aft.ipv6.CopyFrom(aft_entry_key)
        else:
            print ("Not a v4 or v6 route.")
            print (route["entry"]["type"])

        parent_message.operation.extend([aft])

        if show:
            print (parent_message)

        yield parent_message

def gen_gribi_mpls_msgs(mpls_routes, op, show):
    for mpls_route in mpls_routes:
        mpls_label = 0
        if type(mpls_route["label"]) is int:
            mpls_label = mpls_route["label"]
        else:
            mpls_label = getattr(gribi_aft_pb2.Afts.LabelEntryKey, mpls_route["label"])
        #mpls_label = getattr(gribi_aft_pb2.Afts.LabelEntryKey, mpls_route["label"])
        parent_message = gribi_pb2.ModifyRequest()
        aft = gribi_pb2.AFTOperation()
        aft.op = op
        aft.id = mpls_route["id"]
        aft.network_instance = mpls_route["inst_name"]

        aft_entry_key = gribi_aft_pb2.Afts.LabelEntryKey()
        aft_entry_key.label_uint64 = mpls_label

        aft_entry = gribi_aft_pb2.Afts.LabelEntry()

        aft_popped_mpls_stack = []
        for elem in mpls_route["entry"]["popped_mpls_label_stack"]:
            aft_curr_label = gribi_aft_pb2.Afts.LabelEntry.PoppedMplsLabelStackUnion()
            aft_curr_label_enum = 0

            if type(elem) is int:
                aft_curr_label_enum = elem
            else:
                aft_curr_label_enum = getattr(gribi_aft_pb2.Afts.LabelEntry, elem)

            aft_curr_label.popped_mpls_label_stack_uint64 = aft_curr_label_enum
            aft_popped_mpls_stack.append(aft_curr_label)

        aft_nh_group = ywrapper_pb2.UintValue()
        aft_nh_group.value = mpls_route["entry"]["nh_group"]

        aft_octets_forwarded = ywrapper_pb2.UintValue()
        aft_octets_forwarded.value = mpls_route["entry"]["octets_forwarded"]

        aft_packets_forwarded = ywrapper_pb2.UintValue()
        aft_packets_forwarded.value = mpls_route["entry"]["packets_forwarded"]
        aft_entry.next_hop_group.CopyFrom(aft_nh_group)
        aft_entry.octets_forwarded.CopyFrom(aft_octets_forwarded)
        aft_entry.packets_forwarded.CopyFrom(aft_packets_forwarded)

        aft_entry.popped_mpls_label_stack.extend(aft_popped_mpls_stack)
        aft_entry_key.label_entry.CopyFrom(aft_entry)
        aft.mpls.CopyFrom(aft_entry_key)
        parent_message.operation.extend([aft])

        if show:
            print (parent_message)

        yield parent_message

def gen_gribi_nh_group_msgs(nh_groups, op, show):
    for nh_group in nh_groups:
        parent_message = gribi_pb2.ModifyRequest()
        aft = gribi_pb2.AFTOperation()
        aft.op = op
        aft.id = nh_group["id"]
        aft.network_instance = nh_group["inst_name"]

        aft_entry_key = gribi_aft_pb2.Afts.NextHopGroupKey()
        aft_entry_key.id = nh_group["key_id"]

        aft_nh_group = gribi_aft_pb2.Afts.NextHopGroup()

        aft_backup_nh_group = ywrapper_pb2.UintValue()
        aft_backup_nh_group.value = nh_group["entry"]["backup_nh_group"]

        aft_color = ywrapper_pb2.UintValue()
        aft_color.value = nh_group["entry"]["color"]

        aft_nh_key_arr = []
        for nh_key in nh_group["entry"]["nh_keys"]:

            aft_nh_key = gribi_aft_pb2.Afts.NextHopGroup.NextHopKey()
            aft_nh_key.index = nh_key["key_index"]

            aft_nh = gribi_aft_pb2.Afts.NextHopGroup.NextHop()
            aft_nh_weight = ywrapper_pb2.UintValue()
            aft_nh_weight.value = nh_key["nh_weight"]
            aft_nh_key.next_hop.CopyFrom(aft_nh)
            aft_nh_key_arr.append(aft_nh_key)

        aft_nh_group.backup_next_hop_group.CopyFrom(aft_backup_nh_group)
        aft_nh_group.color.CopyFrom(aft_color)
        aft_nh_group.next_hop.extend(aft_nh_key_arr)
        aft_entry_key.next_hop_group.CopyFrom(aft_nh_group)
        aft.next_hop_group.CopyFrom(aft_entry_key)
        parent_message.operation.extend([aft])

        if show:
            print (parent_message)

        yield parent_message

def gen_gribi_nh_msgs(nhs, op, show):
    for nh in nhs:
        encap_header = getattr(enums_pb2, nh["entry"]["encap_header_type"])
        origin_protocol = getattr(enums_pb2, nh["entry"]["origin_protocol"])

        parent_message = gribi_pb2.ModifyRequest()
        aft = gribi_pb2.AFTOperation()
        aft.op = op
        aft.id = nh["id"]
        aft.network_instance = nh["inst_name"]

        aft_entry_key = gribi_aft_pb2.Afts.NextHopKey()
        aft_entry_key.index = nh["key_index"]

        aft_nh = gribi_aft_pb2.Afts.NextHop()

        aft_nh.encapsulate_header = encap_header
        aft_nh.origin_protocol = origin_protocol

        aft_push_label_arr = []
        for elem in nh["entry"]["pushed_mpls_label_stack"]:
            aft_curr_label = gribi_aft_pb2.Afts.NextHop.PushedMplsLabelStackUnion()
            aft_curr_label_enum = 0
            if type(elem) is int:
                aft_curr_label_enum = elem
            else:
                aft_curr_label_enum = getattr(gribi_aft_pb2.Afts.NextHop, elem)

            aft_curr_label.pushed_mpls_label_stack_uint64 = aft_curr_label_enum
            aft_push_label_arr.append(aft_curr_label)

        aft_nh_int_ref = gribi_aft_pb2.Afts.NextHop.InterfaceRef()
        aft_nh_int_ref_int = ywrapper_pb2.StringValue()
        aft_nh_int_ref_int.value = nh["entry"]["int"]
        aft_nh_int_ref_subint = ywrapper_pb2.UintValue()
        aft_nh_int_ref_subint.value = nh["entry"]["subint"]

        aft_nh_ip = ywrapper_pb2.StringValue()
        aft_nh_ip.value = nh["entry"]["ip_address"]
        aft_nh_mac = ywrapper_pb2.StringValue()
        aft_nh_mac.value = nh["entry"]["mac_address"]

        aft_nh_int_ref.interface.CopyFrom(aft_nh_int_ref_int)
        aft_nh_int_ref.subinterface.CopyFrom(aft_nh_int_ref_subint)
        aft_nh.interface_ref.CopyFrom(aft_nh_int_ref)
        aft_nh.ip_address.CopyFrom(aft_nh_ip)
        aft_nh.mac_address.CopyFrom(aft_nh_mac)

        aft_nh.pushed_mpls_label_stack.extend(aft_push_label_arr)
        aft_entry_key.next_hop.CopyFrom(aft_nh)
        aft.next_hop.CopyFrom(aft_entry_key)
        parent_message.operation.extend([aft])

        if show:
            print (parent_message)

        yield parent_message
