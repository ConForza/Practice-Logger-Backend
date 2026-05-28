from pydantic import BaseModel, EmailStr, Field

class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    role: str

class User(BaseModel):
    email: EmailStr
    password: str
    is_active: bool
    role: str

class UserDBResponse(BaseModel):
    id: int
    email: EmailStr
    password: str
    is_active: bool
    role: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str