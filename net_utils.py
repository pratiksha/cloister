import argparse
import csv
import itertools
import json
import math
import subprocess
import sys
import time

default_user = "ubuntu"

# Copy a file to a given host through scp, throwing an exception if scp fails
def scp(host, identity_file, user, local_file, remote_file):
  subprocess.check_call(
    "scp -q -o StrictHostKeyChecking=no -i %s '%s' '%s@%s:%s'" %
    (identity_file, local_file, user, host, remote_file), shell=True)
  
# Copy file from host to local directory
def reverse_scp(host, identity_file, user, local_file, remote_file):
  subprocess.check_call(
    "scp -q -o StrictHostKeyChecking=no -i %s '%s@%s:%s' '%s'" %
    (identity_file, user, host, remote_file, local_file), shell=True)

def ssh(host, identity_file, user):
  subprocess.check_call("ssh -o StrictHostKeyChecking=no -i %s %s@%s" %
                        (identity_file, user, host), shell=True)

# The --delete option will remove files that no longer exist in src.
def rsync(src, dest, identity_file, user, dirname, delete=False):
  command = (("rsync -avh -e 'ssh -o StrictHostKeyChecking=no -i %s' " + 
              "'%s' '%s@%s:%s'") % (identity_file, dirname,
                                      user, dest, dirname))
  if delete:
    command += " --delete"
  output = run_cmdline_nonblock(src, command, identity_file)
  print(output)

def run_cmdline(server_name, script, aws_key, local=False):
  if local:
    output = subprocess.check_output(cmd, shell=True, universal_newlines=True)
    return output
  else:
    cmd = "ssh -A -o StrictHostKeyChecking=no -i %s ubuntu@%s \"%s\"" % (aws_key, server_name, script)
    print(cmd)
    output = subprocess.check_output(cmd, shell=True, universal_newlines=True)
    return output

def run_cmdline_nonblock(server_name, script, aws_key, local=False):
  if local:
    output = subprocess.Popen(cmd, shell=True, universal_newlines=True)
  else:
    cmd = "ssh -A -o StrictHostKeyChecking=no -i %s ubuntu@%s \"%s\"" % (aws_key, server_name, script)
    print(cmd)
    output = subprocess.Popen(cmd, shell=True, universal_newlines=True)
  
## this runs a script
def run_cmd(server_name, script, aws_key, local=False):
  if local:
    output = subprocess.check_output(cmd, shell=True, universal_newlines=True)
    return output
  else:
    cmd = "ssh -A -o StrictHostKeyChecking=no -i %s ubuntu@%s 'bash -s' < %s" % (aws_key, server_name, script)
    output = subprocess.check_output(cmd, shell=True, universal_newlines=True)
    return output

def run_cmd_nonblock(server_name, script, aws_key, local=False):
  if local:
    cmd = script
    print(cmd)
    subprocess.Popen(cmd, shell=True, universal_newlines=True)
  else:
    cmd = "ssh -A -o StrictHostKeyChecking=no -i %s ubuntu@%s 'bash -s' < %s" % (aws_key, server_name, script)
    print(cmd)
    subprocess.Popen(cmd, shell=True, universal_newlines=True)

def read_ips(ip_fname):
    with open(ip_fname, 'r') as f:
        return [l.strip() for l in f.readlines()]

def read_config(config_file):
    with open(config_file, 'r') as f:
        return json.load(f)

def copy_file(instance, conf, local_path, remote_path):
  scp(instance.public_dns_name, 
      conf.key_pair,
      conf.user,
      local_path,
      remote_path)

def copy_remote_file(instance, conf, local_path, remote_path):
  reverse_scp(instance.public_dns_name, 
              conf.key_pair,
              conf.user,
              local_path,
              remote_path)
