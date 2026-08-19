from pydantic import BaseModel


class Login_request(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token:str


class Payload(BaseModel):
    name: str
    email: str

