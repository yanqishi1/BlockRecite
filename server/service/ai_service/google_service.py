import os

from pydub import AudioSegment
import speech_recognition as sr

# 初始化识别器
recognizer = sr.Recognizer()

import subprocess

def convert_audio_with_ffmpeg(input_audio_path, output_audio_path):
    """使用FFmpeg将音频文件转换为WAV格式"""
    ffmpeg_path = r"D:\Program Files (x86)\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe"  # 替换为ffmpeg.exe的完整路径
    try:
        subprocess.run([ffmpeg_path, '-i', input_audio_path, output_audio_path], check=True)
        print(f"音频已成功转换为 WAV 格式: {output_audio_path}")
    except subprocess.CalledProcessError as e:
        print(f"音频转换失败: {e}")

def convert_to_wav(input_audio_path, output_audio_path):
    """将音频文件转换为 WAV 格式"""
    try:
        audio = AudioSegment.from_file(input_audio_path)
        audio.export(output_audio_path, format="wav")
        print(f"音频已成功转换为 WAV 格式: {output_audio_path}")
    except Exception as e:
        print(f"音频转换失败: {e}")

def google_trans_voice_to_text(audio_path):
    try:
        # 将非WAV格式音频转换为WAV
        wav_audio_path = r"D:\DL\BlockRecite\static\converted_audio.wav"

        if os.path.exists(wav_audio_path):
            os.remove(wav_audio_path)
        convert_audio_with_ffmpeg(audio_path, wav_audio_path)

        # 打开转换后的WAV文件
        with sr.AudioFile(wav_audio_path) as source:
            audio = recognizer.record(source)

        # 使用Google Web Speech API转换语音为文本
        text = recognizer.recognize_google(audio)  # 支持中文
        return text
    except sr.UnknownValueError:
        return "无法理解音频内容"
    except sr.RequestError as e:
        return f"无法连接到Google API; {e}"
    except Exception as e:
        return f"发生错误: {e}"


if __name__ == '__main__':
    text = google_trans_voice_to_text(r'D:\DL\BlockRecite\static\voices\generated_audio_22.mp3')
    print(text)