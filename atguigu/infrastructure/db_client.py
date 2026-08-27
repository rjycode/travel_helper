import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine


from atguigu.config.settings import settings

session_engine:AsyncEngine | None = None

session_factory: async_sessionmaker[AsyncSession] | None = None

def init_db_engine():
    global session_engine,session_factory

    db_url = settings.chat_database_url or settings.database_url
    session_engine = create_async_engine(url=db_url,echo=True)
    session_factory = async_sessionmaker(session_engine, expire_on_commit=False)


async def dispose_engine():
    await session_engine.dispose()



async def main_test():
    init_db_engine()

    async with session_factory() as session:
        cursor = await session.execute(text("select 1"))
        print(cursor.mappings().fetchone())


    await dispose_engine()


if __name__ == '__main__':

    asyncio.run(main_test())




