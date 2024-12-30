from volcenginesdkarkruntime import Ark

api_key = "ba1b20a3-61a0-4033-b3d0-a2b95acd6ab0"

client = Ark(
    api_key=api_key,
    base_url="https://ark.cn-beijing.volces.com/api/v3",
)

def get_doubao_answer(text):
    text = text+"  简介一点，不要例句和举例"
    response = client.chat.completions.create(
        model="ep-20241226110703-dr8cr",
        messages = [
            {"role": "system", "content": "你豆包，一个AI英语翻译助手"},
            {"role": "user", "content": text},
        ],
    )
    print("doubao response:", response)
    return response.choices[0]