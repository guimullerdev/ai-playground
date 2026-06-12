from dotenv import load_dotenv
load_dotenv()

import asyncio
from core.backend import get_llm


async def main():
    llm = get_llm()
    print(f"Model: {llm}")

    response = await llm.create(
        messages=[{"role": "user", "content": "Reply with exactly: CONNECTION OK"}]
    )
    print(f"Response: {response.get_text_content()}")


asyncio.run(main())
