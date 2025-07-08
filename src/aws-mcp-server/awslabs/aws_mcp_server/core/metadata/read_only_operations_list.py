# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import requests
from loguru import logger


SERVICE_REFERENCE_URL = 'https://servicereference.us-east-1.amazonaws.com/'


class ServiceReferenceUrlsByService(dict):
    """Service reference urls by service."""

    def __init__(self):
        """Initialize the urls by service map."""
        super().__init__()
        try:
            response = requests.get(SERVICE_REFERENCE_URL).json()
        except Exception as e:
            logger.error(f'Error retrieving the service reference document: {e}')
            raise RuntimeError(f'Error retrieving the service reference document: {e}')
        for service_reference in response:
            self[service_reference['service']] = service_reference['url']


class ReadOnlyOperations(dict):
    """Read only operations list by service."""

    def __init__(self, service_reference_urls_by_service: dict):
        """Initialize the read only operations list."""
        super().__init__()
        self._service_reference_urls_by_service = service_reference_urls_by_service

    def has(self, service, operation) -> bool:
        """Check if the operation is in the read only operations list."""
        logger.info(f'checking in read only list : {service} - {operation}')
        if service not in self:
            if service not in self._service_reference_urls_by_service:
                return False
            self._cache_ready_only_operations_for_service(service)
        return operation in self[service]

    def _cache_ready_only_operations_for_service(self, service: str):
        try:
            response = requests.get(self._service_reference_urls_by_service[service]).json()
        except Exception as e:
            logger.error(f'Error retrieving the service reference document: {e}')
            raise RuntimeError(f'Error retrieving the service reference document: {e}')
        self[service] = []
        for action in response['Actions']:
            if not action['Annotations']['Properties']['IsWrite']:
                self[service].append(action['Name'])


def get_read_only_operations() -> ReadOnlyOperations:
    """Get the read only operations."""
    return ReadOnlyOperations(ServiceReferenceUrlsByService())
