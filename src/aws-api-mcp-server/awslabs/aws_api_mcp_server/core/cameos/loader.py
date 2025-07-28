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

"""Loader for external tools from packages."""

import json
from .proxy_tool_manager import FilteredProxyToolManager
from fastmcp import Client, FastMCP
from fastmcp.client.transports import ClientTransport, StdioTransport, StreamableHttpTransport
from loguru import logger
from pathlib import Path
from pydantic import BaseModel
from typing import Literal, TypedDict


class StdioArgs(TypedDict):
    """Arguments for the stdio transport."""

    command: str
    args: list[str]


class HttpArgs(TypedDict):
    """Arguments for the http transport."""

    url: str


TRANSPORT_FACTORIES: dict[str, ClientTransport] = {
    'streamable-http': StreamableHttpTransport,
    'stdio': StdioTransport,
}


class CameoConfig(BaseModel):
    """Interface for a cameo."""

    name: str
    type: Literal['streamable-http', 'stdio']
    description: str
    args: StdioArgs | HttpArgs
    tools: list[str]


class CameoLoader:
    """Loader for external tools from packages."""

    def __init__(self, mcp_server: FastMCP):
        """Initialize the external tool loader."""
        self.server = mcp_server
        self.cameos = self.load_cameos()

    def load_cameos(self):
        """Load the cameos from the config."""
        with open(Path(__file__).parent / 'config.json', 'r') as f:
            return [CameoConfig(**cameo) for cameo in json.load(f)['cameos']]

    def add_cameos(self):
        """Add the cameos to the server."""
        for cameo in self.cameos:
            logger.info(f'Processing cameo: {cameo.name} (type: {cameo.type})')

            transport = TRANSPORT_FACTORIES[cameo.type](**cameo.args)
            proxy_server = FastMCP.as_proxy(backend=transport)

            try:
                if cameo.tools != ['*']:
                    proxy_server._tool_manager = FilteredProxyToolManager(
                        allowed_tools=cameo.tools,
                        client_factory=self._create_client_factory(transport),
                    )

                self.server.mount(server=proxy_server)
                logger.info(f'Successfully mounted proxy for {cameo.name}')
            except Exception as e:
                logger.error(f'Failed to process cameo {cameo.name}: {e}')

    def _create_client_factory(self, transport_instance: ClientTransport):
        def client_factory():
            return Client(transport_instance)

        return client_factory
