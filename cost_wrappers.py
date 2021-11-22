from optparse import OptionParser

import copy
import json
import subprocess

import boto3

from cluster import Cluster
from config import CloisterConfig
from security_groups import SecurityGroup

from net_utils import read_config

default_config_file = 'configs/cost_config.json'

'''
T3.micro has 2 CPUs and 0.5 GB of memory

input data spec: 
- data size (GB)
- data type?
- data location?
'''

class Dataset:
    def __init__(self, location, npartitions, datatype, size):
        self.location = location
        self.npartitions = npartitions
        self.datatype = datatype
        self.size = size # in number of elements

class CloudFunction:
    def __init__(self, base_config, script):
        self.script = script
        self.base_config = base_config

    def compute_configuration(self):
        pass

    def run(self, input_spec, output_spec, client):
        ## launch cluster
        ## adjust the number of workers based on input_spec
        config = self.compute_configuration(input_spec) # should return config with correct instance type and number of workers?
        print(config)
        
        cluster = Cluster.get_cluster_if_exists(client, config, config.cluster_name)
        if cluster is None:
            cluster = Cluster.create_new_cluster(client, config, config.cluster_name)

        ## load scripts
        ## TODO this is a hack
        cluster.copy_map_script()

        ## run map and save result
        ## run a binary that loads data from s3 (or local) and runs some function
        ## and save result to s3
        cmdline = self.script + " " + input_spec.location + " " + output_spec.location
        output_size = cluster.run_command(cmdline)

        ## tear down cluster
        cluster.destroy()

        output_spec.size = int(output_size)
        return output_spec

class MapFunction(CloudFunction):
    def __init__(self, base_config, script):
        super().__init__(base_config, script)
    
    ## this is where we figure out how many workers to launch for map
    def compute_configuration(self, input_spec):
        ret_config = copy.copy(self.base_config)
        ret_config.master_instance_type = 'm5.4xlarge'
        ret_config.instance_type = 'm5.4xlarge'
        ret_config.nworkers = 1
        return ret_config

def cluster_map(base_config, client):
    input_spec = Dataset('s3://weld-dsm-east/ints-tiny.csv',
                         1, int, 100)
    output_spec = Dataset('s3://weld-dsm-east/tiny-output.csv',
                         1, int, 100)
    func = MapFunction(base_config, '~/map.sh')
    func.run(input_spec, output_spec, client)
    
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

    cluster_map(conf, client)

if __name__ == '__main__':
    main()
