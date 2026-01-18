from datetime import datetime
from sqlalchemy import BigInteger, String, DateTime, Boolean, Enum, Text, Integer, ForeignKey, Numeric
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
import enum


class UserRole(enum.Enum):
    """User roles enum"""
    USER = "user"
    ADMIN = "admin"


class ChatType(enum.Enum):
    """Chat type enum"""
    GROUP = "group"
    SUPERGROUP = "supergroup"
    CHANNEL = "channel"


class TransactionType(enum.Enum):
    """Transaction type enum"""
    REFERRAL_BONUS = "referral_bonus"
    ADMIN_ADD = "admin_add"
    ADMIN_REMOVE = "admin_remove"


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str] = mapped_column(String(255), nullable=True)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=True)
    preferred_name: Mapped[str] = mapped_column(String(255), nullable=True)
    language_code: Mapped[str] = mapped_column(String(10), nullable=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_registered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # KiberCoin fields
    referral_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=True, index=True)
    referred_by_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=True)
    coins: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<User(telegram_id={self.telegram_id}, preferred_name={self.preferred_name}, role={self.role.value})>"


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    chat_type: Mapped[ChatType] = mapped_column(Enum(ChatType), nullable=False)
    username: Mapped[str] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    bot_is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    bot_permissions: Mapped[str] = mapped_column(Text, nullable=True)  # JSON string
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    member_count: Mapped[int] = mapped_column(Integer, nullable=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    left_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Group(chat_id={self.chat_id}, title={self.title}, bot_is_admin={self.bot_is_admin}, is_active={self.is_active})>"


class CoinTransaction(Base):
    """KiberCoin transaction history"""
    __tablename__ = "coin_transactions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)  # Positive for add, negative for remove
    transaction_type: Mapped[TransactionType] = mapped_column(Enum(TransactionType), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    admin_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=True)  # For admin transactions
    related_user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=True)  # For referral transactions
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<CoinTransaction(user_id={self.user_id}, amount={self.amount}, type={self.transaction_type.value})>"
