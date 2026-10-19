from pydantic import BaseModel


class UserData(BaseModel):
    reference: str
    first_name: str
    last_name: str
    email: str
    phone: str
    job: str
    city: str
    country: str


class ExportRequest(BaseModel):
    data: list[UserData]
