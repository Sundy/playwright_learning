import random
from fastapi import FastAPI
from pydantic import BaseModel


class UserRequest(BaseModel):
    name: str


class UserResponse(BaseModel):
    name: str
    age: int


app = FastAPI(title="User API", description="Simple API to return user name and random age")


@app.post("/get_user", response_model=UserResponse)
def get_user(req: UserRequest):
    age = random.randint(18, 65)
    return {"name": req.name, "age": age}


@app.get("/")
def root():
    return {"message": "API is running. POST /get_user with JSON {\"name\": \"你的名字\"}"}
