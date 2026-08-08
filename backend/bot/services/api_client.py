import httpx

async def send_voice(file_path: str):
    async with httpx.AsyncClient() as client:
        with open(file_path, "rb") as f:
            response = await client.post(
                "http://localhost:8000/api/v1/transactions/voice",
                files={"voice": f}
            )
    return response

async def send_photo(file_path: str):
    async with httpx.AsyncClient() as client:
        with open(file_path, "rb") as f:
            response = await client.post(
                "http://localhost:8000/api/v1/transactions/photo",
                files={"photo": f}
            )
    return response

async def send_text(file_path: str):
    async with httpx.AsyncClient() as client:
        with open(file_path, "rb") as f:
            response = await client.post(
                "http://localhost:8000/api/v1/transactions/text",
                files={"text": f}
            )
    return response