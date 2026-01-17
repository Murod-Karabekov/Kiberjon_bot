from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select
from bot.database.models import Base, User, UserRole, Group, ChatType
from bot.config import DATABASE_URL


class Database:
    def __init__(self):
        self.engine = create_async_engine(DATABASE_URL, echo=False)
        self.session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    async def create_tables(self):
        """Create all tables in the database"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_tables(self):
        """Drop all tables in the database"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def get_user(self, telegram_id: int) -> Optional[User]:
        """Get user by telegram_id"""
        async with self.session_maker() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            return result.scalar_one_or_none()

    async def create_user(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        language_code: Optional[str] = None,
        role: UserRole = UserRole.USER
    ) -> User:
        """Create a new user"""
        async with self.session_maker() as session:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                language_code=language_code,
                role=role,
                is_registered=False
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user

    async def update_user_phone(self, telegram_id: int, phone_number: str) -> User:
        """Update user's phone number"""
        async with self.session_maker() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
            if user:
                user.phone_number = phone_number
                await session.commit()
                await session.refresh(user)
            return user

    async def update_user_name(self, telegram_id: int, preferred_name: str) -> User:
        """Update user's preferred name and mark as registered"""
        async with self.session_maker() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
            if user:
                user.preferred_name = preferred_name
                user.is_registered = True
                await session.commit()
                await session.refresh(user)
            return user

    async def update_user_role(self, telegram_id: int, role: UserRole) -> User:
        """Update user's role"""
        async with self.session_maker() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
            if user:
                user.role = role
                await session.commit()
                await session.refresh(user)
            return user

    async def get_all_users(self, role: Optional[UserRole] = None) -> list[User]:
        """Get all users, optionally filtered by role"""
        async with self.session_maker() as session:
            query = select(User)
            if role:
                query = query.where(User.role == role)
            result = await session.execute(query)
            return list(result.scalars().all())

    # Group operations
    async def get_group(self, chat_id: int) -> Optional[Group]:
        """Get group by chat_id"""
        async with self.session_maker() as session:
            result = await session.execute(
                select(Group).where(Group.chat_id == chat_id)
            )
            return result.scalar_one_or_none()

    async def create_group(
        self,
        chat_id: int,
        title: str,
        chat_type: ChatType,
        username: Optional[str] = None,
        description: Optional[str] = None,
        bot_is_admin: bool = False,
        bot_permissions: Optional[str] = None,
        member_count: Optional[int] = None
    ) -> Group:
        """Create a new group"""
        async with self.session_maker() as session:
            group = Group(
                chat_id=chat_id,
                title=title,
                chat_type=chat_type,
                username=username,
                description=description,
                bot_is_admin=bot_is_admin,
                bot_permissions=bot_permissions,
                is_active=True,
                member_count=member_count
            )
            session.add(group)
            await session.commit()
            await session.refresh(group)
            return group

    async def update_group(
        self,
        chat_id: int,
        title: Optional[str] = None,
        username: Optional[str] = None,
        description: Optional[str] = None,
        bot_is_admin: Optional[bool] = None,
        bot_permissions: Optional[str] = None,
        member_count: Optional[int] = None
    ) -> Optional[Group]:
        """Update group information"""
        async with self.session_maker() as session:
            result = await session.execute(
                select(Group).where(Group.chat_id == chat_id)
            )
            group = result.scalar_one_or_none()
            if group:
                if title is not None:
                    group.title = title
                if username is not None:
                    group.username = username
                if description is not None:
                    group.description = description
                if bot_is_admin is not None:
                    group.bot_is_admin = bot_is_admin
                if bot_permissions is not None:
                    group.bot_permissions = bot_permissions
                if member_count is not None:
                    group.member_count = member_count
                await session.commit()
                await session.refresh(group)
            return group

    async def deactivate_group(self, chat_id: int) -> Optional[Group]:
        """Mark group as inactive (bot left or was removed)"""
        async with self.session_maker() as session:
            result = await session.execute(
                select(Group).where(Group.chat_id == chat_id)
            )
            group = result.scalar_one_or_none()
            if group:
                group.is_active = False
                group.left_at = datetime.utcnow()
                await session.commit()
                await session.refresh(group)
            return group

    async def reactivate_group(self, chat_id: int) -> Optional[Group]:
        """Reactivate group (bot rejoined)"""
        async with self.session_maker() as session:
            result = await session.execute(
                select(Group).where(Group.chat_id == chat_id)
            )
            group = result.scalar_one_or_none()
            if group:
                group.is_active = True
                group.left_at = None
                await session.commit()
                await session.refresh(group)
            return group

    async def get_all_groups(self, active_only: bool = False) -> list[Group]:
        """Get all groups, optionally only active ones"""
        async with self.session_maker() as session:
            query = select(Group)
            if active_only:
                query = query.where(Group.is_active == True)
            result = await session.execute(query)
            return list(result.scalars().all())

    async def close(self):
        """Close database connection"""
        await self.engine.dispose()
