# Yandex Cloud API: быстрый старт (OCR чеков + LLM)

Практический гайд для воспроизведения рабочих запросов к облаку в FinMate.

Секреты (`YANDEX_FOLDER_ID`, `YANDEX_API_KEY`) передаются **лично**, в репозиторий не коммитить.

## Используемые сервисы

| Роль | Сервис / модель | Зачем |
|------|-----------------|-------|
| CV: фото чека → текст | **Yandex Vision OCR** `recognizeText` | Прочитать сумму, магазин, позиции с чека |
| LLM: текст → структура расхода | **YandexGPT Pro** `gpt://<folder_id>/yandexgpt/latest` | Извлечь amount / category / details в JSON |

> Для FinMate CV = **OCR (текст)**, не детекция объектов. Multimodal LLM (Qwen и т.п.) для чеков не нужен на старте: сначала OCR, затем LLM по тексту.

## 1. Переменные окружения

```bash
export YANDEX_FOLDER_ID="..."
export YANDEX_API_KEY="..."
```

Либо положить в `backend/.env` (плейсхолдеры в `.env.example`):

```env
YANDEX_FOLDER_ID=...
YANDEX_API_KEY=...
```

## 2. CV: фото чека → текст (Vision OCR)

Подготовить JPEG (WebP под именем `.png` API часто не декодирует):

```bash
python - <<'PY'
from PIL import Image
Image.open("/path/to/receipt").convert("RGB").save("/tmp/receipt.jpg", "JPEG", quality=90)
print("ok")
PY
```

Запрос (тело в файл — base64 в argv у curl даёт `Argument list too long`):

```bash
python - <<'PY'
import base64, json, os, urllib.request, urllib.error

folder = os.environ["YANDEX_FOLDER_ID"]
key = os.environ["YANDEX_API_KEY"]

with open("/tmp/receipt.jpg", "rb") as f:
    content = base64.b64encode(f.read()).decode()

body = json.dumps({
    "mimeType": "JPEG",
    "languageCodes": ["ru", "en"],
    "model": "page",
    "content": content,
}).encode()

req = urllib.request.Request(
    "https://ocr.api.cloud.yandex.net/ocr/v1/recognizeText",
    data=body,
    headers={
        "Authorization": f"Api-Key {key}",
        "x-folder-id": folder,
        "Content-Type": "application/json",
    },
    method="POST",
)

try:
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode())
except urllib.error.HTTPError as e:
    print("HTTP", e.code, e.read().decode()[:1500])
    raise

text = data.get("result", {}).get("textAnnotation", {}).get("fullText", "")
print(text if text else json.dumps(data, ensure_ascii=False)[:2000])
PY
```

Ожидание: в `fullText` (или в блоках) читаемый текст чека — суммы, названия.

## 3. LLM: текст чека → структура расхода (YandexGPT Pro)

```bash
python - <<'PY'
import json, os, urllib.request, urllib.error

folder = os.environ["YANDEX_FOLDER_ID"]
key = os.environ["YANDEX_API_KEY"]

# подставить текст из OCR или пример:
receipt_text = """
МАГАЗИН ПЯТЁРОЧКА
Молоко 89.90
Хлеб 45.00
ИТОГО 134.90
"""

prompt = (
    "Из текста чека извлеки данные о расходе. "
    "Ответ строго JSON: "
    '{"amount": number, "currency": "RUB", "merchant": string|null, '
    '"category": string, "items": string[], "raw_summary": string}. '
    "Если суммы нет — amount: null. "
    f"Текст чека:\n{receipt_text}"
)

body = json.dumps({
    "model": f"gpt://{folder}/yandexgpt/latest",
    "temperature": 0.2,
    "max_tokens": 800,
    "messages": [{"role": "user", "content": prompt}],
}).encode()

req = urllib.request.Request(
    "https://llm.api.cloud.yandex.net/v1/chat/completions",
    data=body,
    headers={
        "Authorization": f"Api-Key {key}",
        "x-folder-id": folder,
        "Content-Type": "application/json",
    },
    method="POST",
)

try:
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode())
except urllib.error.HTTPError as e:
    print("HTTP", e.code, e.read().decode()[:1500])
    raise

print(data["choices"][0]["message"]["content"])
PY
```

Ожидание: JSON с суммой и категорией (иногда в \`\`\`json — нормально для smoke-теста).

Минимальный smoke LLM без чека:

```bash
curl -s https://llm.api.cloud.yandex.net/v1/chat/completions \
  -H "Authorization: Api-Key $YANDEX_API_KEY" \
  -H "x-folder-id: $YANDEX_FOLDER_ID" \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"gpt://$YANDEX_FOLDER_ID/yandexgpt/latest\",
    \"messages\": [{\"role\": \"user\", \"content\": \"Скажи одним словом: работает\"}],
    \"max_tokens\": 50
  }"
```

## 4. Типичные проблемы

| Симптом | Решение |
|---------|---------|
| `403 Forbidden` | Нет роли / scope на Vision или LLM; проверить SA и scopes ключа |
| `Can't decode image` | Неверный формат (часто WebP) → конвертировать в JPEG, `mimeType: "JPEG"` |
| `Argument list too long` | Не передавать base64 в argv curl — писать JSON в файл / слать из Python |
| Пустой `fullText` | Плохой свет/размытие чека или на фото нет текста; проверить другое фото |
| Ключ в git | Не коммитить `.env`; только плейсхолдеры в `.env.example` |

## Цепочка MVP

1. Фото чека → **Vision OCR** → `fullText`
2. `fullText` → **YandexGPT** → JSON расхода
3. Backend сохраняет транзакцию (уже существующие API категорий/транзакций)

Голос → текст (SpeechKit) в этот гайд не входит — отдельный шаг.
