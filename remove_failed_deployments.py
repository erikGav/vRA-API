from vra import *
from env import *
import os
import json

deployment_status = [
    'CREATE_SUCCESSFUL',
    'UPDATE_SUCCESSFUL',
    'CREATE_FAILED',
    'DELETE_FAILED'
]

if (__name__ == "__main__"):
    os.system('cls')

    vra_instance = Vra(fqdn=VRA_FQDN, username=VRA_USERNAME, password=VRA_PASSWORD, domain=VRA_DOMAIN)
    deployments = Deployment.get_all()
    
    for deployment in deployments:
        if "FAILED" in deployment.status:
            print(deployment.status)
            deployment.delete(dry_run=True)