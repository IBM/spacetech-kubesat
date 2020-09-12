## Run kubesat services on your development machine

### Pre-requisite
Docker should be installed and running on your machine.

### Instructions

By default code from `master` branch will be cloned to `/tmp/spacetech-kubesat` folder on your machine.
```bash
curl -sSL https://raw.githubusercontent.com/IBM/spacetech-kubesat/devtest/master/bootstrap.sh | sh
```

Use following commands to instead bootstrap your devtest environment with custom options.

- Pull code from a specific branch
```
curl -sSL https://raw.githubusercontent.com/IBM/spacetech-kubesat/devtest/master/bootstrap.sh | sh -s -- -b <branch-name>
```
- Clone git repo to a specific folder
```
curl -sSL https://raw.githubusercontent.com/IBM/spacetech-kubesat/devtest/master/bootstrap.sh | sh -s -- -r <folder-name>
```

Post-bootstrap, all kubesat services are running with dashboard at http://localhost:8080

Logs for each service can be found in `devtest` folder.

After making any code changes, run `docker exec -it dev-kubesat bash run.sh` to reload kubesat services with code updates.
