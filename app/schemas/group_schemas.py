from datetime import datetime

from pydantic import BaseModel


class GroupBase(BaseModel):
    name: str
    description: str | None = None


class GroupCreate(GroupBase):
    created_by: int


class GroupUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class GroupResponse(GroupBase):
    id: int
    created_at: datetime
    updated_at: datetime
    is_deleted: bool
    created_by: int

    class Config:
        from_attributes = True


# Schémas pour gérer les relations clients-groupes
class AddCustomersToGroup(BaseModel):
    customer_ids: list[int]
    added_by: int


class RemoveCustomersFromGroup(BaseModel):
    customer_ids: list[int]


class MergeGroupsRequest(BaseModel):
    """Schéma pour fusionner plusieurs groupes"""

    source_group_ids: list[int]
    new_group_name: str
    description: str | None = None
    created_by: int


class CustomerGroupResponse(BaseModel):
    customer_id: int
    group_id: int
    added_at: datetime
    added_by: int

    class Config:
        from_attributes = True
