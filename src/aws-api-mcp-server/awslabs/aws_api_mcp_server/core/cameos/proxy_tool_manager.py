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

from fastmcp import Client
from fastmcp.server.proxy import ProxyTool, ProxyToolManager
from fastmcp.tools.tool import Tool
from loguru import logger
from typing import Callable, override


class FilteredProxyToolManager(ProxyToolManager):
    """A tool manager that filters tools based on a list of allowed tools."""

    def __init__(self, allowed_tools: list[str], client_factory: Callable[[], Client]):
        """Initialize the filtered proxy tool manager."""
        super().__init__(client_factory=client_factory)
        self.allowed_tools = allowed_tools

    @override
    async def get_tools(self) -> dict[str, Tool]:
        """Get the filtered list of tools."""
        filtered_tools = {}
        client = self.client_factory()
        async with client:
            try:
                client_tools = await client.list_tools()

                for tool in client_tools:
                    if tool.name in self.allowed_tools:
                        filtered_tools[tool.name] = ProxyTool.from_mcp_tool(client, tool)
                        logger.info(f'Added filtered tool {tool.name}')

                return filtered_tools
            except Exception as e:
                logger.error(f'Error getting tools from {client.transport}: {e}')
                return {}

    @override
    async def list_tools(self) -> list[Tool]:
        """Get the filtered list of tools."""
        tools_dict = await self.get_tools()
        return list(tools_dict.values())
