# cloister
EC2 cluster management for Clamor

## Requirements

Cloister requires `python3` and `boto3`: `pip3 install boto3`.
Set up your AWS credentials first as documented [here](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html).

## Setup

Set up Clamor on a single EC2 instance and create an AMI for the instance.

Create a Cloister configuration for the cluster you want to launch. A sample configuration file can be found in `configs/sample_config.json`.

During development, you may create many AMIs as you develop and iterate.
You can prefix your AMI names with a unique value, e.g. `$USERNAME-clamor-i`,
and then indicate this prefix in the config file using the `ami_tag` key.
(For example, `ami_tag: $USERAME-clamor`.)
If you specify the AMI id as `latest` then Clamor will automatically use the latest
AMI that has your specified prefix.

## Cloister commands

* `login`: Log in to the master for an existing cluster.
* `login-ami`: If you specify your development instance DNS in the config file,
  this shortcut will allow you to log in to the development instance.
* `launch`: Launch a Clamor cluster using the specified config file.
  The manager, master, and server DNS names will be stored in the `servers/` folder.
* `destroy`: Destroy a Clamor cluster with the name specified in the config file.
* `copy-dns`: Copy the lists of server names to the cluster so that experiments
  can be launched directly from the master. (`launch` should run this automatically,
  but on occasion the instances take too long to initialize and SSH times out, so
  this command needs to be run manually after launch.)
* `redeploy`: Use `rsync` to update the `clamor` folder on all workers in the cluster
  using the `clamor` folder on the development instance.

Cloister requires python 3. Run `python3 cloister.py [-c CONFIG] COMMAND`.

## Running experiments

The `run_experiment.py` script (python2 by default) runs a benchmark.
Currently it only supports benchmarks in the following format:
they must be in their own folder in `clamor/experiments/cpp/$EXPERIMENT_NAME`
and the binary must be called `$EXPERIMENT_NAME`.
If your experiment has any local variables (e.g. `LD_LIBRARY_PATH` dependencies)
that need to be sourced before the experiment is run,
they can be stored in a file inside the experiment folder called `experiment_vars`.

`run_experiment.py` allows one to run the various actors in the experiment
using `-a`. `-a killall` will kill all remote processes running the experiment binary
and also free up any bound ports
(this is sometimes required for cleanup if the experiment crashes unexpectedly).

To run an experiment, first log in to the master/manager instance manually
by using `python3 cloister.py login` and then launch the manager:
`python run_experiment.py -a manager -b $EXPERIMENT_NAME -l` is sufficient.
(`-l` indicates that the process should be run locally rather than
as an SSH command on a remote server.)
Then, on your local machine, you can start the rest of the experiment
by running `python run_experiment.py -a experiment -b $EXPERIMENT_NAME -k $NUM_WORKER -p $NUM_PROCS_PER_WORKER`.
The experiment will run and generate timestamped output logs on the master and on each worker.
There are also commands to independently start a master and workers in case you need
fine-grained debugging.