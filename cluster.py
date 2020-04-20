import boto3 as boto

import time

import util

from instance import Instance
from security_groups import SecurityGroup as SG

class Cluster:
    def __init__(self, client, master_nodes, worker_nodes,
                 master_sgroup, worker_sgroup, name):
        self.client = client
        self.master_nodes = master_nodes
        self.worker_nodes = worker_nodes
        self.master_sgroup = master_sgroup
        self.worker_sgroup = worker_sgroup
        self.name = name

    @staticmethod
    def run_instances(client, config, cluster_name, master=False):
        nworkers = 1
        group_name = util.master_group_name(cluster_name)
        if not master:
            nworkers = config.nworkers
            group_name = util.worker_group_name(cluster_name)

        sgroup = SG.get_or_create_group(client, group_name)
        instances = client.create_instances(ImageId = config.ami,
                                      KeyName = config.key_pair,
                                      SecurityGroups = [group_name],
                                      InstanceType = config.instance_type,
                                      MinCount = nworkers,
                                      MaxCount = nworkers,
                                      TagSpecifications=[{
                                          'ResourceType':'instance',
                                          'Tags':[{'Key':'Name', 'Value':group_name}]
                                      }])
        return (sgroup, instances)
        
    @staticmethod
    def create_new_cluster(client, config, cluster_name):
        (master_sgroup, master_nodes) = Cluster.run_instances(client, config, cluster_name, True)
        (worker_sgroup, worker_nodes) = Cluster.run_instances(client, config, cluster_name, False)
        return Cluster(client, master_nodes, worker_nodes,
                       master_sgroup, worker_sgroup, cluster_name)
        
    @staticmethod
    def get_cluster_if_exists(client, cluster_name):
        print("Searching for existing cluster " + cluster_name + "...")
        instances = client.instances.all()
        master_nodes = []
        worker_nodes = []
        master_sgroup = SG.get_or_create_group(client, util.master_group_name(cluster_name))
        worker_sgroup = SG.get_or_create_group(client, util.worker_group_name(cluster_name))

        active_instances = filter(lambda x: x.state in Instance.active_states, instances)
        for i in active_instances:
            group_name = i.security_groups[0].group_name
            if group_name == master_sgroup.name:
                master_nodes.append(i)
            elif group_name == worker_sgroup.name:
                worker_nodes.append(i)
        if any((master_nodes, worker_nodes)):
            print ("Found %d master(s), %d workers" %
                   (len(master_nodes), len(worker_nodes)))
        if (master_nodes != [] and worker_nodes != []):
            return Cluster(client, master_nodes, worker_nodes,
                           master_sgroup, worker_sgroup, cluster_name)
        else:
            if master_nodes == [] and worker_nodes != []:
                print("ERROR: Could not find master in group " + cluster_name + "-master")
            elif master_nodes != [] and worker_nodes == []:
                print("ERROR: Could not find workers in group " + cluster_name + "-workers")
            else:
                print("ERROR: Could not find any existing cluster")
            return None

    def destroy(self):
        print('Terminating...')

        [x.terminate() for x in self.master_nodes + self.worker_nodes]

        # wait for instances to terminate
        states = ([x.state['Name'] for x in self.master_nodes + self.worker_nodes])
        while any([x.state['Name'] in Instance.active_states + Instance.waiting_states
                   for x in self.master_nodes + self.worker_nodes]):
            print([x.state for x in self.master_nodes + self.worker_nodes])
            time.sleep(10)
            [x.reload() for x in self.master_nodes + self.worker_nodes]

        print('done.')
        SG.revoke(self.master_sgroup, self.client)
        SG.revoke(self.worker_sgroup, self.client)

        self.master_sgroup.delete()
        self.worker_sgroup.delete()
