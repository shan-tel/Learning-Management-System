from pydantic import BaseModel
from typing import List, Optional


class InstructorInfo(BaseModel):
    id: int
    username: str 

    class Config:
        from_attributes = True

class SectionBase(BaseModel):
    title: str
    content: str

class SectionCreate(SectionBase):
    pass 

class SectionResponse(SectionBase):
    id: int
    course_id: int

    class Config:
        from_attributes = True


class CourseBase(BaseModel):
    title: str
    description: str

class CourseCreate(CourseBase):
    pass 

class CourseResponse(CourseBase):
    id: int
    instructor_id: int
    instructor: InstructorInfo
    sections: List[SectionResponse] = [] 

    class Config:
        from_attributes = True

class QuizBase(BaseModel):
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_answer: str

class QuizCreate(QuizBase):
    pass

class QuizResponse(QuizBase):
    id: int
    section_id: int

    class Config:
        from_attributes = True

class EnrollmentResponse(BaseModel):
    id: int
    user_id: int
    course_id: int

    class Config:
        from_attributes = True

class QuizSubmission(BaseModel):
    student_answer: str 


class AnswerItem(BaseModel):
    quiz_id: int
    student_answer: str


class SectionQuizSubmission(BaseModel):
    answers: List[AnswerItem]

class FullCourseCreate(BaseModel):
    title: str
    description: str
    pass_mark: int = 50
    total_marks: int = 0
    sections: List[SectionCreate] = []
    course_quiz: List[QuizQuestion] = []