#!/usr/bin/python3
from optparse import OptionParser

import json
import subprocess

import boto3

from cluster import Cluster
from config import CloisterConfig
from security_groups import SecurityGroup

default_config_file = 'clamor_config_east.json'

from net_utils import *

def login(host, identity_file, user):
    ssh(host, identity_file, user)

def main():
    parser = OptionParser()

    (opts, args) = parser.parse_args()
    action = None
    if len(args) > 0:
        (action,) = args
        
    conf = CloisterConfig(read_config(default_config_file))
    print(conf)
    
    server_names = read_ips(conf.servers_file)
    master_name = read_ips(conf.master_file)[0]

    try:
        client = boto3.resource('ec2', region_name=conf.region)
    except Exception as e:
        print >> stderr, (e)
        sys.exit(1)

    if action == 'login':
        login(master_name, conf.key_pair, conf.user)
    elif action == 'login-ami':
        login(conf.ami_instance_ip, conf.key_pair, conf.user)
    elif action == 'launch':
        cluster = Cluster.get_cluster_if_exists(client, conf.cluster_name)
        if cluster is None:
            cluster = Cluster.create_new_cluster(client, conf, conf.cluster_name)
    elif action == 'destroy':
        cluster = Cluster.get_cluster_if_exists(client, conf.cluster_name)
        if cluster is not None:
            cluster.destroy()
        else:
            print('No cluster found')
        
if __name__ == '__main__':
    main()
