#!/bin/bash

python3 ../gribi_client.py -j r1.gribi.json -ip 100.96.0.14 -port 57777 -p -d 
python3 ../gribi_client.py -j r3.gribi.json -ip 100.96.0.18 -port 57777 -p -d
python3 ../gribi_client.py -j r4.gribi.json -ip 100.96.0.26 -port 57777 -p -d
