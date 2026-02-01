import httpx
import json
from typing import Any
from app.config import settings


class NeuralGraphClient:
    def __init__(self):
        self.base_url = settings.neuralgraph_url
    
    def _interpolate_params(self, query: str, params: dict) -> str:
        """Replace $param with actual values in query."""
        if not params:
            return query
        
        result = query
        for key, value in params.items():
            placeholder = f"${key}"
            if isinstance(value, str):
                escaped = value.replace('\\', '\\\\').replace('"', '\\"')
                replacement = f'"{escaped}"'
            elif isinstance(value, bool):
                replacement = "true" if value else "false"
            elif value is None:
                replacement = "null"
            elif isinstance(value, (list, dict)):
                replacement = json.dumps(value)
            else:
                replacement = str(value)
            
            result = result.replace(placeholder, replacement)
        
        return result
    
    async def query(self, query: str, params: dict = None) -> dict:
        """Execute NGQL query against NeuralGraphDB."""
        interpolated_query = self._interpolate_params(query, params)
        
        print(f"=== QUERY ===")
        print(interpolated_query)
        print(f"=============")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/query",
                json={"query": interpolated_query},
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    
    async def execute(self, query: str, params: dict = None) -> list[dict]:
        """Execute query and return rows."""
        result = await self.query(query, params)
        if result.get("success"):
            return result.get("result", {}).get("rows", [])
        raise Exception(result.get("error", "Query failed"))


db = NeuralGraphClient()
