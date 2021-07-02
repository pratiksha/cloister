#!/usr/bin/python3
from optparse import OptionParser

import json
import subprocess

import boto3

from cluster import Cluster
from config import CloisterConfig
from security_groups import SecurityGroup

default_config_file = 'configs/ps_config.json'

from net_utils import *

def login(host, identity_file, user):
    ssh(host, identity_file, user)

def main():
    parser = OptionParser()
    parser.add_option('-c', '--config_file', type=str,
                      help='Cloister configuration file name')
    parser.add_option('-l', '--cluster_label', type=str,
                      help='Cluster name override')
    parser.add_option('-n', '--nworkers', type=str,
                      help='Cluster size override')

    (opts, args) = parser.parse_args()
    if len(args) < 1:
        
        print('Must specify a Cloister command.')
        exit(1)
    elif len(args) == 1:
        (action,) = args
    elif len(args) > 1:
        action = args[0]
        args = args[1:]

    conf_file = default_config_file
    if opts.config_file != None:
        conf_file = opts.config_file
    conf = CloisterConfig(read_config(conf_file))

    if opts.cluster_label != None:
        conf.cluster_name = opts.cluster_label
        conf.ami_tag = opts.cluster_label

    if opts.nworkers != None:
        conf.nworkers = int(opts.nworkers)
        
    print(conf)
        
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
    elif action == 'load-tpch':
        cluster = Cluster.get_cluster_if_exists(client, conf, conf.cluster_name) # creates cluster and copies names
        cluster.load_tpch_data()
    elif action == 'attach-swap':
        cluster = Cluster.get_cluster_if_exists(client, conf, conf.cluster_name) # creates cluster and copies names
        cluster.attach_swap()
    elif action == 'run-command':
        cluster = Cluster.get_cluster_if_exists(client, conf, conf.cluster_name) # creates cluster and copies names
        cluster.run_command(args[0])
    elif action == 'copy-dns':
        cluster = Cluster.get_cluster_if_exists(client, conf, conf.cluster_name) # creates cluster and copies names
        cluster.copy_all_dns_names()
        cluster.copy_key()
    elif action == 'copy-id-rsa':
        cluster = Cluster.get_cluster_if_exists(client, conf, conf.cluster_name) # creates cluster and copies names
        cluster.copy_id_rsa()
    elif action == 'redeploy':
        # rsync all files from ami instance to cluster.
        cluster = Cluster.get_cluster_if_exists(client, conf, conf.cluster_name) # creates cluster and copies names
        cluster.redeploy()
    elif action == 'download-logs':
        cluster = Cluster.get_cluster_if_exists(client, conf, conf.cluster_name) # creates cluster and copies names
        bench_name = args[0]
        timestamp = args[1]
        cluster.download_logs(bench_name, timestamp)
    elif action == 'erase-logs':
        cluster = Cluster.get_cluster_if_exists(client, conf, conf.cluster_name) # creates cluster and copies names
        bench_name = args[0]
        timestamp = args[1]
        cluster.erase_logs(bench_name, timestamp)
    elif action == 'erase-all-logs':
        cluster = Cluster.get_cluster_if_exists(client, conf, conf.cluster_name) # creates cluster and copies names
        bench_name = args[0]
        cluster.erase_all_logs(bench_name)
    else:
        print('Invalid action: ' + action)
        
if __name__ == '__main__':
    main()
