from __future__ import annotations

import logging
from typing import List, Optional

from autogen_core.application.logging import TRACE_LOGGER_NAME
from langchain.callbacks.manager import CallbackManagerForToolRun
from pydantic import BaseModel, Field

from ._base import LanceDbTool
from ._filters import build_where_clause, FilterCondition


class GetEntitySchema(BaseModel):
    table_name: str = Field(description="The name of the table to get the entity from")
    conditions: List[FilterCondition] = Field(
        description="List of filter conditions that must ALL be met"
    )


class LanceDBGetEntity(LanceDbTool):
    """Tool for retrieving entities from LanceDB tables.

    This tool allows querying and retrieving entities from specified LanceDB tables.
    """

    name: str = "get_lancedb_entity"
    description: str = (
        "Use this tool to retrieve entities from a LanceDB table. "
        "You need to specify the table name and a WHERE clause to filter entities."
    )
    args_schema: type[BaseModel] = GetEntitySchema

    _logger = logging.getLogger(f"{TRACE_LOGGER_NAME}.{name}")

    def _run(
        self,
        table_name: str,
        conditions: List[FilterCondition],
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        try:
            table = self.open_table(table_name)

            where_clause = build_where_clause(conditions)
            results = table.search().where(where=where_clause, prefilter=True).to_list()

            # Format the results in a more readable way
            formatted_results = []
            for entity in results:
                # Convert entity to dict and format each field
                entity_dict = dict(entity)
                # Sort keys for consistent output
                formatted_fields = [
                    f"{k}: {entity_dict[k]}"
                    for k in sorted(entity_dict.keys())
                    if k != "vector"
                ]
                formatted_entity = "{\n    " + "\n    ".join(formatted_fields) + "\n}"
                formatted_results.append(formatted_entity)

            results_str = "\n".join(formatted_results)

            return (
                f"Found {len(results)} entities matching {where_clause}:\n{results_str}"
            )

        except Exception as e:
            self._logger.error(f"Failed to get entities: {str(e)}")
            raise

    async def _arun(
        self,
        table: str,
        where: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        raise NotImplementedError("Async version not implemented")
