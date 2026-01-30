from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: str
    email: EmailStr

class B2BUserCreate(BaseModel):
    email: EmailStr
    password: str
    company_name: str
    contact_person: str
    phone: str
    address: str
    business_type: str

class B2BUserOut(BaseModel):
    id: str
    email: EmailStr
    company_name: str
    contact_person: str
    phone: str
    address: str
    business_type: str
