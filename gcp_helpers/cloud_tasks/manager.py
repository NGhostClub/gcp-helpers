import json
from dataclasses import dataclass

from google.cloud import tasks_v2
from google.oauth2 import service_account


@dataclass
class HttpMethod:
    GET: str = "GET"
    POST: str = "POST"
    PUT: str = "PUT"
    PATCH: str = "PATCH"


class CloudTasksManager:
    def __init__(self, project, location, queue_name, key_path=None):
        self._project = project
        self._location = location
        self._queue_name = queue_name
        self._key_path = key_path
        self.cli = self._new_client()
        self._queue_path = self._new_queue()
        self.http = HttpCloudTasks(self.cli, self._queue_path)

    def _new_client(self):
        if not self._key_path:
            return tasks_v2.CloudTasksClient()
        else:
            return tasks_v2.CloudTasksClient(
                credentials=service_account.Credentials.from_service_account_file(self._key_path)
            )

    def _new_queue(self):
        return self.cli.queue_path(self._project, self._location, self._queue_name)


class HttpCloudTasks:
    METHODS = {
        "POST": tasks_v2.HttpMethod.POST,
        "GET": tasks_v2.HttpMethod.GET,
        "PUT": tasks_v2.HttpMethod.PUT,
        "PATCH": tasks_v2.HttpMethod.PATCH
    }

    def __init__(self, client: tasks_v2.CloudTasksClient, queue_path: tasks_v2):
        self._cli = client
        self._queue_path = queue_path
        self._invoker_sa_email: str | None = None

    def set_service_account(self, email: str):
        self._invoker_sa_email = email

    def _create_task_payload(self, method: tasks_v2.HttpMethod, url, body: str | dict | None = None, headers=None, auth=False):
        payload = {
            "http_request": {  # Specify the type of request.
                "http_method": method,
                "url": url,  # The full url path that the task will be sent to.
                "headers": headers if headers and isinstance(headers, dict) else {}
            }
        }
        if body:
            if isinstance(body, dict):
                body = json.dumps(body)
                payload['http_request']['body'] = body.encode()
            payload['http_request']['headers'].update({"Content-type": "application/json"})
        if auth:
            payload['http_request']["oidc_token"] = {
                    "service_account_email": self._invoker_sa_email,
                    "audience": url
            }

        return payload

    def create_task(self, method: str, url, body: str | dict | None = None, headers=None, auth=False):
        method = self.METHODS.get(method, HttpMethod.GET)
        task = self._create_task_payload(
            method,
            url,
            body,
            headers,
            auth
        )
        print(task)
        resp = self._cli.create_task(request={"parent": self._queue_path, "task": task})
        print("Created task {}".format(resp.name))

