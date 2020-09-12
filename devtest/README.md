## Run kubesat services on your development machine

### Pre-requisite
Docker should be installed and running on your machine.

### Instructions

```bash
mkdir -p /tmp/spacetech-kubesat
git clone https://github.com/IBM/spacetech-kubesat /tmp/spacetech-kubesat
```

`/tmp/spacetech-kubesat` is used as location of the cloned repository on your development machine. If cloned to a different location, set the directory location to `kubesat_repo` in `spacetech-kubesat/dev/bootstrap.sh`.  

Run `bootstrap.sh`. This will create a container with required conda environment. This container will mount your cloned repo, so you can do development work on your machine and use the container to run and test.

```bash
bash /tmp/spacetech-kubesat/dev/bootstrap.sh
```

You should now have `dev-kubesat` container in running state. Log in and start kubesat services.

```bash
docker exec -it dev-kubesat /bin/bash
conda activate kubesat && bash /tmp/spacetech-kubesat/dev/run-kubesat.sh
```

STDOUT from each each service is also available as log file in the `dev` folder. After all services are running, kubesat dashboard is accessible at http://localhost:8080


After making any code changes to existing services, re-run `conda activate kubesat && bash /tmp/spacetech-kubesat/dev/run-kubesat.sh` to reload new environment with the updates.
