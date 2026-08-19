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

async def send_text(text: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/transactions/text",
            json={"text": text}
        )
    return response


async def authorize_user(telegram_id: int, username: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8088/api/v1/auth/telegram",
            json={"telegram_id": telegram_id, "username": username}
        )
    return response

async def get_report(date_from: str, date_to: str, token: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8088/api/v1/reports",
            json={"date_from": date_from, "date_to": date_to},
            headers={"Authorization": f"Bearer {token}"}
        )
    return response