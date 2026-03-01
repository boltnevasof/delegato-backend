import uuid

from app.core.constants import SkillAccessLevel
from app.exceptions.base import NotFound
from app.models.agent_skill import AgentSkill
from app.repositories.agent_skill import AgentSkillRepository
from app.repositories.skill import SkillCatalogRepository


class SkillService:
    def __init__(
        self,
        skill_catalog_repository: SkillCatalogRepository,
        agent_skill_repository: AgentSkillRepository,
    ) -> None:
        self._catalog_repo = skill_catalog_repository
        self._agent_skill_repo = agent_skill_repository

    async def get_catalog(self, user_tariff_access: SkillAccessLevel | None = None) -> dict:
        skills = await self._catalog_repo.list_active()
        presets = await self._catalog_repo.list_presets()
        return {
            "skills": [
                {
                    "id": s.id,
                    "slug": s.slug,
                    "name": s.name,
                    "description": s.description,
                    "access_level": s.access_level.value,
                    "available_for_user": (
                        user_tariff_access == SkillAccessLevel.ALL
                        or s.access_level == SkillAccessLevel.BASIC
                    ) if user_tariff_access else True,
                }
                for s in skills
            ],
            "presets": [
                {
                    "slug": p.slug,
                    "name": p.name,
                    "skill_ids": [s.id for s in p.skills],
                }
                for p in presets
            ],
        }

    async def activate_skills(
        self, agent_id: uuid.UUID, skill_ids: list[uuid.UUID],
    ) -> list[AgentSkill]:
        activated = []
        for skill_id in skill_ids:
            skill = await self._catalog_repo.get_by_id(skill_id)
            if skill is None:
                raise NotFound(detail=f"Skill {skill_id} not found")
            existing = await self._agent_skill_repo.get_by_agent_and_skill(agent_id, skill_id)
            if existing is None:
                agent_skill = await self._agent_skill_repo.create(agent_id, skill_id)
                activated.append(agent_skill)
            else:
                activated.append(existing)
        return activated

    async def activate_preset(
        self, agent_id: uuid.UUID, preset_slug: str,
    ) -> list[AgentSkill]:
        preset = await self._catalog_repo.get_preset_by_slug(preset_slug)
        if preset is None:
            raise NotFound(detail=f"Preset '{preset_slug}' not found")
        skill_ids = [s.id for s in preset.skills]
        return await self.activate_skills(agent_id, skill_ids)

    async def toggle_skill(
        self, agent_id: uuid.UUID, skill_id: uuid.UUID, is_enabled: bool,
    ) -> AgentSkill:
        agent_skill = await self._agent_skill_repo.get_by_agent_and_skill(agent_id, skill_id)
        if agent_skill is None:
            raise NotFound(detail="Skill not assigned to agent")
        await self._agent_skill_repo.update(agent_skill.id, is_enabled=is_enabled)
        agent_skill.is_enabled = is_enabled
        return agent_skill

    async def remove_skill(self, agent_id: uuid.UUID, skill_id: uuid.UUID) -> None:
        agent_skill = await self._agent_skill_repo.get_by_agent_and_skill(agent_id, skill_id)
        if agent_skill is None:
            raise NotFound(detail="Skill not assigned to agent")
        await self._agent_skill_repo.delete(agent_skill.id)
