from fastapi import APIRouter, HTTPException, Depends, status
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from models import User, User_Pydantic, UserIn_Pydantic, Subscription_Pydantic
from tortoise.exceptions import DoesNotExist
from typing import Optional
from config import APIConfig


JWT_SECRET_KEY = APIConfig().jwt_secret
JWT_ALGORITHM = 'HS256'
JWT_TOKEN_LIFETIME = {'days': 4}


pwd_context = CryptContext(schemes=['argon2', 'django_pbkdf2_sha256'],
	deprecated=['django_pbkdf2_sha256'])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='auth/login')
router = APIRouter()


async def get_current_user(token: str = Depends(oauth2_scheme)):
	credentials_exception = HTTPException(
		status_code=status.HTTP_401_UNAUTHORIZED,
		detail='Could not validate credentials',
		headers={'WWW-Authenticate': 'Bearer'},
	)

	try:
		payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
		uuid: str = payload.get('sub')
		if uuid is None:
			raise credentials_exception
	except JWTError:
		raise credentials_exception

	user = await User.get(id=uuid)
	if user is None:
		raise credentials_exception
	return user


async def get_subscribed_user(token: str = Depends(oauth2_scheme)):
	user = await get_current_user(token)
	if not await user.has_active_subscription():
		raise HTTPException(
			status_code=status.HTTP_402_PAYMENT_REQUIRED,
			detail='You need an active subscription to perform this action.')

	return user


def create_access_token(user):
	data = {
		'sub': str(user.id),
		'exp': datetime.utcnow() + timedelta(**JWT_TOKEN_LIFETIME)
	}
	return jwt.encode(data, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


class UserResponse(User_Pydantic):
	subscription: Optional[Subscription_Pydantic]


class LoginResponse(BaseModel):
	access_token: str
	user: UserResponse


@router.post('/login', response_model=LoginResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
	credentials_exception = HTTPException(
		status_code=status.HTTP_401_UNAUTHORIZED,
		detail='Incorrect username or password',
		headers={'WWW-Authenticate': 'Bearer'},
	)

	try:
		user = await User.get(email=form_data.username.lower())
	except DoesNotExist:
		try:
			user = await User.get(legacy_username=form_data.username)
		except DoesNotExist:
			raise credentials_exception

	(verified, new_hash) = pwd_context.verify_and_update(form_data.password, user.password)

	if not verified:
		raise credentials_exception

	if new_hash:
		user.password = new_hash

	user.last_seen = datetime.utcnow()
	await user.save()

	return {
		'access_token': create_access_token(user),
		'user': await UserResponse.from_tortoise_orm(user),
		'ephemeral_key_salt': user.ephemeral_key_salt,
		'master_key': user.master_key,
		'master_key_nonce': user.master_key_nonce,
	}


class AccessTokenResponse(BaseModel):
	access_token: str


@router.post('/token', response_model=AccessTokenResponse)
async def renew_token(user: User = Depends(get_current_user)):
	user.last_seen = datetime.utcnow()
	await user.save()
	return {'access_token': create_access_token(user)}


class SignupData(BaseModel):
	email: str
	password: str
	ephemeral_key_salt: str
	master_key: str
	master_key_nonce: str


class SignupResponse(BaseModel):
	email: str


@router.post('/signup', response_model=SignupResponse)
async def signup(user: SignupData):
	user.email = user.email.lower()
	if await User.get(email=user.email).exists():
		raise HTTPException(
			status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
			detail='An account with this email address already exists'
		)

	user.password = pwd_context.hash(user.password)
	user = await User.create(**user.dict(exclude_unset=True))
	return await UserResponse.from_tortoise_orm(user)


@router.get('/user', response_model=UserResponse)
async def get_user(user: User = Depends(get_current_user)):
	return await UserResponse.from_tortoise_orm(user)


@router.put('/user', response_model=UserResponse)
async def update_user(user_data: UserIn_Pydantic, user: User = Depends(get_current_user)):
	user_data.email = user_data.email.lower()
	if user_data.email != user.email and await User.get(email=user_data.email).exists():
		raise HTTPException(
			status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
			detail='An account with this email address already exists'
		)

	await User.filter(id=user.id).update(**user_data.dict(exclude_unset=True))
	return await UserResponse.from_queryset_single(User.get(id=user.id))
