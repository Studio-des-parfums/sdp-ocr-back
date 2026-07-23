from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class DeviceRegisterRequest(BaseModel):
    device_id: str
    device_name: Optional[str] = None


class DeviceRegisterResponse(BaseModel):
    id: int
    device_id: str
    device_name: Optional[str] = None
    status: str = "pending"


class DeviceVerifyRequest(BaseModel):
    device_id: str


class DeviceVerifyResponse(BaseModel):
    authorized: bool
    device_id: str
    status: Optional[str] = None


class DeviceRenameRequest(BaseModel):
    device_name: str


class DeviceResponse(BaseModel):
    id: int
    device_id: str
    device_name: Optional[str] = None
    registered_at: datetime
    last_seen_at: Optional[datetime] = None
    status: str
    decided_at: Optional[datetime] = None
