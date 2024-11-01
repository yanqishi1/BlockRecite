from gtts import gTTS
import os

def generate_voice_by_text(text, front_id, lang='en'):
    if text is None or len(text) == 0:
        return None
    try:
        tts = gTTS(text=text, lang=lang)

        audio_file_path = get_voice_path(front_id)
        if os.path.exists(audio_file_path):
            # 如果音频文件存在，直接返回路径
            return audio_file_path

        tts.save(audio_file_path)

        return audio_file_path
    except Exception as e:
        print(e)
        return None

def remove_voice(front_id):
    audio_file_path = get_voice_path(front_id)
    if os.path.exists(audio_file_path):
        os.remove(audio_file_path)


def get_voice_path(front_id):
    if front_id is None:
        return ""
    return './tmp/generated_audio_' + str(front_id) + ".mp3"