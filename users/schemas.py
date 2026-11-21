from pydantic import BaseModel, EmailStr, Field, ConfigDict
from enum import Enum
from typing import List, Optional

class RoleEnum(str, Enum):
    student = "student"
    teacher = "teacher"
    admin = "admin"

class UserBase(BaseModel):
    username : str
    email : EmailStr
    full_name : str 
    role : RoleEnum = RoleEnum.student

class UserCreate(UserBase):
    password : str = Field(min_length = 6)

class UserResponse(UserBase):
    id: int  
    
    
    model_config = ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
    username: str | None = None
    email: EmailStr | None = None
    full_name: str | None = None
    role: RoleEnum | None = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user_id: int
    role: str

class TokenRefreshRequest(BaseModel):
    refresh_token: str

# --- QUIZ SCHEMAS ---
class QuizBase(BaseModel):
    question_text: str
    correct_answer: str

class QuizCreate(QuizBase):
    pass

class QuizResponse(QuizBase):
    id: int
    section_id: int

    
    model_config = ConfigDict(from_attributes=True)



class InstructorCatalogResponse(BaseModel):
    id: int
    full_name: str
    official_title: Optional[str] = "Instructor"
    profile_picture: Optional[str] = None
    courses_count: int
    students_count: int
    course_titles: List[str] = []

    class Config:
        from_attributes = True