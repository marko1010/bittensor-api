from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, GetCoreSchemaHandler, GetJsonSchemaHandler
from datetime import datetime
from bson import ObjectId
from pydantic_core import CoreSchema
from bson import ObjectId
from pydantic_core import core_schema

class PyObjectId(str):
    @classmethod
    def __get_pydantic_core_schema__(
            cls, _source_type: Any, _handler: Any
    ) -> core_schema.CoreSchema:
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(ObjectId),
                core_schema.chain_schema([
                    core_schema.str_schema(),
                    core_schema.no_info_plain_validator_function(cls.validate),
                ])
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x)
            ),
        )

    @classmethod
    def validate(cls, value) -> ObjectId:
        if not ObjectId.is_valid(value):
            raise ValueError("Invalid ObjectId")

        return ObjectId(value)

class StakeAction(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id")
    netuid: int
    hotkey: str
    sentiment_score: float
    action: str
    amount: float
    result: bool
    timestamp: datetime