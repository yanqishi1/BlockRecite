from gtts import gTTS

def generate_voice_by_text(text, front_id, lang='en'):
    if text is None or len(text) == 0:
        return None
    try:
        tts = gTTS(text=text, lang=lang)

        audio_file_path = './tmp/generated_audio_'+str(front_id)+".mp3"
        tts.save(audio_file_path)

        return audio_file_path
    except Exception as e:
        print(e)
        return None