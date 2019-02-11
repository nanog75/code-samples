#!/bin/bash

python3 gribi_client.py -j r1.gribi.json -ip localhost -port 57777 -p -d 
python3 gribi_client.py -j r2.gribi.json -ip localhost -port 57778 -p -d
python3 gribi_client.py -j r3.gribi.json -ip localhost -port 57779 -p -d 
python3 gribi_client.py -j r4.gribi.json -ip localhost -port 57780 -p -d 
