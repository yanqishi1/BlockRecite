import requests

from .doubao_service import get_doubao_answer
from .google_service import google_trans_voice_to_text

def get_voice_trans_answer(voice_path, voice_model="sense_voice_to_text", gpt_model="doubao"):
    speech_text = trans_voice_to_text(voice_path, voice_model)
    transcription_text = get_gpt_answer(speech_text, gpt_model)

    return speech_text, transcription_text


def trans_voice_to_text(voice_path, voice_model):
    if voice_model == 'google_voice_to_text':
        text = google_trans_voice_to_text(voice_path)
        print("Google voice:",text)
        return text
    elif voice_model == 'sense_voice_to_text':
        text = call_sense_voice_api(voice_path)
        print("SenceVoice voice:",text)
        return text
    else:
        raise ValueError("Don't support this model:{}".format(voice_model))
    return None


def call_sense_voice_api(audio_file_path):
    url = "https://320g424385.hsk.top/api/sense_voice_to_text"
    files = {"audio_file": open(audio_file_path, "rb")}

    try:
        response = requests.post(url, files=files)
        response.raise_for_status()  # Raise an error for HTTP codes 4xx/5xx
        return response.json()['text']

    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def get_gpt_answer(speech_text, gpt_model):
    if gpt_model.startswith('doubao'):
        res = get_doubao_answer(speech_text)
        if res is not None:
            return res.message.content
        else:
            return None
    else:
        raise ValueError("Don't support this model:{}".format(gpt_model))