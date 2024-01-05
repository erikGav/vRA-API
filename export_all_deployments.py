from vra import *
from env import *
import os
import json

FILENAME = 'deployments.json'

if (__name__ == "__main__"):
    os.system('cls')

    vra_instance = Vra(fqdn=VRA_FQDN, username=VRA_USERNAME, password=VRA_PASSWORD, domain=VRA_DOMAIN)
    deployments = Deployment.get_all(resourceTypes=['Cloud.vSphere.Machine', 'Cloud.vSphere.Network'])

    all_deployments = {}

    for deployment in deployments:
        all_deployments.update({
            deployment.name: vars(deployment)
        })

    if (not os.path.exists(EXPORT_PATH)):
        os.makedirs(EXPORT_PATH)
    
    with open(f"{EXPORT_PATH}/{FILENAME}", 'w') as f:
        f.write(json.dumps(all_deployments))