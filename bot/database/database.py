from typing import Optional
from datetime import datetime
import secrets
import string
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select
from bot.database.models import Base, User, UserRole, Group, ChatType, CoinTransaction, TransactionType
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

    # KiberCoin operations
    def generate_referral_code(self) -> str:
        """Generate unique referral code"""
        chars = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(chars) for _ in range(8))

    async def get_user_by_referral_code(self, referral_code: str) -> Optional[User]:
        """Get user by referral code"""
        async with self.session_maker() as session:
            result = await session.execute(
                select(User).where(User.referral_code == referral_code)
            )
            return result.scalar_one_or_none()

    async def get_user_by_phone(self, phone_number: str) -> Optional[User]:
        """Get user by phone number"""
        async with self.session_maker() as session:
            result = await session.execute(
                select(User).where(User.phone_number == phone_number)
            )
            return result.scalar_one_or_none()

    async def set_referral_code(self, user_id: int) -> str:
        """Generate and set referral code for user"""
        async with self.session_maker() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            if user and not user.referral_code:
                # Generate unique code
                while True:
                    code = self.generate_referral_code()
                    existing = await self.get_user_by_referral_code(code)
                    if not existing:
                        break
                
                user.referral_code = code
                await session.commit()
                await session.refresh(user)
                return code
            return user.referral_code if user else None

    async def add_coins(
        self,
        user_id: int,
        amount: int,
        transaction_type: TransactionType,
        description: Optional[str] = None,
        admin_id: Optional[int] = None,
        related_user_id: Optional[int] = None
    ) -> bool:
        """Add coins to user and record transaction"""
        async with self.session_maker() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            if user:
                user.coins += amount
                
                # Create transaction record
                transaction = CoinTransaction(
                    user_id=user_id,
                    amount=amount,
                    transaction_type=transaction_type,
                    description=description,
                    admin_id=admin_id,
                    related_user_id=related_user_id
                )
                session.add(transaction)
                
                await session.commit()
                return True
            return False

    async def remove_coins(
        self,
        user_id: int,
        amount: int,
        description: Optional[str] = None,
        admin_id: Optional[int] = None
    ) -> bool:
        """Remove coins from user and record transaction"""
        async with self.session_maker() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            if user:
                user.coins -= amount
                if user.coins < 0:
                    user.coins = 0
                
                # Create transaction record
                transaction = CoinTransaction(
                    user_id=user_id,
                    amount=-amount,
                    transaction_type=TransactionType.ADMIN_REMOVE,
                    description=description,
                    admin_id=admin_id
                )
                session.add(transaction)
                
                await session.commit()
                return True
            return False

    async def get_transactions(
        self,
        user_id: Optional[int] = None,
        limit: int = 50
    ) -> list[CoinTransaction]:
        """Get transaction history"""
        async with self.session_maker() as session:
            query = select(CoinTransaction)
            if user_id:
                query = query.where(CoinTransaction.user_id == user_id)
            query = query.order_by(CoinTransaction.created_at.desc()).limit(limit)
            result = await session.execute(query)
            return list(result.scalars().all())

    async def get_total_coins_in_system(self) -> int:
        """Get total KiberCoins in the system"""
        async with self.session_maker() as session:
            users = await session.execute(select(User))
            total = sum(user.coins for user in users.scalars().all())
            return total
