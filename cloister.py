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
    parser.add_option('-c', '--config_file', type=str,
                      help='Cloister configuration file name')

    (opts, args) = parser.parse_args()
    if len(args) != 1:
        print('Must specify a Cloister command.')
        exit(1)
    else:
        (action,) = args

    conf_file = default_config_file
    if opts.config_file != None:
        conf_file = opts.config_file
    conf = CloisterConfig(read_config(conf_file))
    
    try:
        client = boto3.resource('ec2', region_name=conf.region)
    except Exception as e:
        print >> stderr, (e)
        sys.exit(1)

    if conf.ami == 'latest':
        try:
            conf.get_latest_clamor_ami(client, conf.ami_tag)
        except AttributeError as e:
            conf.get_latest_clamor_ami(client)
            
    if action == 'login':
        try:
            master_name = read_ips(conf.master_file)[0]
        except Exception as e:
            print(e, 'Unable to read master IP file')
            exit(1)
            
        login(master_name, conf.key_pair, conf.user)
    elif action == 'login-ami':
        login(conf.ami_instance_ip, conf.key_pair, conf.user)
    elif action == 'launch':
        cluster = Cluster.get_cluster_if_exists(client, conf, conf.cluster_name)
        if cluster is None:
            cluster = Cluster.create_new_cluster(client, conf, conf.cluster_name)
    elif action == 'destroy':
        cluster = Cluster.get_cluster_if_exists(client, conf, conf.cluster_name)
        if cluster is not None:
            cluster.destroy()
        else:
            print('No cluster found')
    elif action == 'copy-dns':
        cluster = Cluster.get_cluster_if_exists(client, conf, conf.cluster_name) # creates cluster and copies names
        cluster.copy_all_dns_names()
        cluster.copy_key()
    elif action == 'copy-id-rsa':
        cluster = Cluster.get_cluster_if_exists(client, conf, conf.cluster_name) # creates cluster and copies names
        cluster.copy_id_rsa()
    else:
        print('Invalid action: ' + action)
        
if __name__ == '__main__':
    main()
