from copy import deepcopy

import time

class obj(object):
    def __init__(self, d):
        for a, b in d.items():
            if isinstance(b, (list, tuple)):
                setattr(self, a, [obj(x) if isinstance(x, dict) else x for x in b])
            else:
                setattr(self, a, obj(b) if isinstance(b, dict) else b)

def dict_to_obj(instance, d):
    ret = obj(d)
    instance.__dict__.update(ret.__dict__)


def worker_group_name(cluster_name):
    return cluster_name + '-workers'

def master_group_name(cluster_name):
    return cluster_name + '-master'

def parse_ami_date(date):
    fmtstr = '%Y-%m-%dT%H:%M:%S.%fZ'
    return time.strptime(date, fmtstr)
