import argparse
import csv
import itertools
import json
import math
import subprocess
import sys
import time

from net_utils import *

def start_manager(manager_ip, bench_name, nprocs, npartitions, worker_ips, aws_key, local):
    run_cmd_nonblock(manager_ip, "scripts/run-manager.sh %s %d %s %d" % (bench_name, nprocs, worker_ips, npartitions), aws_key, local)

def start_master(master_ip, bench_name, nprocs, npartitions, manager_name, worker_ips, aws_key, local):
    run_cmd_nonblock(master_ip, "scripts/run-master.sh %s %d %s %s %d" % (bench_name, nprocs, manager_name, worker_ips, npartitions), aws_key, local)

def start_worker_blocking(worker_ip, bench_name, manager_name, worker_id, aws_key, local, worker=False):
    if worker:
        cmd = "./runserver-worker.sh %s %d %s" % (bench_name, worker_id, manager_name) # Run separate worker binary
    else:
        cmd = "./runserver.sh %s %d %s" % (bench_name, worker_id, manager_name)
    print cmd
    output = run_cmd(worker_ip, cmd, aws_key, local)
    return output

def start_workers(worker_ips, bench_name, nprocs, manager_name, aws_key, local, worker=False):
    for ip in worker_ips:
        for i in range(nprocs):
            if worker:
                cmd = "scripts/runserver-worker.sh %s %d %s & sleep 0.1" % (bench_name, i, manager_name)
            else:
                cmd = "scripts/runserver.sh %s %d %s & sleep 0.1" % (bench_name, i, manager_name)
            print cmd
            run_cmd_nonblock(ip, cmd, aws_key, local)

def kill_servers(server_ips, bench_name, aws_key):
    for ip in server_ips:
        try:
            output = run_cmd(ip, "scripts/killserver.sh %s" % bench_name, aws_key)
            print output
        except subprocess.CalledProcessError as e:
            print e
            continue
        
def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-n', "--num_iterations", type=int, default=1,
                        help="Number of iterations to run each benchmark")
    #parser.add_argument('-f', "--output_fname", type=str, required=True,
    #                    help="Name of CSV to dump output in")
    parser.add_argument('-b', "--benchmark", type=str, default=None,
                        help="Benchmark to run")
    parser.add_argument('-s', "--server_names", type=str, default="servers/servers.txt",
                        help="Filename containing list of server IPs")
    parser.add_argument('-m', "--master_name", type=str, default="servers/master.txt",
                        help="Filename containing master IP")
    parser.add_argument('-k', "--nworkers", type=int, default=1,
                        help="Number of nodes to use")
    parser.add_argument('-p', "--nprocs", type=int, default=1,
                        help="Number of processes per worker")
    parser.add_argument('-a', "--action", type=str, default="experiment",
                        help="Command to launch")
    parser.add_argument('-l', "--local", action='store_true',
                        help="Run command locally (default is to run remotely on server)")
    parser.add_argument('-y', "--aws-key", type=str, default="prthaker-slate.pem",
                        help="AWS key for experiment")
    parser.add_argument('-w', "--worker", action='store_true',
                        help="Run separate worker binary")
    parser.add_argument('-z', "--no_master", action='store_true',
                        help="Run workers only (start master manually)")
    
    args = parser.parse_args()

    server_names = read_ips(args.server_names)
    master_name = read_ips(args.master_name)[0]
    manager_name = master_name
    worker_names = server_names[:args.nworkers]
    
    assert args.nworkers <= (len(server_names))

    if args.action == 'experiment':

        # don't use this - SSH to master node to start memory manager for experiments, instead
        #    start_manager(manager_name, args.benchmark, args.nprocs, ','.join(worker_names))
        #    time.sleep(10)
        start_workers(worker_names, args.benchmark, args.nprocs, manager_name, args.aws_key, args.local, args.worker)
        time.sleep(10) # wait for workers to come up

        print('Launching master...')

        time.sleep(1)

        if not args.no_master:
            start_master(master_name, args.benchmark, args.nprocs, args.nprocs * len(worker_names), manager_name, ','.join(worker_names), args.aws_key, args.local)

        time.sleep(1000) # wait for end

    elif args.action == 'killall':
        kill_servers([master_name], args.benchmark, args.aws_key)
        kill_servers(server_names, args.benchmark, args.aws_key)
        
    elif args.action == 'make':
        for name in server_names + [master_name]:
            run_cmd(name, "scripts/make.sh", args.aws_key, args.local)

    elif args.action == 'manager':
        start_manager(manager_name, args.benchmark, args.nprocs, args.nprocs * len(worker_names), ','.join(worker_names), args.aws_key, args.local)

    elif args.action == 'master':
        start_master(manager_name, args.benchmark, args.nprocs, args.nprocs * len(worker_names), manager_name, ','.join(worker_names), args.aws_key, args.local)

    elif args.action == 'worker': # mainly for running single workers locally after ssh to node
        start_worker_blocking(args.benchmark, manager_name, args.worker_idx, args.aws_key, args.local, args.worker)
    
if __name__=="__main__":
    main()
