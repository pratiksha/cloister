#!/bin/bash
ssh-keygen
python gen_mpi_hosts.py
pip3 install boto3
python3 cloister.py copy-id-rsa -c configs/clamor_config_east.json -l cost
./add_hosts.sh
