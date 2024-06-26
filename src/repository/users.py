from libgravatar import Gravatar
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, join
from typing import List, Union
from fastapi import HTTPException

import sys
from pathlib import Path

# Добавляем корневую папку проекта в sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


from src.database.models import User, Role, Photos
from src.schemas.schemas_auth import UserModel
from src.schemas.user import UserResponse

async def get_user_by_email(email: str, db: AsyncSession) -> User:
    stmt = select(User).filter(User.email==email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    return user


async def check_username_unique(username: str, db: AsyncSession) -> bool:
    """
    Check if the username is unique.

    :param username: str: Username to check
    :param db: AsyncSession: Async database session
    :return: bool: True if the username is unique, False otherwise
    """
    user = await db.execute(select(User).filter(User.username == username))
    return user.scalar_one_or_none() is None


async def create_user(body: UserModel, db: AsyncSession, role: Role) -> User:
    """
    The create_user function creates a new user in the database.
    Args:
        body (UserModel): The UserModel object containing the data to be inserted into the database.
        db (Session): The SQLAlchemy Session object used to interact with the database.
    Returns:
        User: A newly created user from the database.

    :param body: UserModel: Create a new user
    :param db: Session: Create a database session
    :return: A user object
    :doc-author: Trelent
    """
    # Перевіряємо унікальність імені користувача
    if not await check_username_unique(body.username, db):
        raise HTTPException(status_code=400, detail="Username is already taken")

    avatar = None
    try:
        g = Gravatar(body.email)
        avatar = g.get_image()
    except Exception as e:
        print(e)

    new_user = User(**body.dict(), avatar=avatar, role=role.value)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user



async def update_token(user: User, token: str | None, db: AsyncSession) -> None:
    """
    The update_token function updates the refresh token for a user.

    :param user: User: Identify the user that will have their token updated
    :param token: str | None: Update the user's refresh token
    :param db: Session: Commit the changes to the database
    :return: None
    :doc-author: Trelent
    """
    user.refresh_token = token
    await db.commit()

async def confirmed_email(email: str, db: AsyncSession) -> None:
    user = await get_user_by_email(email, db)
    user.confirmed = True
    await db.commit()


async def update_avatar_url(email: str, url: str | None, db: AsyncSession) -> User:
    user = await get_user_by_email(email, db)
    user.avatar = url
    await db.commit()
    await db.refresh(user)
    return user


async def get_all_users(db: AsyncSession) -> List[User]:
    stmt = select(User)
    user = await db.execute(stmt)
    user = user.scalars().all()
    return user

   

async def update_user_role(email: str, new_role: str, db: AsyncSession) -> User:
    user = await get_user_by_email(email, db)
    user.role = new_role
    await db.commit()
    await db.refresh(user)
    return user

async def get_user_by_username(username: str, db: AsyncSession) -> User:
    stmt = select(User).filter(User.username==username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    return user

async def count_user_photos(username: str, db: AsyncSession) -> Union[int, None]:
    stmt = select(func.count()).select_from(User.__table__.join(Photos)).where(User.username == username)
    result = await db.execute(stmt)
    photo_count = result.scalar_one_or_none()
    return photo_count