import util

import boto3 as boto

class Instance:
    active_states = ['pending', 'running', 'stopping', 'stopped']
    waiting_states = ['shutting-down']
    
    def __init__(self, client, d):
        util.dict_to_obj(self, d)
        print(str(self.__dict__))
        self.client = client

    def is_pending(self):
        return self.State.Name == 'pending'
    
    def is_running(self):
        return self.State.Name == 'running'

    def is_active(self):
        return self.State.Name in Instance.active_states
