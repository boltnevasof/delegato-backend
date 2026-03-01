from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession


async def paginate(
    session: AsyncSession,
    query: Select,
    page: int,
    per_page: int,
) -> tuple[list, int]:
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar_one()

    offset = (page - 1) * per_page
    paginated_query = query.offset(offset).limit(per_page)
    result = await session.execute(paginated_query)
    items = list(result.scalars().all())

    return items, total
