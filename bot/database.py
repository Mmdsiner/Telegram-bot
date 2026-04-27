import asyncpg
from config import DATABASE_URL

pool = None

async def connect():
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL)

async def init_db():
    async with pool.acquire() as conn:
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS users(
            user_id BIGINT PRIMARY KEY
        )
        """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS payments(
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            amount INT,
            status TEXT
        )
        """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS settings(
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """)

        await conn.execute("""
        INSERT INTO settings(key,value) VALUES
        ('normal_price','400000'),
        ('vip_price','600000'),
        ('discount','0')
        ON CONFLICT DO NOTHING
        """)

async def fetch(query,*args):
    async with pool.acquire() as conn:
        return await conn.fetch(query,*args)

async def execute(query,*args):
    async with pool.acquire() as conn:
        return await conn.execute(query,*args)
