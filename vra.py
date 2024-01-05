from requests.adapters import HTTPAdapter
from singleton import *
import requests
import json

requests.packages.urllib3.disable_warnings()

class Vra(metaclass=Singleton):
    base_url = None
    username = None
    password = None
    session = None

    _refresh_token = None
    _bearer_token = None
    _bearer_token_type = None

    def __init__(self, username, password, domain, fqdn):
        if (username and password and domain and fqdn):
            self.base_url = f"https://{fqdn}"
            self.username = username
            self.password = password
            self.domain = domain

            self.get_bearer_token()

    def get_session(self):
        if (Vra.session):
            return Vra.session

        session = requests.Session()
        http_adapter = HTTPAdapter(pool_connections=100, pool_maxsize=100)
        session.mount(prefix="https://", adapter=http_adapter)
        session.verify = False
        session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json"
        })
        Vra.session = session

        return session

    def get_refresh_token(self):
        if (Vra._refresh_token):
            return Vra.refresh_token

        session = self.get_session()

        refresh_token_body = json.dumps({
            "username": self.username,
            "password": self.password,
            "domain": self.domain
        })
        refresh_token_response = session.post(url=f"{self.base_url}/csp/gateway/am/api/login?access_token", data=refresh_token_body)

        refresh_token = refresh_token_response.json()['refresh_token']
        #print(f"Refresh Token: {refresh_token}")
        Vra._refresh_token = refresh_token

        return refresh_token
        
    def get_bearer_token(self):
        if (Vra._bearer_token):
            return Vra._bearer_token

        refresh_token = self.get_refresh_token()
        session = self.get_session()

        bearer_token_body = json.dumps({'refreshToken': refresh_token})
        bearer_token_response = session.post(url=f"{self.base_url}/iaas/api/login", data=bearer_token_body)
        
        bearer_token_json = bearer_token_response.json()
        bearer_token = bearer_token_json['token']
        bearer_token_type = bearer_token_json['tokenType']

        Vra._bearer_token = bearer_token
        Vra._bearer_token_type = bearer_token_type

        Vra.session.headers.update({'Authorization': f"{bearer_token_type} {bearer_token}"})

        return bearer_token

    def send_request(self, url, method='get', params={}, data={}, content=[]):
        session = self.get_session()
        action = getattr(session, method)

        if (method in ['get', 'head']):
            response = action(url=f"{self.base_url}{url}", params=params)
        else:
            response = action(url=f"{self.base_url}{url}", params=params, data=json.dumps(data))
        if (response.status_code != 200):
            return f"Response Code {response.status_code}"
            exit()
        response_json = response.json()

        if isinstance(response_json, dict):
            if ('content' in response_json.keys()):
                finalRes = [*content, *response_json['content']]
            else:
                finalRes = response_json
            # handle pagination
            if ('pageable' in response_json.keys() and response_json['pageable']['paged']):
                pageNumber = response_json['pageable']['pageNumber']
                print(f"Page Number: {pageNumber + 1}/{response_json['totalPages']}")

                if (not response_json['last']):
                    params['page'] = pageNumber + 1
                    return self.send_request(url=url, params=params, data=data, method=method, content=finalRes)

            return finalRes        
        elif isinstance(response_json, list):
            return response_json
        else:
            print(f"Unhandeled type of [response_json]: {type(response_json)}")

class Deployment:
    id = None
    name = None
    projectId = None
    status = None

    def __init__(self, id=None, name=None, status=None, projectId=None):
        if name and projectId:
            self.id = id
            self.name = name
            self.projectId = projectId
            self.status = status
        elif id:
            self.id = id
            deployment = self.get()

            self.name = deployment['name']
            self.projectId = deployment['projectId']
            self.status = deployment['status']
    
    def delete(self, dry_run=False):
        if not dry_run:
            print(f"Deleting deplyoment {self.name}")
            Vra().send_request(url=f"/deployment/api/deployments/{self.id}", method='delete')
        else:
            print(f"Deleting deplyoment {self.name}")

    def get(self):
        deployment_res = Vra().send_request(url=f"/deployment/api/deployments/{self.id}")
        return deployment_res

    def get_resources(self):
        resource_res = Vra().send_request(url=f"/deployment/api/deployments/{self.id}/resources")
        def map_resource(resource):
            if (resource['type'] == 'Cloud.vSphere.Machine'):
                return Virtualmachine(
                    id=resource['id'],
                    name=resource['properties']['resourceName'],
                    type=resource['type'],
                    origin=resource['origin'],
                    syncStatus=resource['syncStatus'],
                    deploymentId=self.id,
                    endpointId=resource['properties']['endpointId'],
                    resourceLink=resource['properties']['resourceLink']
                )
            else:
                return Resource(
                    id=resource['id'],
                    name=resource['properties']['resourceName'],
                    type=resource['type'],
                    origin=resource['origin'],
                    syncStatus=resource['syncStatus'],
                    deploymentId=self.id,
                    resourceLink=resource['properties']['resourceLink']
                )
        resources = list(map(map_resource, resource_res))

        return resources

    @staticmethod
    def get_all(resourceTypes=None):
        deployment_res = Vra().send_request(
            url='/deployment/api/deployments',
            params={"size": "200", "resourceTypes": resourceTypes}
            )
        def map_deployments(deployment):
            return Deployment(
                id=deployment['id'],
                name=deployment['name'],
                status=deployment['status'],
                projectId=deployment['projectId']
            )
        
        deployments = list(map(map_deployments, deployment_res))

        return deployments

class Resource:
    id = None
    name = None
    type = None
    origin = None
    endpointId = None
    syncStatus = None
    deploymentId = None
    resourceLink = None

    def __init__(
        self,
        id=None,
        name=None,
        type=None,
        origin=None,
        endpointId=None,
        syncStatus=None,
        deploymentId=None,
        resourceLink=None
    ):
        self.id = id
        self.name = name
        self.type = type
        self.origin = origin
        self.syncStatus = syncStatus
        self.deploymentId = deploymentId
        self.endpointId = endpointId
        self.resourceLink = resourceLink

    def get(self):
        resource_res = Vra().send_request(f"/deployment/api/deployments/{self.deploymentId}/resources/{self.id}")
        return resource_res

    def get_actions(self):
        actions = Vra().send_request(f"/deployment/api/resources/{self.id}/actions")
        return actions

    def run_action(self, actionId):
        action_res = Vra().send_request(
            url=f"/deployment/api/resources/{self.id}/requests",
            data={"actionId": actionId},
            method="post"
            )
        return f"Running: \n\tAction: [{action_res['name']}]\n\tResource: [{self.name}]\n\tType: [{self.type}]"

    @staticmethod
    def get_all(resourceTypes=None):
        resource_res = Vra().send_request(
            url='/deployment/api/resources',
            params={"size": "200", "resourceTypes": resourceTypes}
        )
        def map_resources(resource):
            if (resource['type'] == 'Cloud.vSphere.Machine'):
                return Virtualmachine(
                    id=resource['id'],
                    name=resource['properties']['resourceName'],
                    type=resource['type'],
                    origin=resource['origin'],
                    syncStatus=resource['syncStatus'],
                    deploymentId=resource['deploymentId'] if 'deploymentId' in resource.keys() else None,
                    endpointId=resource['properties']['endpointId'],
                    resourceLink=resource['properties']['id'],
                )
            else:
                return Resource(
                    id=resource['id'],
                    name=resource['properties']['resourceName'],
                    type=resource['type'],
                    origin=resource['origin'],
                    syncStatus=resource['syncStatus'],
                    deploymentId=resource['deploymentId'] if 'deploymentId' in resource.keys() else None,
                    resourceLink=resource['properties']['id']
                )

        resources = list(map(map_resources, resource_res))

        return resources

class Project:
    id = None
    name = None
    zones = None
    description = None

    def __init__(self, id=None, name=None, zones=None, description=None):
        if name and id:
            self.id = id
            self.name = name
            self.zones = zones
            self.description = description
        elif id:
            self.id = id
            project_res = self.get()

            self.name = project_res['name']
            self.zones = project_res['zones'] if project_res['zones'] else None
            self.description = project_res['description']
        elif name:
            self.name = name
            project_res = self.get()

            self.id = project_res[0]['id']
            self.zones = project_res[0]['zones'] if project_res[0]['zones'] else None
            self.description = project_res['description']

    def get(self):
        if self.id:
            project_res = Vra().send_request(url=f"/iaas/api/projects/{self.id}")
            return project_res
        elif self.name:
            project_res = Vra().send_request(url=f"/iaas/api/projects/?$filter=name eq '{self.name}'")
            return project_res

    @staticmethod
    def get_all():
        project_res = Vra().send_request(url='/iaas/api/projects')

        def map_project(project):
            return Project(
                id=project['id'],
                name=project['name'],
                zones=project['zones'],
                description=project['description']
            )

        projects = list(map(map_project, project_res))

        return projects

class Virtualmachine(Resource):
    _actions = [
        "Cloud.vSphere.Machine.Add.Disk",
        "Cloud.vSphere.Machine.custom.adddisk",
        "Cloud.vSphere.Machine.ApplySaltConfiguration",
        "Cloud.vSphere.Machine.AttachSaltStackResource",
        "Cloud.vSphere.Machine.Change.SecurityGroup",
        "Cloud.vSphere.Machine.Remote.Console",
        "Cloud.vSphere.Machine.Snapshot.Create",
        "Cloud.vSphere.Machine.Delete",
        "Cloud.vSphere.Machine.Snapshot.Delete",    
        "Cloud.vSphere.Machine.Remote.PrivateKey",
        "Cloud.vSphere.Machine.PowerOff",
        "Cloud.vSphere.Machine.PowerOn",
        "Cloud.vSphere.Machine.Reboot",
        "Cloud.vSphere.Machine.Rebuild",
        "Cloud.vSphere.Machine.Remove.Disk",
        "Cloud.vSphere.Machine.Reset",
        "Cloud.vSphere.Machine.Resize",
        "Cloud.vSphere.Machine.Compute.Disk.Resize",
        "Cloud.vSphere.Machine.Resize.Compute.Disk",
        "Cloud.vSphere.Machine.Snapshot.Revert",
        "Cloud.vSphere.Machine.Shutdown",
        "Cloud.vSphere.Machine.Suspend",
        "Cloud.vSphere.Machine.Unregister",
        "Cloud.vSphere.Machine.Update.Tags",
    ]

    def __init__(
        self,
        id=None,
        name=None,
        type=None,
        origin=None,
        syncStatus=None,
        deploymentId=None,
        endpointId=None,
        resourceLink=None,
    ):
        super().__init__(id, name, type, origin, syncStatus, deploymentId, endpointId, resourceLink)

    def shutdown(self):
        action_res = self.run_action(actionId='Cloud.vSphere.Machine.Shutdown')
        return action_res

    def power_on(self):
        action_res = self.run_action(actionId='Cloud.vSphere.Machine.PowerOn')
        return action_res

    def unregister(self):
        action_res = self.run_action(actionId='Cloud.vSphere.Machine.Unregister')
        return action_res
