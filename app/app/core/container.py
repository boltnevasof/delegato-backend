from dependency_injector import containers, providers

from app.core.config import settings
from app.db.engine import get_async_session

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
            "app.main",
        ],
    )

    # --- Session ---
    db_session = providers.Resource(get_async_session)

    # --- Repositories ---
    user_repository = providers.Factory(UserRepository, session=db_session)
    auth_method_repository = providers.Factory(
        UserAuthMethodRepository, session=db_session,
    )
    otp_repository = providers.Factory(OTPCodeRepository, session=db_session)
    refresh_token_repository = providers.Factory(
        RefreshTokenRepository, session=db_session,
    )
    tariff_repository = providers.Factory(TariffRepository, session=db_session)
    subscription_repository = providers.Factory(
        SubscriptionRepository, session=db_session,
    )
    agent_repository = providers.Factory(AgentRepository, session=db_session)
    payment_repository = providers.Factory(PaymentRepository, session=db_session)
    custom_request_repository = providers.Factory(
        CustomTariffRequestRepository, session=db_session,
    )
    server_repository = providers.Factory(ServerRepository, session=db_session)
    server_log_repository = providers.Factory(ServerLogRepository, session=db_session)
    provisioning_repository = providers.Factory(
        ProvisioningTaskRepository, session=db_session,
    )
    skill_catalog_repository = providers.Factory(
        SkillCatalogRepository, session=db_session,
    )
    agent_skill_repository = providers.Factory(
        AgentSkillRepository, session=db_session,
    )
    agent_channel_repository = providers.Factory(
        AgentChannelRepository, session=db_session,
    )
    tool_catalog_repository = providers.Factory(
        ToolCatalogRepository, session=db_session,
    )
    agent_tool_repository = providers.Factory(AgentToolRepository, session=db_session)

    # --- External services ---
    email_service = providers.Singleton(UnisenderEmailService)
    payment_gateway = providers.Singleton(_create_payment_gateway)

    # --- Services ---
    auth_service = providers.Factory(
        AuthService,
        user_repository=user_repository,
        auth_method_repository=auth_method_repository,
        otp_repository=otp_repository,
        refresh_token_repository=refresh_token_repository,
        email_service=email_service,
    )

    user_service = providers.Factory(
        UserService,
        user_repository=user_repository,
        agent_repository=agent_repository,
        subscription_repository=subscription_repository,
        tariff_repository=tariff_repository,
    )

    tariff_service = providers.Factory(
        TariffService,
        tariff_repository=tariff_repository,
        custom_request_repository=custom_request_repository,
    )

    subscription_service = providers.Factory(
        SubscriptionService,
        subscription_repository=subscription_repository,
        tariff_repository=tariff_repository,
    )

    skill_service = providers.Factory(
        SkillService,
        skill_catalog_repository=skill_catalog_repository,
        agent_skill_repository=agent_skill_repository,
    )

    channel_service = providers.Factory(
        ChannelService,
        agent_channel_repository=agent_channel_repository,
    )

    tool_service = providers.Factory(
        ToolService,
        tool_catalog_repository=tool_catalog_repository,
        agent_tool_repository=agent_tool_repository,
    )

    server_service = providers.Factory(
        ServerService,
        server_repository=server_repository,
        agent_repository=agent_repository,
        server_log_repository=server_log_repository,
    )

    agent_service = providers.Factory(
        AgentService,
        agent_repository=agent_repository,
        agent_skill_repository=agent_skill_repository,
        agent_tool_repository=agent_tool_repository,
        agent_channel_repository=agent_channel_repository,
        server_repository=server_repository,
        skill_service=skill_service,
    )

    provisioning_service = providers.Factory(
        ProvisioningService,
        server_repository=server_repository,
        server_log_repository=server_log_repository,
        provisioning_repository=provisioning_repository,
        agent_repository=agent_repository,
        agent_skill_repository=agent_skill_repository,
        agent_tool_repository=agent_tool_repository,
        agent_channel_repository=agent_channel_repository,
    )

    payment_service = providers.Factory(
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
