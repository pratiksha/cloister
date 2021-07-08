#!/usr/bin/python3

def main():
    procs_per_server = 8
    outfile = 'servers/mpi_hosts.txt'
    servers = []
    with open('servers/servers_private.txt', 'r') as f:
        servers = [l.strip() for l in f.readlines()]

    with open(outfile, 'w') as f:
        for s in servers:
            f.write(s + ' slots=' + str(procs_per_server) + ' max-slots=' + str(procs_per_server) + '\n')
        
if __name__=='__main__':
    main()
