from volcenginesdkarkruntime import Ark

api_key = "ba1b20a3-61a0-4033-b3d0-a2b95acd6ab0"

client = Ark(
    api_key=api_key,
    base_url="https://ark.cn-beijing.volces.com/api/v3",
)

def get_doubao_answer(text):
    response = client.chat.completions.create(
        model="ep-20241215205247-5xglc",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": text},
                ],
            }
        ],
    )
    return response.choices[0]