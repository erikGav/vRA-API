from vra import *
from env import *
import os

FILENAME = 'missing_resource_deployments.txt'

if (__name__ == "__main__"):
    os.system('cls')

    vra_instance = Vra(fqdn=VRA_FQDN, username=VRA_USERNAME, password=VRA_PASSWORD, domain=VRA_DOMAIN)
    # deployments = Deployment.get_all()
    resources = Resource.get_all(syncStatus='MISSING')
    missing_deployments = [] 
    for resource in resources:
        if (resource.syncStatus == 'MISSING'):
            missing_deployments.append(resource.deploymentId)
    print(len(missing_deployments))
    deployments_name = []
    for missing_deployment in missing_deployments:
        deployment = Deployment(id=missing_deployment)
        deployments_name.append(deployment.name)
    if (not os.path.exists(EXPORT_PATH)):
        os.makedirs(EXPORT_PATH)
    
    with open(f"{EXPORT_PATH}/{FILENAME}", 'w') as f:
        for line in deployments_name:
            f.write(f"{line}\n")