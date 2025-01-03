from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
import sqlite3
import os
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)

app = FastAPI()
origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# User model
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

Base.metadata.create_all(bind=engine)

# Database session generator
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Authentication and Password Management
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

# Pydantic Models
class UserCreate(BaseModel):
    username: str
    password: str

class QuestionRequest(BaseModel):
    question: str

class QuestionHistory(BaseModel):
    id: int
    question: str
    answer: str

# Utility functions for user authentication
def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, user: UserCreate):
    hashed_password = pwd_context.hash(user.password)
    db_user = User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    return "User created successfully"

def authenticate_user(username: str, password: str, db: Session):
    user = db.query(User).filter(User.username == username).first()
    if not user or not pwd_context.verify(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# ML Model Setup (Hugging Face)
load_dotenv()
huggingface_token = os.getenv("Token")
if not huggingface_token:
    raise ValueError("Access token not found. Ensure 'Token' is set in the environment variables.")

logging.info("Initializing Hugging Face model...")
text_model = "facebook/opt-1.3b"
tokenizer = AutoTokenizer.from_pretrained(text_model, token=huggingface_token)
model = AutoModelForCausalLM.from_pretrained(text_model, token=huggingface_token)
gemma_pipeline = pipeline("text-generation", model=model, tokenizer=tokenizer)
logging.info("Model initialized successfully.")

# SQLite Database Setup for question history
DATABASE = "questions.db"
def init_db():
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("""CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY,
                question TEXT NOT NULL,
                answer TEXT NOT NULL
            )""")
            conn.commit()
    except Exception as e:
        logging.error(f"Error initializing the database: {e}")
        raise
init_db()

# API Endpoints

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "OK"}

# User registration endpoint
@app.post("/register")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return create_user(db=db, user=user)

# Login and token generation endpoint
@app.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

# Endpoint to ask a question and get a response from the model
@app.post("/ask")
def ask_question(request: QuestionRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        # Generate answer using the pipeline
        encoded_input = tokenizer(request.question, max_length=150, truncation=True, padding=True, return_tensors="pt")
        output = model.generate(encoded_input['input_ids'], max_length=150, num_return_sequences=1, max_new_tokens=50)
        answer = tokenizer.decode(output[0], skip_special_tokens=True)

        # Save question and answer to SQLite history
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO history (question, answer) VALUES (?, ?)", (request.question, answer))
            conn.commit()

        return {"answer": answer}
    except Exception as e:
        logging.error(f"Error generating answer: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating answer: {str(e)}")

# Endpoint to fetch question history
@app.get("/history", response_model=list[QuestionHistory])
def get_history():
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, question, answer FROM history")
            rows = cursor.fetchall()
        return [{"id": row[0], "question": row[1], "answer": row[2]} for row in rows]
    except Exception as e:
        logging.error(f"Error fetching history: {e}")
        raise HTTPException(status_code=500, detail="Error fetching history.")
