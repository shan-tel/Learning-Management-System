from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from . import models, schemas 
from authentication.oauth2 import get_current_user
from typing import List

router = APIRouter(prefix="/courses", tags=["Courses"])

@router.post("/full", status_code=status.HTTP_201_CREATED)
def create_full_course(
    course: schemas.FullCourseCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.role not in ("instructor", "teacher"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only instructors can create courses.",
        )

    new_course = models.Course(
        title=course.title,
        description=course.description,
        pass_mark=course.pass_mark,
        total_marks=course.total_marks,
        sections_data=[s.model_dump() for s in course.sections],
        course_quiz=[q.model_dump() for q in course.course_quiz],
        instructor_id=current_user.id,
    )
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    return new_course
#@router.post("/", response_model=schemas.CourseResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=schemas.CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(course: schemas.CourseCreate, db: Session = Depends(get_db), current_user: int = Depends(get_current_user)):
    
    
    new_course = models.Course(
        title=course.title,
        description=course.description,
        instructor_id=current_user  
    )
    
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    
    return new_course

@router.get("/my-courses", response_model=List[schemas.CourseResponse])
def get_my_enrolled_courses(db: Session = Depends(get_db), current_user: int = Depends(get_current_user)):
    
    
    enrolled_courses = (
        db.query(models.Course)
        .join(models.Enrollment, models.Course.id == models.Enrollment.course_id)
        .filter(models.Enrollment.user_id == current_user)
        .all()
    )
    
    return enrolled_courses

@router.post("/{course_id}/sections", response_model=schemas.SectionResponse, status_code=status.HTTP_201_CREATED)
def create_section(course_id: int, section: schemas.SectionCreate, db: Session = Depends(get_db), current_user: int = Depends(get_current_user)):
    
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
        
    new_section = models.Section(
        title=section.title,
        content=section.content,
        course_id=course_id
    )
    
    db.add(new_section)
    db.commit()
    db.refresh(new_section)
    
    return new_section

@router.post("/{section_id}/quizzes", response_model=schemas.QuizResponse, status_code=status.HTTP_201_CREATED)
def create_quiz(section_id: int, quiz: schemas.QuizCreate, db: Session = Depends(get_db), current_user: int = Depends(get_current_user)):
    
   
    section = db.query(models.Section).filter(models.Section.id == section_id).first()
    if not section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")
        
   
    new_quiz = models.Quiz(
        
        question_text=quiz.question_text,
        option_a=quiz.option_a,
        option_b=quiz.option_b,
        option_c=quiz.option_c,
        option_d=quiz.option_d,
        correct_answer=quiz.correct_answer,
        section_id=section_id
    )
    
    db.add(new_quiz)
    db.commit()
    db.refresh(new_quiz)
    
    return new_quiz

@router.get("/", response_model=List[schemas.CourseResponse])
def get_all_courses(db: Session = Depends(get_db)):
    
    courses = db.query(models.Course).all()
    return courses

@router.get("/{course_id}", response_model=schemas.CourseResponse)
def get_course(course_id: int, db: Session = Depends(get_db)):
    
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
        
    return course

@router.post("/{course_id}/enroll", response_model=schemas.EnrollmentResponse, status_code=status.HTTP_201_CREATED)
def enroll_in_course(course_id: int, db: Session = Depends(get_db), current_user: int = Depends(get_current_user)):
    
    
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    
    existing_enrollment = db.query(models.Enrollment).filter(
        models.Enrollment.course_id == course_id,
        models.Enrollment.user_id == current_user
    ).first()

    if existing_enrollment:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You are already enrolled in this course")

    
    new_enrollment = models.Enrollment(
        user_id=current_user,
        course_id=course_id
    )
    
    db.add(new_enrollment)
    db.commit()
    db.refresh(new_enrollment)
    
    return new_enrollment

@router.post("/quizzes/{quiz_id}/submit")
def submit_quiz_answer(
    quiz_id: int, 
    submission: schemas.QuizSubmission, 
    db: Session = Depends(get_db), 
    current_user: int = Depends(get_current_user)
):
    
    
    quiz = db.query(models.Quiz).filter(models.Quiz.id == quiz_id).first()
    
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    
    is_correct = submission.student_answer.upper() == quiz.correct_answer.upper()

    
    if is_correct:
        return {"status": "success", "message": "Correct! Great job.", "correct": True}
    else:
        return {"status": "failed", "message": f"Incorrect. The right answer was {quiz.correct_answer}.", "correct": False}


@router.post("/sections/{section_id}/submit-quiz")
def submit_section_quiz(
    section_id: int, 
    submission: schemas.SectionQuizSubmission, 
    db: Session = Depends(get_db), 
    current_user: int = Depends(get_current_user)
):
    
    questions = db.query(models.Quiz).filter(models.Quiz.section_id == section_id).all()
    
    if not questions:
        raise HTTPException(status_code=404, detail="No questions found for this section")

    
    answer_key = {q.id: q.correct_answer.upper() for q in questions}
    
    
    correct_count = 0
    
    for item in submission.answers:
        correct_ans = answer_key.get(item.quiz_id)
        
        if correct_ans and item.student_answer.upper() == correct_ans:
            correct_count += 1

    
    total_questions = len(questions)
    
    final_percentage = int((correct_count / total_questions) * 100)

    
    new_grade = models.SectionGrade(
        user_id=current_user,
        section_id=section_id,
        score=final_percentage
    )
    db.add(new_grade)
    db.commit()
    db.refresh(new_grade)

    
    return {
        "status": "success", 
        "message": f"You got {correct_count} out of {total_questions} correct.", 
        "score_percentage": final_percentage
    }