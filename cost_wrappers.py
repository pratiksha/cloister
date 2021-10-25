from optparse import OptionParser

import json
import subprocess

import boto3

from cluster import Cluster
from config import CloisterConfig
from security_groups import SecurityGroup

'''
T3.micro has 2 CPUs and 0.5 GB of memory

input data spec: 
- data size (GB)
- data type?
- data location?
'''

class Dataset:
    def __init__(self, location, npartitions, size):
        self.location = location
        self.npartitions = npartitions
        self.size = size # in GB

class CloudFunction:
    def __init__(self, config, input_spec, output_spec):
        self.config = config
        self.input_spec = input_spec
        self.output_spec = output_spec

    def compute_configuration(self):
        pass

    def run(self):
        ## launch cluster
        ## adjust the number of workers based on input_spec
        new_config = compute_map_configuration(config, input_spec) # should return config with correct instance type and number of workers?

        cluster = Cluster.get_cluster_if_exists(client, config, config.cluster_name)
        if cluster is None:
            cluster = Cluster.create_new_cluster(client, config, config.cluster_name)

        ## load data
        cluster.load_data(input_spec)

        ## run map and save result
        cluster.run_function(script, output_dir)

        ## tear down cluster


def MapFunction(CloudFunction):
    ## this is where we figure out how many workers to launch for map
    def compute_configuration(self):
        pass
        
def main():
    parser = OptionParser()
    parser.add_option('-c', '--config_file', type=str,
                      help='Cloister configuration file name')
    parser.add_option('-l', '--cluster_label', type=str,
                      help='Cluster name override')

    (opts, args) = parser.parse_args()

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

    input_spec = None
    output_spec = None
    cluster_map(conf, input_spec, output_spec)

if __name__ == '__main__':
    main()
