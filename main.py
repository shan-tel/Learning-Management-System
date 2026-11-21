from fastapi import FastAPI
from database import engine, Base
from users import models
from users.router import router as users_router
from login import router as login_router
from courses import router as courses_router
from fastapi.middleware.cors import CORSMiddleware
from authentication.router import router as auth_router




Base.metadata.create_all(bind = engine)

app = FastAPI( title ="Medemy Backend")

origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, PUT, DELETE)
    allow_headers=["*"],  # Allows all headers (crucial for sending your Bearer token!)
)


app.include_router(users_router)
app.include_router(login_router.router)
app.include_router(courses_router.router)
app.include_router(auth_router)
@app.get("/")
def read_root():
    return{"message" : "Welcome to the School API! The datebase is connected."}

