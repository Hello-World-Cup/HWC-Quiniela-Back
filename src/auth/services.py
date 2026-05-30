from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.core.config import settings


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_user_by_id(self, user_id: int) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_or_create_user_from_google(self, google_token: str) -> User:
        google_info = id_token.verify_oauth2_token(
            google_token,
            google_requests.Request(),
            settings.google_client_id,
        )
        google_id: str = google_info["sub"]
        email: str = google_info["email"]
        full_name: str = google_info.get("name", email)
        avatar_url: str | None = google_info.get("picture")

        result = await self.db.execute(select(User).where(User.google_id == google_id))
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                google_id=google_id,
                email=email,
                full_name=full_name,
                avatar_url=avatar_url,
            )
            self.db.add(user)
        else:
            # Keep avatar in sync on every login
            if avatar_url and user.avatar_url != avatar_url:
                user.avatar_url = avatar_url

        await self.db.commit()
        await self.db.refresh(user)
        return user
