from gtts import gTTS
import os
import pyttsx3
def generate_voice_by_text(text, front_id, lang='en', option='tts'):
    if text is None or len(text) == 0:
        return None

    if option =='tts':
        generate_voice_by_tts(text, front_id, lang)
    elif option =='pyttsx3':
        generate_voice_by_pyttsx3(text, front_id, lang)


def generate_voice_by_pyttsx3(text, front_id, lang='en'):
    engine = pyttsx3.init()
    # 设置语速为150，可以根据个人喜好调整
    engine.setProperty('rate', 150)

    audio_file_path = get_voice_path(front_id)
    engine.save_to_file(text, audio_file_path)


def generate_voice_by_tts(text, front_id, lang='en'):
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