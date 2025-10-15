import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect(
        "postgresql://kbju_user:securepassword123@127.0.0.1:5432/kbju"
    )
    print("✅ Connected successfully!")
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
