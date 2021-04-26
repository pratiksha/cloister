#!/bin/bash
echo 0 | sudo tee /proc/sys/kernel/randomize_va_space
echo 1 | sudo tee /proc/sys/vm/overcommit_memory
ulimit -s unlimited
source ~/.local_vars
#export GRPC_TRACE=api,channel,client_channel_call,executor,server_Channel,subchannel,subchannel_pool,tcp
#export GRPC_VERBOSITY=debug
export PUBLIC_HOSTNAME="$(curl http://169.254.169.254/latest/meta-data/public-hostname 2>/dev/null)"
cd $HOME/clamor/experiments/cpp/$1
echo ./$1 -i $PUBLIC_HOSTNAME -m worker -p $((50000 + $2)) -d $3 -l $1.weld
source experiment_vars # Will fail but continue if the file doesn't exist
curdate=$(date +"%m%d%Y_%H%M")
echo $curdate
./$1 -i $PUBLIC_HOSTNAME -m worker -p $((50000 + $2)) -d $3 -l $1.weld &> worker$2_$curdate.log
