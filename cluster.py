import boto3 as boto

import time
import os

import net_utils
import util

from instance import Instance
from security_groups import SecurityGroup as SG

class Cluster:
    def __init__(self, client, master_nodes, worker_nodes,
                 master_sgroup, worker_sgroup, name, conf, copy_dns=False):
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
        Cluster.write_private_ips(self.worker_nodes, 'servers/servers_private.txt')
        Cluster.write_public_ips(self.worker_nodes, 'servers/servers_public.txt')

        if copy_dns:
            self.copy_all_dns_names()
            self.copy_key()

    def download_logs(self, bench_name, timestamp):
        folder_name = 'logs_' + bench_name + '_' + timestamp + '/'
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        prefix = '~/clamor/experiments/cpp/' + bench_name + '/'
            
        for instance in self.worker_nodes:
            subfolder_name = 'logs_' + bench_name + '_' + timestamp + '/' + instance.public_dns_name + '/'
            if not os.path.exists(subfolder_name):
                os.makedirs(subfolder_name)
            try:
                files = net_utils.run_cmdline(instance.public_dns_name,
                                              'ls ' + prefix + '*_' + timestamp + '\.log',
                                              self.conf.key_pair)
                print(files)
                net_utils.copy_remote_file(instance, self.conf, subfolder_name, prefix + '*_' + timestamp + '\.log')
            except:
                continue
                
        # Master/manager may not have exactly the same timestamp
        for instance in self.master_nodes:
            files = net_utils.run_cmdline(instance.public_dns_name,
                                          'ls ' + prefix + '*_' + timestamp + '\.log',
                                          self.conf.key_pair)
            files = net_utils.run_cmdline(instance.public_dns_name,
                                          'ls -tr ' + prefix + '*.log | tail -2',
                                          self.conf.key_pair)
            s = ''.join(files)
            files = s.strip().split('\n')
            for f in files:
                net_utils.copy_remote_file(instance, self.conf, folder_name, f)                

    def erase_logs(self, bench_name, timestamp):
        folder_name = 'logs_' + bench_name + '_' + timestamp + '/'
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        prefix = '~/clamor/experiments/cpp/' + bench_name + '/'
            
        for instance in self.worker_nodes:
            subfolder_name = 'logs_' + bench_name + '_' + timestamp + '/' + instance.public_dns_name + '/'
            if not os.path.exists(subfolder_name):
                os.makedirs(subfolder_name)
            try:
                files = net_utils.run_cmdline(instance.public_dns_name,
                                              'rm -rf ' + prefix + '*_' + timestamp + '\.log',
                                              self.conf.key_pair)
                print(files)
            except:
                continue
                
        # Master/manager may not have exactly the same timestamp
        for instance in self.master_nodes:
            files = net_utils.run_cmdline(instance.public_dns_name,
                                          'rm -rf ' + prefix + '*_' + timestamp + '\.log',
                                          self.conf.key_pair)
            #files = net_utils.run_cmdline(instance.public_dns_name,
            #                              'ls -tr ' + prefix + '*.log | tail -2',
            #                              self.conf.key_pair)

    def erase_all_logs(self, bench_name):
        prefix = '~/clamor/experiments/cpp/' + bench_name + '/'
            
        for instance in self.worker_nodes:
            try:
                files = net_utils.run_cmdline(instance.public_dns_name,
                                              'rm -rf ' + prefix + '*\.log',
                                              self.conf.key_pair)
                print(files)
            except:
                continue
                
        # Master/manager may not have exactly the same timestamp
        for instance in self.master_nodes:
            files = net_utils.run_cmdline(instance.public_dns_name,
                                          'rm -rf ' + prefix + '*\.log',
                                          self.conf.key_pair)
            #files = net_utils.run_cmdline(instance.public_dns_name,
            #                              'ls -tr ' + prefix + '*.log | tail -2',
            #                              self.conf.key_pair)
            
    def redeploy(self):
        folders = ['clamor/', 'weld/', 'cloister/', 'cost-benchmarks/', '.bashrc']
        idx = 0
        for instance in self.master_nodes + self.worker_nodes:
            if idx % 2 == 0:
                time.sleep(3) # avoid ssh errors
            idx += 1
            for folder in folders:
                print('rsync to %s' % instance.public_dns_name)
                net_utils.rsync(self.conf.ami_instance_ip,
                                instance.public_dns_name,
                                self.conf.key_pair,
                                self.conf.user,
                                folder, delete=False)

    def load_tpch_data(self):
        files = ['lineitem_large', 'order_large', 'part_large', 'supplier_large']
        cmd = 'wget https://weld-dsm-east.s3.amazonaws.com/%s -P /home/ubuntu/clamor/baselines/tpch_data/' 
        for f in files:
            self.run_command(cmd % f)

    def load_data(self, data_spec, load_dir):
        nworkers = len(self.worker_nodes)
        for i in range(nworkers): # actually what we want is to distribute partitions across workers.
            cmd = 'wget %s/%s -P %s' % (data_spec.location, i, load_dir)
            self.run_command(cmd)
            
    def run_command(self, command):
        for instance in self.master_nodes + self.worker_nodes:
            print(instance.public_dns_name)
            net_utils.run_cmdline_nonblock(instance.public_dns_name,
                                           command,
                                           self.conf.key_pair)
                
    def copy_all_dns_names(self):
        for instance in self.master_nodes + self.worker_nodes:
            print('Copying master...')
            net_utils.copy_file(instance, self.conf, 'servers/master.txt', '~/cloister/servers/master.txt', nonblock=True)
            print('Copying manager...')
            net_utils.copy_file(instance, self.conf, 'servers/manager.txt', '~/cloister/servers/manager.txt', nonblock=True)
            print('Copying servers...')
            net_utils.copy_file(instance, self.conf, 'servers/servers.txt', '~/cloister/servers/servers.txt', nonblock=True)
            print('...done.')
            net_utils.copy_file(instance, self.conf, 'servers/servers_private.txt', '~/cloister/servers/servers_private.txt', nonblock=True)
            print('...done.')
            net_utils.copy_file(instance, self.conf, 'servers/servers_public.txt', '~/cloister/servers/servers_public.txt', nonblock=True)
            print('...done.')

    def copy_key(self):
        for instance in self.master_nodes:
            net_utils.copy_file(instance, self.conf, self.conf.key_pair, '~/cloister/' + self.conf.key_pair)

    def copy_id_rsa(self):
        for instance in self.worker_nodes:
            net_utils.copy_file(instance, self.conf, '/home/ubuntu/.ssh/id_rsa.pub', '~/cloister/master_key.pub')
            net_utils.run_cmdline(instance.public_dns_name,
                                  "cat ~/cloister/master_key.pub >> ~/.ssh/authorized_keys",
                                  self.conf.key_pair)

    def attach_swap(self):
        swap_size = self.conf.swap_size_master
        master_id = self.master_nodes[0].id
        zone = self.master_nodes[0].placement['AvailabilityZone']
        print(zone)
        volume = self.client.create_volume(
            AvailabilityZone=zone,
            Encrypted=False,
            Size=swap_size
        )

        while volume.state != 'available':
            print(volume.state)
            time.sleep(1)
            volume.reload()
            
        response= self.master_nodes[0].attach_volume(
            Device='/dev/sdf',
            VolumeId=volume.id,
        )

        print(response)
            
    @staticmethod
    def run_instances(client, config, cluster_name, master=False):
        nworkers = 1
        group_name = util.master_group_name(cluster_name)
        if not master:
            nworkers = config.nworkers
            group_name = util.worker_group_name(cluster_name)

        imgs = list(client.images.filter(ImageIds=[config.ami]));
        device_name = imgs[0].root_device_name
            
        sgroup = SG.get_or_create_group(client, group_name)
        if master and config.master_instance_type:
            instance_type = config.master_instance_type
        else:
            instance_type = config.instance_type

        device_mappings = [{"DeviceName": device_name,
                            "Ebs" :
                            { "VolumeSize" : config.root_size }}]
        instances = client.create_instances(ImageId = config.ami,
                                            KeyName = config.identity_file,
                                            SecurityGroups = [group_name],
                                            InstanceType = instance_type,
                                            MinCount = nworkers,
                                            MaxCount = nworkers,
                                            BlockDeviceMappings=device_mappings,
                                            Placement={
                                                #'AvailabilityZone':config.region,
                                                'GroupName':'clamor',
                                            },
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
    def write_private_ips(instances, outfile):
        open(outfile, 'w').close()
        for i in instances:
            with open(outfile, 'a') as f:
                f.write(i.private_ip_address + '\n')

    @staticmethod
    def write_public_ips(instances, outfile):
        open(outfile, 'w').close()
        for i in instances:
            with open(outfile, 'a') as f:
                f.write(i.public_ip_address + '\n')
                
    @staticmethod
    def create_new_cluster(client, config, cluster_name):
        (master_sgroup, master_nodes) = Cluster.run_instances(client, config, cluster_name, True)
        (worker_sgroup, worker_nodes) = Cluster.run_instances(client, config, cluster_name, False)
        return Cluster(client, master_nodes, worker_nodes,
                       master_sgroup, worker_sgroup, cluster_name, config, copy_dns=True)
        
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
                           master_sgroup, worker_sgroup, cluster_name, config, copy_dns=False)
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
