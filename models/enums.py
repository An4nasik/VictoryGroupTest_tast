import enum


class TargetAudienceEnum(enum.Enum):
    ALL = "all"
    USERS = "users"
    MODERATORS = "moderators"
    ADMINS = "admins"
class NewsletterStatusEnum(enum.Enum):
    DRAFT = "draft"
    PENDING = "pending"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    SENT = "sent"
class ContentTypeEnum(enum.Enum):
    TEXT = "text"
    PHOTO = "photo"
    VIDEO = "video"
    ANIMATION = "animation"
    DOCUMENT = "document"
class ButtonTypeEnum(enum.Enum):
    URL = "url"
    CALLBACK = "callback"
