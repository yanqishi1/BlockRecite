from .doubao_service import get_doubao_answer
from .google_service import google_trans_voice_to_text

def get_voice_trans_answer(voice_path, voice_model="google_voice_to_text", gpt_model="doubao"):
    speech_text = trans_voice_to_text(voice_path, voice_model)
    transcription_text = get_gpt_answer(speech_text, gpt_model)

    return speech_text, transcription_text


def trans_voice_to_text(voice_path, voice_model):
    if voice_model == 'google_voice_to_text':
        text = google_trans_voice_to_text(voice_path)
        return text
    else:
        raise ValueError("Don't support this model:{}".format(voice_model))
    return None


def get_gpt_answer(speech_text, gpt_model):
    if gpt_model.startswith('doubao'):
        res = get_doubao_answer(speech_text)
        if res is not None:
            return res.message.content
        else:
            return None
    else:
        raise ValueError("Don't support this model:{}".format(gpt_model))