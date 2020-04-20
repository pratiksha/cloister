import util

import boto3 as boto

class Instance:
    active_states = ['pending', 'running', 'stopping', 'stopped']
    waiting_states = ['shutting-down']
