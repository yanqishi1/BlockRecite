from volcengine.maas.v2 import MaasService

api_key = "ba1b20a3-61a0-4033-b3d0-a2b95acd6ab0"

maas = MaasService("https://ark.cn-beijing.volces.com/api/v3", "cn-beijing")
maas.set_ak(api_key)

def get_doubao_answer(text):
    text = text + "  简介一点，不要例句和举例"
    
    req = {
        "model": "ep-20241226110703-dr8cr",
        "messages": [
            {"role": "system", "content": "你豆包，一个AI英语翻译助手"},
            {"role": "user", "content": text},
        ],
    }
    
    resp = maas.chat(req)
    print("doubao response:", resp)
    return resp["choices"][0]["message"]
