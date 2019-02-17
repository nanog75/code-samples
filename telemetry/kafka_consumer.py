#!/usr/bin/env python
import json
from kafka import KafkaConsumer

class Consumer():
    def run(self):
        consumer = KafkaConsumer(bootstrap_servers='100.96.0.22:9092',
                                 auto_offset_reset='largest', 
                                 enable_auto_commit=True)
        consumer.subscribe(['gnmi-telemetry'])

        for message in consumer:
                print(json.loads(message.value))

def main():
    consumer =  Consumer()
    consumer.run()


if __name__ == "__main__":
    main()

