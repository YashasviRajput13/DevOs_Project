from app.config import get_settings
from groq import Groq

settings = get_settings()

client = Groq(api_key=settings.GROQ_API_KEY)

try:
    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[
            {
                "role": "user",
                "content": "Reply with exactly: GROQ OK"
            }
        ],
        max_tokens=10,
    )
    print(response.choices[0].message.content)
except Exception as e:
    print(f"Groq credentials are invalid or revoked; application code is loading the key but Groq rejected it.")
