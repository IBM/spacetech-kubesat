# Simulation Quick Start


## Build and deploy the simulation on a local system

[bootstrap.sh](https://raw.githubusercontent.com/IBM/spacetech-kubesat/master/simulation/devtest/bootstrap.sh) script clones a Github repository, build container images, and start simulation containers on your machine. Docker and git should be installed and running on your machine.


By default, code from `master` branch will be cloned to `/tmp/spacetech-kubesat` folder on your machine.
```sh
curl -sSL https://raw.githubusercontent.com/IBM/spacetech-kubesat/master/simulation/devtest/bootstrap.sh | sh
```

Use the following command to pull code from a specific branch.
```
curl -sSL https://raw.githubusercontent.com/IBM/spacetech-kubesat/master/simulation/devtest/bootstrap.sh | sh -s -- -b <branch-name>
```
Use the following command to clone git repo to a specific folder.
```
curl -sSL https://raw.githubusercontent.com/IBM/spacetech-kubesat/master/simulation/devtest/bootstrap.sh | sh -s -- -r <folder-name>
```

After several minutes later, all simulation services are running with dashboard at http://localhost:8080

Logs for each service can be found in `devtest` folder.

After making any code changes, run `docker exec -t dev-kubesat bash run.sh` to reload kubesat services with code updates.