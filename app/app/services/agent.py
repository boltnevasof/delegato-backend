import uuid

from app.core.constants import AgentStatus
from app.exceptions.base import NotFound
from app.models.agent import Agent
from app.repositories.agent import AgentRepository
from app.repositories.agent_channel import AgentChannelRepository
from app.repositories.agent_skill import AgentSkillRepository
from app.repositories.agent_tool import AgentToolRepository
from app.repositories.server import ServerRepository
from app.services.dto.agent import AgentDetailDTO
from app.services.skill import SkillService
from app.tasks.ai import enhance_content_task, generate_soul_md_task
from app.tasks.provisioning import configure_agent


class AgentService:
    def __init__(
        self,
        agent_repository: AgentRepository,
        agent_skill_repository: AgentSkillRepository,
        agent_tool_repository: AgentToolRepository,
        agent_channel_repository: AgentChannelRepository,
        server_repository: ServerRepository,
        skill_service: SkillService,
    ) -> None:
        self._repo = agent_repository
        self._skill_repo = agent_skill_repository
        self._tool_repo = agent_tool_repository
        self._channel_repo = agent_channel_repository
        self._server_repo = server_repository
        self._skill_service = skill_service

    async def create_agent(self, user_id: uuid.UUID) -> Agent:
        return await self._repo.create(user_id)

    async def get_or_create_agent(self, user_id: uuid.UUID) -> Agent:
        agent = await self._repo.get_by_user_id(user_id)
        if agent is None:
            agent = await self._repo.create(user_id)
        return agent

    async def get_by_user(self, user_id: uuid.UUID) -> Agent:
        agent = await self._repo.get_by_user_id(user_id)
        if agent is None:
            raise NotFound(detail="Agent not found")
        return agent

    async def update_status(self, agent_id: uuid.UUID, status: AgentStatus) -> Agent:
        agent = await self._repo.update(agent_id, status=status)
        if agent is None:
            raise NotFound(detail="Agent not found")
        return agent

    async def get_detail(self, agent_id: uuid.UUID) -> AgentDetailDTO:
        agent = await self._repo.get_by_id(agent_id)
        if agent is None:
            raise NotFound(detail="Agent not found")

        skills = await self._skill_repo.get_by_agent_id(agent_id)
        tools = await self._tool_repo.get_by_agent_id(agent_id)
        channels = await self._channel_repo.get_by_agent_id(agent_id)
        server = await self._server_repo.get_by_agent_id(agent_id)

        return AgentDetailDTO(
            id=agent.id,
            status=agent.status.value,
            soul_md=agent.soul_md,
            agent_md=agent.agent_md,
            onboarding_step=agent.onboarding_step,
            skills=[
                {"id": s.skill.id, "slug": s.skill.slug, "is_enabled": s.is_enabled}
                for s in skills
            ],
            tools=[
                {"id": t.tool.id, "slug": t.tool.slug, "is_enabled": t.is_enabled}
                for t in tools
            ],
            channels=[
                {"id": c.id, "type": c.channel_type.value, "status": c.status.value}
                for c in channels
            ],
            server={
                "id": server.id,
                "status": server.status.value,
                "ip_address": server.ip_address,
            } if server else None,
        )

    async def describe(self, agent_id: uuid.UUID, business_description: str) -> str:
        task = await generate_soul_md_task.kiq(str(agent_id), business_description)
        return task.task_id

    async def skip_describe(self, agent_id: uuid.UUID) -> dict:
        default_soul = "# SOUL.md\n\nDefault personality template. Please customize."
        default_agent = "# AGENT.md\n\nDefault agent configuration. Please customize."
        await self._repo.update(
            agent_id, soul_md=default_soul, agent_md=default_agent, onboarding_step=1,
        )
        return {"soul_md": default_soul, "agent_md": default_agent}

    async def select_skills(
        self, agent_id: uuid.UUID, skill_ids: list[uuid.UUID], preset_slug: str | None,
    ) -> list:
        if preset_slug:
            return await self._skill_service.activate_preset(agent_id, preset_slug)
        return await self._skill_service.activate_skills(agent_id, skill_ids)

    async def complete_onboarding(self, agent_id: uuid.UUID) -> Agent:
        agent = await self._repo.update(
            agent_id, status=AgentStatus.CONFIGURING, onboarding_step=4,
        )
        if agent is None:
            raise NotFound(detail="Agent not found")

        # Push agent config (SOUL.md, skills, tools, channels) to the server
        server = await self._server_repo.get_by_agent_id(agent_id)
        if server is not None:
            await configure_agent.kiq(str(server.id))

        return agent

    async def update_onboarding_step(self, agent_id: uuid.UUID, step: int) -> None:
        await self._repo.update(agent_id, onboarding_step=step)

    async def update_soul_md(self, agent_id: uuid.UUID, content: str) -> Agent:
        agent = await self._repo.update(agent_id, soul_md=content)
        if agent is None:
            raise NotFound(detail="Agent not found")
        return agent

    async def update_agent_md(self, agent_id: uuid.UUID, content: str) -> Agent:
        agent = await self._repo.update(agent_id, agent_md=content)
        if agent is None:
            raise NotFound(detail="Agent not found")
        return agent

    async def request_enhance(self, agent_id: uuid.UUID, field: str, content: str) -> str:
        task = await enhance_content_task.kiq(str(agent_id), field, content)
        return task.task_id
