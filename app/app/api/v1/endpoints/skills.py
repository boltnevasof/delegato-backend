import uuid

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, manage_session
from app.api.v1.schemas.skill import (
    AddSkillRequest,
    AgentSkillResponse,
    SkillCatalogItem,
    SkillCatalogResponse,
    SkillPresetItem,
    ToggleSkillRequest,
)
from app.core.container import Container
from app.models.user import User
from app.services.agent import AgentService
from app.services.skill import SkillService

router = APIRouter(tags=["skills"])


@router.get(
    "/skills/catalog",
    response_model=SkillCatalogResponse,
    summary="Каталог навыков",
    description="Возвращает полный каталог доступных навыков и пресеты (готовые наборы навыков).",
)
@inject
@manage_session
async def get_skill_catalog(
    current_user: User = Depends(get_current_user),
    skill_service: SkillService = Depends(Provide[Container.skill_service]),
) -> SkillCatalogResponse:
    catalog = await skill_service.get_catalog()
    return SkillCatalogResponse(
        skills=[SkillCatalogItem(**s) for s in catalog["skills"]],
        presets=[SkillPresetItem(**p) for p in catalog["presets"]],
    )


@router.post(
    "/agents/me/skills",
    response_model=AgentSkillResponse,
    status_code=201,
    summary="Добавить навык агенту",
    description="Активирует указанный навык из каталога для AI-агента текущего пользователя.",
)
@inject
@manage_session
async def add_skill(
    body: AddSkillRequest,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(Provide[Container.agent_service]),
    skill_service: SkillService = Depends(Provide[Container.skill_service]),
) -> AgentSkillResponse:
    agent = await agent_service.get_by_user(current_user.id)
    activated = await skill_service.activate_skills(agent.id, [body.skill_id])
    s = activated[0]
    return AgentSkillResponse(id=s.skill.id, slug=s.skill.slug, is_enabled=s.is_enabled)


@router.patch(
    "/agents/me/skills/{skill_id}",
    response_model=AgentSkillResponse,
    summary="Вкл/выкл навык",
    description="Включает или выключает ранее добавленный навык агента без удаления.",
)
@inject
@manage_session
async def toggle_skill(
    skill_id: uuid.UUID,
    body: ToggleSkillRequest,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(Provide[Container.agent_service]),
    skill_service: SkillService = Depends(Provide[Container.skill_service]),
) -> AgentSkillResponse:
    agent = await agent_service.get_by_user(current_user.id)
    agent_skill = await skill_service.toggle_skill(agent.id, skill_id, body.is_enabled)
    return AgentSkillResponse(
        id=agent_skill.skill.id, slug=agent_skill.skill.slug, is_enabled=agent_skill.is_enabled,
    )


@router.delete(
    "/agents/me/skills/{skill_id}",
    status_code=204,
    summary="Удалить навык",
    description="Полностью удаляет навык из агента. Для повторного использования потребуется добавить заново.",
)
@inject
@manage_session
async def remove_skill(
    skill_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(Provide[Container.agent_service]),
    skill_service: SkillService = Depends(Provide[Container.skill_service]),
) -> None:
    agent = await agent_service.get_by_user(current_user.id)
    await skill_service.remove_skill(agent.id, skill_id)
