"""Pydantic base model for MongoDB documents."""

from typing import Optional

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field

from app.db_connection import db


class MongoModel(BaseModel):
    """Base model for MongoDB documents. Maps _id to id and provides save()."""

    model_config = ConfigDict(populate_by_name=True)

    id: Optional[str] = Field(None, alias="_id", description="MongoDB document id")
    case_id: str = Field(..., description="The ID of the case")
    date: str = Field(..., description="The date of the document")
    text: str = Field(..., description="The text of the document")

    def save(self, collection_name: str) -> "MongoModel":
        """Save or update the document in the specified collection."""
        data = self.model_dump(by_alias=True, exclude_none=True)

        if self.id is None:
            data.pop("_id", None)
            result = db[collection_name].insert_one(data)
            self.id = str(result.inserted_id)
        else:
            data.pop("_id", None)
            db[collection_name].update_one(
                {"_id": ObjectId(self.id)},
                {"$set": data},
            )
        return self
