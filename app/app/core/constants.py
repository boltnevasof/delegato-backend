import enum


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"


class AuthProvider(str, enum.Enum):
    EMAIL = "email"
    GOOGLE = "google"
    TELEGRAM = "telegram"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    PAST_DUE = "past_due"
    GRACE_PERIOD = "grace_period"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class AgentStatus(str, enum.Enum):
    PENDING_SETUP = "pending_setup"
    CONFIGURING = "configuring"
    ACTIVE = "active"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class ServerStatus(str, enum.Enum):
    PROVISIONING = "provisioning"
    CONFIGURING = "configuring"
    ACTIVE = "active"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    DESTROYED = "destroyed"


class ProvisioningTaskStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ProvisioningTaskType(str, enum.Enum):
    PROVISION = "provision"
    CONFIGURE = "configure"
    UPDATE_CONFIG = "update_config"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"


class NotificationType(str, enum.Enum):
    SERVER_READY = "server_ready"
    SERVER_ERROR = "server_error"
    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAILED = "payment_failed"
    SUBSCRIPTION_EXPIRING = "subscription_expiring"
    AGENT_STOPPED = "agent_stopped"


class NotificationChannel(str, enum.Enum):
    TELEGRAM = "telegram"
    EMAIL = "email"


class NotificationStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class ChannelType(str, enum.Enum):
    TELEGRAM = "telegram"


class ChannelStatus(str, enum.Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class SkillAccessLevel(str, enum.Enum):
    BASIC = "basic"
    ALL = "all"


class CustomRequestStatus(str, enum.Enum):
    NEW = "new"
    CONTACTED = "contacted"
    CLOSED = "closed"


class SupportRequestStatus(str, enum.Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"


class ServerLogLevel(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
