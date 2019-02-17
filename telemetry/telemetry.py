#!/usr/bin/env python
import pdb
import json

#import logging
#logger = logging.getLogger("ydk")
#logger.setLevel(logging.INFO)
#handler = logging.StreamHandler()
#formatter = logging.Formatter(("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
#handler.setFormatter(formatter)
#logger.addHandler(handler)
import time

from ydk.models.openconfig import openconfig_interfaces
from ydk.models.openconfig import openconfig_network_instance
from ydk.path import Repository
from ydk.gnmi.providers import gNMIServiceProvider
from ydk.gnmi.services import gNMIService
from ydk.gnmi.services import gNMISubscription
from ydk.filters import YFilter
import pdb, sys
import json
import grpc
from gnmi_pb2 import SubscribeResponse

from google.protobuf import text_format
from google.protobuf.json_format import MessageToJson
from kafka import KafkaConsumer, KafkaProducer

producer = KafkaProducer(bootstrap_servers='100.96.0.22:9092')

# Callback function to handle telemetry data
def push_to_kafka(var):
    response = SubscribeResponse()
    text_format.Parse(var, response)
    jsonResponse = MessageToJson(response)
    producer.send('gnmi-telemetry', json.dumps(jsonResponse).encode('utf-8'))


# Function to subscribe to telemetry data
def subscribe(func):
    gnmi = gNMIService()

    try:
        try:
            #Running on dev1 environment of tesuto cloud setup for Nanog75
            repository = Repository('/home/tesuto/yang/')
        except:
            #Running in a docker container started off image akshshar/nanog75-telemetry
            repository = Repository('/root/yang/')
    except Exception as e:
        print("Failed to import yang models, check repository path,  aborting....")
        sys.exit(1)

    provider = gNMIServiceProvider(repo=repository, address='100.96.0.14', port=57777, username='rtrdev', password='nanog75sf')

    # The below will create a telemetry subscription path 'openconfig-interfaces:interfaces/interface'
    interfaces = openconfig_interfaces.Interfaces()
    interface = openconfig_interfaces.Interfaces.Interface()
    interfaces.interface.append(interface)

    network_instances = openconfig_network_instance.NetworkInstances()


    subscription = gNMISubscription()
    subscription.entity = interfaces #network_instances

    subscription.subscription_mode = "SAMPLE";
    subscription.sample_interval = 10* 1000000000;
    subscription.suppress_redundant = False;
    subscription.heartbeat_interval = 100 * 1000000000;

    # Subscribe for updates in STREAM mode.
    var = gnmi.subscribe(provider, subscription, 10, "STREAM", "PROTO", func)


if __name__ == "__main__":
    subscribe(push_to_kafka)

