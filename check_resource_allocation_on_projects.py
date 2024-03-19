from vra import *
from env import *
import os
import csv
import json

FILENAME = 'resource_allocation'
ZONES_ID = {}

if (__name__ == "__main__"):
    os.system('cls')

    vra_instances = Vra(fqdn=VRA_FQDN, username=VRA_USERNAME, password=VRA_PASSWORD, domain=VRA_DOMAIN)
    projects = Project.get_all()
    deployments = Deployment.get_all(resourceTypes='Cloud.vSphere.Machine')

    result = {}

    for project in projects:
        projectName = project.name
        max_allocated = 0
        zones = []
        if project.zones:
            for zone in project.zones:
                max_allocated += zone['allocatedInstancesCount']
                zone_name = ZONES_ID[zone['zoneId']]
                zone = {
                    'name': zone_name,
                    'MemoryLimitMB': zone['memoryLimitMB'],
                    'MemoryAllocatedMB': zone['allocatedMemoryMB'],
                    'CPULimit': zone['cpuLimit'],
                    'CPUAllocated': zone['allocatedCpu'],
                    'StorageLimitGB': zone['storageLimitGB'],
                    'StorageAllocatedGB': zone['allocatedStorageGB']
                }
                zones.append(zone)
            result.update({
                projectName: {
                    'Description': project.description,
                    'Max Allocated Instances': max_allocated,
                    'Existing': 0,
                    'zones': zones
                }
            })
        else:
            result.update({
                projectName: {
                    'Description': project.description,
                    'Max Allocated Instances': max_allocated,
                    'Existing': 0,
                    'zones': []
                }
            })
    
    count_deployments = len(deployments)
    count = 0
    for deployment in deployments:
        count += 1
        # print(f"Machine: {count}/{count_deployments}")
        for project in projects:
            if deployment.projectId == project.id:
                projectName = project.name
                to_add = result[projectName]['Existing'] + 1
                result[projectName].update({
                    'Existing': to_add
                })
            else:
                continue
    
    result_copy = result.copy()

    for k, v in result.items():
        # if (v['Max Allocated Instances'] == v['Existing']):
        #     del result_copy[k]
        if v['zones']:
            zone_len = len(v['zones'])
            count = 0
            for zone in v['zones']:
                if zone['MemoryAllocatedMB'] > zone['MemoryLimitMB'] or zone['CPUAllocated'] > zone['CPULimit'] or zone['StorageAllocatedGB'] > zone['StorageLimitGB']:
                    count += 1
            if (count == 0):
                result_copy.pop(k, None)
        else:
            result_copy.pop(k, None)

    if (not os.path.exists(EXPORT_PATH)):
        os.makedirs(EXPORT_PATH)
    
    # export to JSON
    with open(f"{EXPORT_PATH}/filtered_{FILENAME}.json", 'w') as filtered, open(f"{EXPORT_PATH}/{FILENAME}.json", 'w') as original:
        filtered.write(json.dumps(result_copy))
        original.write(json.dumps(result))

    # export to CSV
    with open(f"{EXPORT_PATH}/{FILENAME}.csv", 'w', newline='') as original:
        csvwriter = csv.writer(original)
        header = ['Project Name', 'Description', 'VMs Count']
        data = []

        for key, value in result.items():
            
            to_extend = [[key, value['Description'], value['Existing']]]
            data.extend(to_extend)

        csvwriter.writerow(header)
        csvwriter.writerows(data)