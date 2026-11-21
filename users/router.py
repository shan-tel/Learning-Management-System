from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from . import models, schemas
from .utils import hash_password
from authentication.oauth2 import get_current_user
from courses import models as course_models
import os
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True,
)

router = APIRouter(prefix = "/users", tags =["Users"])


@router.post("/register", response_model = schemas.UserResponse)
def register_user(user_data: schemas.UserCreate, db:Session = Depends(get_db)):
    print(f"Received user: {user_data.username}")
   
    db_user = db.query(models.User).filter(models.User.email == user_data.email).first()
    if db_user:
        raise HTTPException(status_code = 400, detail = "Email already registered")

    new_user = models.User(
    username = user_data.username,
    email = user_data.email,
    full_name = user_data.full_name,
    hashed_password = hash_password(user_data.password),
    role = user_data.role.value
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

@router.get("/", response_model = list[schemas.UserResponse])
def get_all_users(db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user)):
    requesting_user = db.query(models.User).filter(models.User.id == current_user_id).first()
    
    if requesting_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to view all users")
        
    return db.query(models.User).all()
@router.get("/instructors", response_model=list[schemas.InstructorCatalogResponse])
def get_public_instructors(db: Session = Depends(get_db)):
    # 1. Fetch all users who registered as an instructor 
    instructors = db.query(models.User).filter(
        models.User.role.in_(["instructor", "teacher"])
    ).all()

    catalog = []
    for inst in instructors:
        # 2. Get all courses created by this instructor
        inst_courses = db.query(course_models.Course).filter(
            course_models.Course.instructor_id == inst.id
        ).all()

        course_ids = [c.id for c in inst_courses]
        course_titles = [c.title for c in inst_courses]

        # 3. Count total students enrolled across all their courses
        total_students = 0
        if course_ids:
            total_students = db.query(course_models.Enrollment).filter(
                course_models.Enrollment.course_id.in_(course_ids)
            ).count()

        catalog.append({
            "id": inst.id,
            "full_name": inst.full_name,
            "official_title": inst.official_title or "Instructor",
            "profile_picture": inst.profile_picture,
            "courses_count": len(inst_courses),
            "students_count": total_students,
            "course_titles": course_titles,
        })

    return catalog
@router.get("/{user_id}", response_model= schemas.UserResponse)
def get_user(user_id: int, db:Session = Depends(get_db), current_user_id: int = Depends(get_current_user)):
    user = db.query(models.User).filter(models.User.id == user_id).first()

    if not user:
        raise HTTPException(status_code = 404, detail = "User not found")

    return user

@router.put("/{user_id}", response_model= schemas.UserResponse)
def update_user(user_id: int, updated_user: schemas.UserUpdate, db: Session= Depends(get_db), current_user_id: int = Depends(get_current_user)):
    requesting_user = db.query(models.User).filter(models.User.id == current_user_id).first()
    
    if requesting_user.id != user_id and requesting_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to modify this account")
    user_query = db.query(models.User).filter(models.User.id == user_id)
    db_user = user_query.first()

    if not db_user:
        raise HTTPException(status_code= 404, detail= "User not found")

    update_data = updated_user.model_dump(exclude_unset=True, exclude_none=True)

    user_query.update(update_data, synchronize_session= False)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user)):
    requesting_user = db.query(models.User).filter(models.User.id == current_user_id).first()
    
    if requesting_user.id != user_id and requesting_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to modify this account")
    user_query = db.query(models.User).filter(models.User.id == user_id)
    db_user = user_query.first()

    if not db_user:
        raise HTTPException(status_code= 404, detail= "User not found")

    user_query.delete(synchronize_session=False)
    db.commit()
    
    return {"message": f"User {user_id} deleted successfully"}
    

@router.put("/{user_id}/onboarding", response_model=schemas.UserResponse)
def complete_instructor_onboarding(
    user_id: int,
    official_title: str = Form(...),
    profile_picture: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    db_user.official_title = official_title

    if profile_picture:
        try:
            upload_result = cloudinary.uploader.upload(
                profile_picture.file,
                folder="medemy/instructors",
                resource_type="image",
            )
            db_user.profile_picture = upload_result["secure_url"]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")

    db.commit()
    db.refresh(db_user)
    return db_user