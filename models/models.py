import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base
from .enums import (
    ButtonTypeEnum,
    ContentTypeEnum,
    NewsletterStatusEnum,
    TargetAudienceEnum,
)

target_audience_enum = ENUM(TargetAudienceEnum, name="targetaudienceenum")
newsletter_status_enum = ENUM(NewsletterStatusEnum, name="newsletterstatusenum")
content_type_enum = ENUM(ContentTypeEnum, name="contenttypeenum")
button_type_enum = ENUM(ButtonTypeEnum, name="buttontypeenum")
class Role(Base):
    __tablename__ = "ROLES"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(sa.String, unique=True)
    permissions: Mapped[dict] = mapped_column(sa.JSON, nullable=True)
    users: Mapped[list["User"]] = relationship(back_populates="role")
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(sa.String, unique=True, index=True)
    telegram_id: Mapped[int] = mapped_column(sa.BigInteger, unique=True, index=True)
    role_id: Mapped[int] = mapped_column(sa.ForeignKey("ROLES.id"))
    role: Mapped["Role"] = relationship(back_populates="users")
    created_newsletters: Mapped[list["Newsletter"]] = relationship(
        back_populates="creator"
    )
class Newsletter(Base):
    __tablename__ = "newsletters"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    creator_id: Mapped[int] = mapped_column(sa.ForeignKey("users.id"))
    text: Mapped[str] = mapped_column(sa.Text, nullable=True)
    target_audience: Mapped[TargetAudienceEnum] = mapped_column(target_audience_enum)
    created_at: Mapped[sa.DateTime] = mapped_column(
        sa.DateTime, server_default=sa.func.now()
    )
    scheduled_at: Mapped[sa.DateTime] = mapped_column(sa.DateTime, nullable=True)
    status: Mapped[NewsletterStatusEnum] = mapped_column(
        newsletter_status_enum, default=NewsletterStatusEnum.DRAFT
    )
    content_type: Mapped[ContentTypeEnum] = mapped_column(
        content_type_enum,
        nullable=False,
        server_default="TEXT",
    )
    creator: Mapped["User"] = relationship(back_populates="created_newsletters")
    media_files: Mapped[list["NewsletterMedia"]] = relationship(
        back_populates="newsletter", cascade="all, delete-orphan"
    )
    inline_buttons: Mapped[list["NewsletterButton"]] = relationship(
        back_populates="newsletter", cascade="all, delete-orphan"
    )
class NewsletterMedia(Base):
    __tablename__ = "newsletter_media"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    newsletter_id: Mapped[int] = mapped_column(sa.ForeignKey("newsletters.id"))
    file_id: Mapped[str] = mapped_column(sa.String, nullable=False)
    file_unique_id: Mapped[str] = mapped_column(
        sa.String, nullable=True
    )
    file_type: Mapped[str] = mapped_column(
        sa.String, nullable=False
    )
    file_size: Mapped[int] = mapped_column(
        sa.Integer, nullable=True
    )
    mime_type: Mapped[str] = mapped_column(sa.String, nullable=True)
    file_name: Mapped[str] = mapped_column(
        sa.String, nullable=True
    )
    newsletter: Mapped["Newsletter"] = relationship(back_populates="media_files")
class NewsletterButton(Base):
    __tablename__ = "newsletter_buttons"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    newsletter_id: Mapped[int] = mapped_column(sa.ForeignKey("newsletters.id"))
    text: Mapped[str] = mapped_column(sa.String, nullable=False)
    button_type: Mapped[ButtonTypeEnum] = mapped_column(
        button_type_enum, default=ButtonTypeEnum.URL
    )
    url: Mapped[str] = mapped_column(sa.String, nullable=True)
    callback_data: Mapped[str] = mapped_column(
        sa.String, nullable=True
    )
    row_position: Mapped[int] = mapped_column(
        sa.Integer, default=0
    )
    column_position: Mapped[int] = mapped_column(
        sa.Integer, default=0
    )
    newsletter: Mapped["Newsletter"] = relationship(back_populates="inline_buttons")
