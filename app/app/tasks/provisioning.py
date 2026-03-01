import uuid

from loguru import logger

from app.broker import broker
from app.core.constants import ProvisioningTaskStatus
from app.db.engine import async_session_factory
from app.repositories.agent import AgentRepository
from app.repositories.agent_channel import AgentChannelRepository
from app.repositories.agent_skill import AgentSkillRepository
from app.repositories.agent_tool import AgentToolRepository
from app.repositories.provisioning import ProvisioningTaskRepository
from app.repositories.server import ServerRepository
from app.repositories.server_log import ServerLogRepository
from app.services.provisioning import ProvisioningService

ANSIBLE_MAX_RETRIES = 3


def _create_provisioning_service(session) -> ProvisioningService:
    return ProvisioningService(
        server_repository=ServerRepository(session),
        server_log_repository=ServerLogRepository(session),
        provisioning_repository=ProvisioningTaskRepository(session),
        agent_repository=AgentRepository(session),
        agent_skill_repository=AgentSkillRepository(session),
        agent_tool_repository=AgentToolRepository(session),
        agent_channel_repository=AgentChannelRepository(session),
    )


@broker.task(retry_on_error=True, max_retries=3)
async def provision_server(server_id: str) -> dict:
    """Full provisioning: Terraform -> Ansible -> active."""
    sid = uuid.UUID(server_id)
    logger.info("Starting server provisioning: {server_id}", server_id=server_id)

    async with async_session_factory() as session:
        service = _create_provisioning_service(session)
        prov_repo = ProvisioningTaskRepository(session)

        tasks = await prov_repo.get_by_server_id(sid)
        task = tasks[0] if tasks else None
        if task:
            await prov_repo.update_status(task.id, ProvisioningTaskStatus.RUNNING)

        try:
            ip = await service.run_terraform(sid)
            if not ip:
                await service.mark_error(sid, "Terraform failed to return IP")
                if task:
                    await prov_repo.update_status(task.id, ProvisioningTaskStatus.FAILED)
                await session.commit()
                return {"success": False, "error": "Terraform failed"}

            # Ansible with retries — avoid leaving dead servers running
            ansible_success = False
            for attempt in range(1, ANSIBLE_MAX_RETRIES + 1):
                logger.info(
                    "Ansible attempt {attempt}/{max} for server {server_id}",
                    attempt=attempt,
                    max=ANSIBLE_MAX_RETRIES,
                    server_id=server_id,
                )
                ansible_success = await service.run_ansible(sid)
                if ansible_success:
                    break
                if task:
                    await prov_repo.increment_retry(task.id)

            if not ansible_success:
                await service.mark_error(sid, "Ansible configuration failed after max retries")
                if task:
                    await prov_repo.update_status(task.id, ProvisioningTaskStatus.FAILED)

                # Destroy the VPS to avoid paying for dead servers
                logger.warning(
                    "Destroying server {server_id} after {max} failed Ansible attempts",
                    server_id=server_id,
                    max=ANSIBLE_MAX_RETRIES,
                )
                await service.destroy_server(sid)
                await session.commit()
                return {"success": False, "error": "Ansible failed, server destroyed"}

            if task:
                await prov_repo.update_status(task.id, ProvisioningTaskStatus.COMPLETED)
            await session.commit()

            logger.info("Server provisioning completed: {server_id}", server_id=server_id)
            return {"success": True, "ip_address": ip}

        except Exception as e:
            await service.mark_error(sid, str(e))
            if task:
                await prov_repo.increment_retry(task.id)
                await prov_repo.update_status(task.id, ProvisioningTaskStatus.FAILED)
            await session.commit()
            raise


@broker.task
async def configure_agent(server_id: str) -> dict:
    """Post-onboarding Ansible config deployment."""
    sid = uuid.UUID(server_id)
    logger.info("Starting agent config update: {server_id}", server_id=server_id)

    async with async_session_factory() as session:
        service = _create_provisioning_service(session)
        success = await service.run_config_update(sid)
        await session.commit()

    return {"success": success}


@broker.task
async def update_agent_config(server_id: str) -> dict:
    """Apply SOUL.md/skill/tool/channel changes to server via Ansible."""
    sid = uuid.UUID(server_id)
    logger.info("Updating agent config on server: {server_id}", server_id=server_id)

    async with async_session_factory() as session:
        service = _create_provisioning_service(session)
        success = await service.run_config_update(sid)
        await session.commit()

    return {"success": success}
