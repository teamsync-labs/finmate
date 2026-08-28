import httpx

from config import AUTH_ENDPOINT, PHOTO_ENDPOINT, REPORT_ENDPOINT, TEXT_ENDPOINT, VOICE_ENDPOINT


async def send_voice(file):
    async with httpx.AsyncClient() as client:
        response = await client.post(VOICE_ENDPOINT, files={"voice": file})
    return response


async def send_photo(file):
    async with httpx.AsyncClient() as client:
        response = await client.post(PHOTO_ENDPOINT, files={"photo": file})
    return response


async def send_text(text: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(TEXT_ENDPOINT, json={"text": text})
    return response


async def get_report(date_from: str, date_to: str, token: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            REPORT_ENDPOINT,
            json={"date_from": date_from, "date_to": date_to},
            headers={"Authorization": f"Bearer {token}"}
        )
    return response