while read x; do ssh-keyscan -H $x >> ~/.ssh/known_hosts; done < servers/servers.txt
