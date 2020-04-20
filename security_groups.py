import util

import boto3 as boto

class SecurityGroup:
    cluster_permissions = [{'IpProtocol': 'tcp',
                            'FromPort': 22,
                            'ToPort': 22,
                            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                           {'IpProtocol': 'tcp',
                            'FromPort': 8080,
                            'ToPort': 8081,
                            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                           {'IpProtocol': 'tcp',
                            'FromPort': 0,
                            'ToPort': 65535,
                            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}]

    def __init__(self, client, name, d):
        self.client = client
        self.name = name
        util.dict_to_obj(self, d)

    @staticmethod
    def get_or_create_group(client, name):
        groups = client.security_groups.all()
        group = [g for g in groups if g.group_name == name]
        if len(group) > 0:
            print("Found security group " + name)
            return group[0]
        else:
            print("Creating security group " + name)
            group = client.create_security_group(GroupName=name, Description="Clamor EC2 group")
            SecurityGroup.authorize(group, client)
            return group

    @staticmethod
    def authorize(sg, client):
        sg.authorize_ingress(
            GroupId=sg.group_id,
            IpPermissions=SecurityGroup.cluster_permissions)
        sg.authorize_egress(
            GroupId=sg.group_id,
            IpPermissions=SecurityGroup.cluster_permissions)
        
    @staticmethod
    def revoke(sg, client):
        sg.revoke_ingress(
            GroupId=sg.group_id,
            IpPermissions=SecurityGroup.cluster_permissions)
        sg.revoke_egress(
            GroupId=sg.group_id,
            IpPermissions=SecurityGroup.cluster_permissions)
        
    def destroy(self):
        self.client.delete_security_group(GroupId=self.GroupId)
