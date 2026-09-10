from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_user, require_admin
from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User, UserRole
from app.schemas.user import LoginRequest, RegistrationRequest, TokenResponse, UserResponse


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(data: RegistrationRequest, db: Session = Depends(get_db)) -> User:
	email = str(data.email).lower()
	if db.query(User).filter(User.email == email).first():
		raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

	user = User(
		email=email,
		password_hash=hash_password(data.password),
		role=UserRole.CUSTOMER,
	)
	db.add(user)
	db.commit()
	db.refresh(user)
	return user


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
	user = db.query(User).filter(User.email == str(data.email).lower()).first()
	if not user or not verify_password(data.password, user.password_hash):
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Invalid email or password",
		)

	return TokenResponse(access_token=create_access_token({
		"sub": str(user.id),
		"role": user.role.value,
	}))


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)) -> User:
	return current_user


@router.get("/admin-check", response_model=UserResponse)
def admin_check(current_user: User = Depends(require_admin)) -> User:
	return current_user