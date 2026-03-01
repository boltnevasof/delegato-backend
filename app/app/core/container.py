from dependency_injector import containers, providers

from app.core.config import settings
from app.db.engine import create_session

# Repositories
from app.repositories.agent import AgentRepository
from app.repositories.agent_channel import AgentChannelRepository
from app.repositories.agent_skill import AgentSkillRepository
from app.repositories.agent_tool import AgentToolRepository
from app.repositories.auth_method import UserAuthMethodRepository
from app.repositories.custom_request import CustomTariffRequestRepository
from app.repositories.otp import OTPCodeRepository
from app.repositories.payment import PaymentRepository
from app.repositories.provisioning import ProvisioningTaskRepository
from app.repositories.refresh_token import RefreshTokenRepository
from app.repositories.server import ServerRepository
from app.repositories.server_log import ServerLogRepository
from app.repositories.skill import SkillCatalogRepository
from app.repositories.subscription import SubscriptionRepository
from app.repositories.tariff import TariffRepository
from app.repositories.tool import ToolCatalogRepository
from app.repositories.user import UserRepository

# Services
from app.services.agent import AgentService
from app.services.auth import AuthService
from app.services.channel import ChannelService
from app.services.email.unisender import UnisenderEmailService
from app.services.payment.base import PaymentGateway
from app.services.payment.tbank import TBankPaymentGateway
from app.services.payment.yookassa import YooKassaPaymentGateway
from app.services.payment_service import PaymentService
from app.services.provisioning import ProvisioningService
from app.services.server import ServerService
from app.services.skill import SkillService
from app.services.tool import ToolService
from app.services.subscription import SubscriptionService
from app.services.tariff import TariffService
from app.services.user import UserService


def _create_payment_gateway() -> PaymentGateway:
    if settings.PAYMENT_PROVIDER == "yookassa":
        return YooKassaPaymentGateway()
    return TBankPaymentGateway()


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=[
            "app.api.v1.endpoints.auth",
            "app.api.v1.endpoints.users",
            "app.api.v1.endpoints.tariffs",
            "app.api.v1.endpoints.payments",
            "app.api.v1.endpoints.agents",
            "app.api.v1.endpoints.skills",
            "app.api.v1.endpoints.servers",
            "app.api.v1.endpoints.tools",
            "app.api.v1.endpoints.channels",
            "app.api.v1.endpoints.subscriptions",
            "app.api.v1.endpoints.admin",
            "app.api.deps",
            "app.main",
        ],
    )

    # --- Session factory: каждый вызов Container.session() = новая сессия ---
    session = providers.Factory(create_session)

    # --- Repositories (singletons — session из ContextVar в каждом методе) ---
    user_repository = providers.Singleton(UserRepository)
    auth_method_repository = providers.Singleton(UserAuthMethodRepository)
    otp_repository = providers.Singleton(OTPCodeRepository)
    refresh_token_repository = providers.Singleton(RefreshTokenRepository)
    tariff_repository = providers.Singleton(TariffRepository)
    subscription_repository = providers.Singleton(SubscriptionRepository)
    agent_repository = providers.Singleton(AgentRepository)
    payment_repository = providers.Singleton(PaymentRepository)
    custom_request_repository = providers.Singleton(CustomTariffRequestRepository)
    server_repository = providers.Singleton(ServerRepository)
    server_log_repository = providers.Singleton(ServerLogRepository)
    provisioning_repository = providers.Singleton(ProvisioningTaskRepository)
    skill_catalog_repository = providers.Singleton(SkillCatalogRepository)
    agent_skill_repository = providers.Singleton(AgentSkillRepository)
    agent_channel_repository = providers.Singleton(AgentChannelRepository)
    tool_catalog_repository = providers.Singleton(ToolCatalogRepository)
    agent_tool_repository = providers.Singleton(AgentToolRepository)

    # --- External services ---
    email_service = providers.Singleton(UnisenderEmailService)
    payment_gateway = providers.Singleton(_create_payment_gateway)

    # --- Services ---
    auth_service = providers.Singleton(
        AuthService,
        user_repository=user_repository,
        auth_method_repository=auth_method_repository,
        otp_repository=otp_repository,
        refresh_token_repository=refresh_token_repository,
        email_service=email_service,
    )

    user_service = providers.Singleton(
        UserService,
        user_repository=user_repository,
        agent_repository=agent_repository,
        subscription_repository=subscription_repository,
        tariff_repository=tariff_repository,
    )

    tariff_service = providers.Singleton(
        TariffService,
        tariff_repository=tariff_repository,
        custom_request_repository=custom_request_repository,
    )

    subscription_service = providers.Singleton(
        SubscriptionService,
        subscription_repository=subscription_repository,
        tariff_repository=tariff_repository,
    )

    skill_service = providers.Singleton(
        SkillService,
        skill_catalog_repository=skill_catalog_repository,
        agent_skill_repository=agent_skill_repository,
    )

    channel_service = providers.Singleton(
        ChannelService,
        agent_channel_repository=agent_channel_repository,
    )

    tool_service = providers.Singleton(
        ToolService,
        tool_catalog_repository=tool_catalog_repository,
        agent_tool_repository=agent_tool_repository,
    )

    server_service = providers.Singleton(
        ServerService,
        server_repository=server_repository,
        agent_repository=agent_repository,
        server_log_repository=server_log_repository,
    )

    agent_service = providers.Singleton(
        AgentService,
        agent_repository=agent_repository,
        agent_skill_repository=agent_skill_repository,
        agent_tool_repository=agent_tool_repository,
        agent_channel_repository=agent_channel_repository,
        server_repository=server_repository,
        skill_service=skill_service,
    )

    provisioning_service = providers.Singleton(
        ProvisioningService,
        server_repository=server_repository,
        server_log_repository=server_log_repository,
        provisioning_repository=provisioning_repository,
        agent_repository=agent_repository,
        agent_skill_repository=agent_skill_repository,
        agent_tool_repository=agent_tool_repository,
        agent_channel_repository=agent_channel_repository,
    )

    payment_service = providers.Singleton(
        PaymentService,
        payment_repository=payment_repository,
        subscription_repository=subscription_repository,
        tariff_repository=tariff_repository,
        agent_repository=agent_repository,
        server_repository=server_repository,
        payment_gateway=payment_gateway,
        subscription_service=subscription_service,
        agent_service=agent_service,
        server_service=server_service,
    )
