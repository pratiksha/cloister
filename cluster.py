import boto3 as boto

import time

import net_utils
import util

from instance import Instance
from security_groups import SecurityGroup as SG

class Cluster:
    def __init__(self, client, master_nodes, worker_nodes,
                 master_sgroup, worker_sgroup, name, conf):
        self.client = client
        self.master_nodes = master_nodes
        self.worker_nodes = worker_nodes
        self.master_sgroup = master_sgroup
        self.worker_sgroup = worker_sgroup
        self.name = name
        self.conf = conf

        Cluster.write_dns_names(self.master_nodes, 'servers/master.txt')
        Cluster.write_dns_names(self.master_nodes, 'servers/manager.txt')
        Cluster.write_dns_names(self.worker_nodes, 'servers/servers.txt')

        for instance in self.master_nodes + self.worker_nodes:
            self.copy_all_dns_names(instance)
        
    def copy_all_dns_names(self, instance):
        print('Copying master...')
        net_utils.copy_file(instance, self.conf, 'servers/master.txt', '~/cloister/servers/master.txt')
        print('Copying manager...')
        net_utils.copy_file(instance, self.conf, 'servers/manager.txt', '~/cloister/servers/manager.txt')
        print('Copying servers...')
        net_utils.copy_file(instance, self.conf, 'servers/servers.txt', '~/cloister/servers/servers.txt')
        print('...done.')
        
    @staticmethod
    def run_instances(client, config, cluster_name, master=False):
        nworkers = 1
        group_name = util.master_group_name(cluster_name)
        if not master:
            nworkers = config.nworkers
            group_name = util.worker_group_name(cluster_name)

        sgroup = SG.get_or_create_group(client, group_name)
        instances = client.create_instances(ImageId = config.ami,
                                      KeyName = config.identity_file,
                                      SecurityGroups = [group_name],
                                      InstanceType = config.instance_type,
                                      MinCount = nworkers,
                                      MaxCount = nworkers,
                                      TagSpecifications=[{
                                          'ResourceType':'instance',
                                          'Tags':[{'Key':'Name', 'Value':group_name}]
                                      }])

        # wait for instances to start up
        states = ([x.state['Name'] for x in instances])
        while any([x.state['Name'] != 'running' for x in instances]):
            print([x.state for x in instances])
            time.sleep(10)
            [x.reload() for x in instances]
        return (sgroup, instances)
        
    @staticmethod
    def write_dns_names(instances, outfile):
        open(outfile, 'w').close() # erases existing data
        for i in instances:
            # TODO check to make sure instance is running. For now, assume as precondition
            with open(outfile, 'a') as f:
                f.write(i.public_dns_name +'\n')

    @staticmethod
    def create_new_cluster(client, config, cluster_name):
        (master_sgroup, master_nodes) = Cluster.run_instances(client, config, cluster_name, True)
        (worker_sgroup, worker_nodes) = Cluster.run_instances(client, config, cluster_name, False)
        return Cluster(client, master_nodes, worker_nodes,
                       master_sgroup, worker_sgroup, cluster_name, config)
        
    @staticmethod
    def get_cluster_if_exists(client, config, cluster_name):
        print("Searching for existing cluster " + cluster_name + "...")
        instances = client.instances.all()
        master_nodes = []
        worker_nodes = []
        master_sgroup = SG.get_or_create_group(client, util.master_group_name(cluster_name))
        worker_sgroup = SG.get_or_create_group(client, util.worker_group_name(cluster_name))

        print(list(x.state for x in instances))
        active_instances = filter(lambda x: x.state['Name'] in Instance.active_states, instances)
        for i in active_instances:
            print(i.security_groups)
            group_names = [x['GroupName'] for x in i.security_groups]
            if master_sgroup.group_name in group_names:
                master_nodes.append(i)
            elif worker_sgroup.group_name in group_names:
                worker_nodes.append(i)
        if any((master_nodes, worker_nodes)):
            print ("Found %d master(s), %d workers" %
                   (len(master_nodes), len(worker_nodes)))
        if (master_nodes != [] and worker_nodes != []):
            return Cluster(client, master_nodes, worker_nodes,
                           master_sgroup, worker_sgroup, cluster_name, config)
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
