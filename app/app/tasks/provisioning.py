import uuid

from loguru import logger

from app.broker import broker
from app.core.constants import ProvisioningTaskStatus
from app.db.engine import session_context

ANSIBLE_MAX_RETRIES = 3


@broker.task(retry_on_error=True, max_retries=3)
async def provision_server(server_id: str) -> dict:
    """Full provisioning: Terraform -> Ansible -> active."""
    sid = uuid.UUID(server_id)
    logger.info("Starting server provisioning: {server_id}", server_id=server_id)

    from app.core.container import Container
    session = Container.session()
    token = session_context.set(session)
    try:
        service = Container.provisioning_service()
        prov_repo = Container.provisioning_repository()

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
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
        session_context.reset(token)


@broker.task
async def configure_agent(server_id: str) -> dict:
    """Post-onboarding Ansible config deployment."""
    sid = uuid.UUID(server_id)
    logger.info("Starting agent config update: {server_id}", server_id=server_id)

    from app.core.container import Container
    session = Container.session()
    token = session_context.set(session)
    try:
        service = Container.provisioning_service()
        success = await service.run_config_update(sid)
        await session.commit()
        return {"success": success}
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
        session_context.reset(token)


@broker.task
async def update_agent_config(server_id: str) -> dict:
    """Apply SOUL.md/skill/tool/channel changes to server via Ansible."""
    sid = uuid.UUID(server_id)
    logger.info("Updating agent config on server: {server_id}", server_id=server_id)

    from app.core.container import Container
    session = Container.session()
    token = session_context.set(session)
    try:
        service = Container.provisioning_service()
        success = await service.run_config_update(sid)
        await session.commit()
        return {"success": success}
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
        session_context.reset(token)
