from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict

from database import get_session
from services.user_service import UserService, RoleService
from models.user import UserCreate, UserLogin
from exceptions import (
    NotFoundException,
    BadRequestException,
    UnauthorizedException,
    ForbiddenException,
    ConflictException
)

router = APIRouter()


@router.post(
    "/signup",
    status_code=status.HTTP_201_CREATED,
    summary="User Registration",
    description="Register a new user in the system",
    response_description="Confirmation of successful user creation with user ID",
    responses={
        201: {"description": "User successfully created"},
        400: {"description": "Invalid input data"},
        409: {"description": "User with this login or email already exists"},
        500: {"description": "Internal server error"}
    }
)
async def signup(
    user_data: UserCreate,
    db: Session = Depends(get_session)
) -> Dict[str, str]:
    """
    Регистрация нового пользователя в системе.

    Создает нового пользователя с указанными данными и автоматически инициализирует
    баланс пользователя со значением 0.0 в валюте RUB.

    Args:
        user_data: Данные для регистрации пользователя, включая:
            - login: Уникальный логин пользователя
            - email: Уникальный email пользователя
            - password: Пароль пользователя
            - display_name: Отображаемое имя пользователя
            - role_id: ID роли пользователя в системе

    Returns:
        Dict с сообщением об успехе и ID созданного пользователя

    Raises:
        HTTPException 400: Если роль с указанным ID не найдена
        HTTPException 409: Если пользователь с таким логином или email уже существует
        HTTPException 500: При внутренних ошибках сервера
    """
    role_service = RoleService(db)
    user_service = UserService(db, role_service)

    try:
        user = user_service.create_user(user_data, 1)
        return {
            "message": "User created successfully",
            "user_id": str(user.id)
        }
    except BadRequestException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail)
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e.detail)
        )
    except ConflictException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e.detail)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {e}"
        )


@router.post(
    "/signin",
    summary="User Authentication",
    description="Authenticate user with login credentials",
    response_description="Authentication token or success message",
    responses={
        200: {"description": "Successful authentication"},
        401: {"description": "Invalid credentials"},
        403: {"description": "User account is deactivated"},
        404: {"description": "User not found"},
        500: {"description": "Internal server error"}
    }
)
async def signin(
    login_data: UserLogin,
    db: Session = Depends(get_session)
) -> Dict[str, str]:
    """
    Аутентификация пользователя в системе.

    Проверяет учетные данные пользователя (логин и пароль) и возвращает
    идентификатор пользователя при успешной аутентификации.

    Args:
        login_data: Данные для входа, включая:
            - login: Логин пользователя
            - password: Пароль пользователя

    Returns:
        Dict с сообщением об успешном входе и ID пользователя

    Raises:
        HTTPException 401: Если пароль неверен
        HTTPException 403: Если учетная запись пользователя деактивирована
        HTTPException 404: Если пользователь с таким логином не найден
        HTTPException 500: При внутренних ошибках сервера
    """
    role_service = RoleService(db)
    user_service = UserService(db, role_service)

    try:
        user = user_service.authenticate_user(login_data)
        return {
            "message": "Login successful",
            "user_id": str(user.id)
        }
    except UnauthorizedException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e.detail)
        )
    except ForbiddenException as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e.detail)
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e.detail)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
