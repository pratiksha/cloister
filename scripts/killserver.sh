#!/bin/bash
sudo killall $1
sudo fuser -k 50000/tcp
sudo fuser -k 50001/tcp
sudo fuser -k 50002/tcp
sudo fuser -k 50003/tcp
sudo fuser -k 50004/tcp
sudo fuser -k 50005/tcp
sudo fuser -k 50006/tcp
sudo fuser -k 50007/tcp
sudo fuser -k 50008/tcp
sudo fuser -k 40000/tcp
sudo fuser -k 70000/tcp
