from hashlib import sha256
from typing import List, Optional

import errors
from app.models import User as UserModel
from app.models import AuthData
from app.models import new_session


class User:
    pass


async def get_by_id(user_id) -> Optional[UserModel]:
    user = await UserModel.get(user_id)
    return user


async def resolve(username) -> Optional[UserModel]:
    user = await UserModel.resolve(username)
    return user


async def search(username) -> List[UserModel]:
    users_list = await UserModel.search(username)
    users_list = [(row.User.id, row.User.username) for row in users_list]
    return users_list


async def login(username: str, hexdigest: str):
    digest = bytes.fromhex(hexdigest)
    user = await AuthData.get_user(username, 'password', digest)
    if not user:
        raise ValueError("no such user")
    token = await user.get_token()
    return token


async def register(username: str, password: str) -> UserModel:
    if await resolve(username):
        raise errors.UsernameOccupied
    pwd_hash = sha256(password.encode())
    pwd_digest = pwd_hash.digest()
    async with new_session() as session:
        user = UserModel(username=username)
        await user.store(session=session)
        auth_data = AuthData(user=user.id, method='password', data=pwd_digest)
        await auth_data.store(session=session)
    return user
