from django.shortcuts import render,HttpResponse
from django.http import FileResponse
from server.service import card_service
from server.service import ai_service
from server.service import sentence_service
from server.service import ai_evaluation_service
from server.service.ai_service.deepseek_service import chat_completion_text
import json
from BlockRecite import settings
import os
from server.models import VoiceTranslateHistory, FrontCard, BackCard

def recite_page(request):
    return render(request, "recite.html")

def create_card_page(request):
    return render(request, "CardCreator.html")

def home_page(request):
    return render(request, "Home.html")

def setting_page(request):
    return render(request, "Setting.html")

def voice_page(request):
    return render(request, "voice_page.html")


def ocr(request):
    if request.method == "POST":
        re_text = card_service.ocr(request.FILES['img'])
        if re_text is not None:
            return HttpResponse(json.dumps({'code':200, 'message':'success', 'data':re_text}))
        else:
            return HttpResponse(json.dumps({'code': 500, 'message': 'OCR recognise is fail'}))
    else:
        return HttpResponse(json.dumps({'code':0, 'message':'method not allowed'}))

def trans_word(request):
    if request.method == "GET":
        word = request.GET.get('word')
        type = request.GET.get('type')
        if type is None:
            # 默认是单词
            type = card_service.WORD

        translation = card_service.explain(word, type)

        # 如果词典没有翻译，尝试用 DeepSeek 翻译
        if type == card_service.WORD and (
            not translation or
            not translation.get('translation') or
            translation.get('translation').strip() == ''
        ):
            translation = trans_word_by_ai(word)

        return HttpResponse(json.dumps({'code':0, 'message':'success','data':translation}),content_type="application/json; charset=utf-8")
    else:
        return HttpResponse(json.dumps({'code':0, 'message':'method not allowed'}))

def trans_word_by_ai(word, model="deepseek"):
    translation = None
    prompt = f'请将单词 "{word}" 翻译成中文。要求：\n1. 只返回中文翻译，不要包含英文原文\n2. 如果单词拼写错误或不存在，返回空字符串\n3. 翻译格式参考：n. 意思1, 意思2'
    if model == "deepseek":
        ai_translation = chat_completion_text(
            messages=[
                {"role": "system", "content": "你是一位专业的英译中翻译助手。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=200
        )

    # 如果 AI 返回了有效翻译，更新 translation
    if ai_translation and ai_translation.strip():
        if translation is None:
            translation = {
                "id": 0,
                "word": word,
                "sw": word,
                "phonetic": "",
                "definition": "",
                "translation": ai_translation,
                "pos": "",
                "collins": 0,
                "oxford": 0,
                "tag": "",
                "bnc": 0,
                "frq": 0,
                "exchange": "",
                "detail": None,
                "audio": ""
            }
    return translation


'''
生成卡片
{
    "front_card":[
        {
            "content":"work",
            "desc":"n.工作"
        }
    ],
    "back_card":{
        "content":"work",
        "desc":"n.工作"
    }
}
'''
def generate_card(request):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
        front_card = data.get('front_card')
        back_card = data.get('back_card')
        if front_card is not None and back_card is not None:
            card_service.generate_card(front_card,back_card)
            return HttpResponse(json.dumps({'code':200, 'message':'success'}))
        else:
            card_service.generate_card(front_card,back_card)
            return HttpResponse(json.dumps({'code':501, 'message':'param is empty'}))
    else:
        return HttpResponse(json.dumps({'code':0, 'message':'method not allowed'}))


def get_recite_card(request):
    num = request.GET.get('num')
    new_word_percent = request.GET.get('new_word_percent')
    if num is None:
        num = 30
    else:
        num = int(num)

    if new_word_percent is None:
        new_word_percent=0.5
    else:
        new_word_percent = float(new_word_percent)

    recite_content = card_service.get_recite_content(num,new_word_percent)
    if recite_content is None:
        return HttpResponse(json.dumps({'code': 200, 'message': 'No word need to recite', 'data': None}))
    else:
        return HttpResponse(json.dumps({'code':200, 'message':'success','data':recite_content}))


def remember(request):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
        front_id = data.get('front_id')
        back_id = data.get('back_id')
        card_service.remember(front_id,back_id)
        card_service.recite_history_count_add()
        return HttpResponse(json.dumps({'code':200, 'message':'success'}))
    else:
        return HttpResponse(json.dumps({'code':0, 'message':'method not allowed'}))

def master_remember(request):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
        front_id = data.get('front_id')
        back_id = data.get('back_id')
        card_service.remember(front_id,back_id,5)
        card_service.recite_history_count_add()
        return HttpResponse(json.dumps({'code':200, 'message':'success'}))
    else:
        return HttpResponse(json.dumps({'code':0, 'message':'method not allowed'}))


def forget(request):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
        front_id = data.get('front_id')
        back_id = data.get('back_id')
        card_service.forget(front_id, back_id)
        return HttpResponse(json.dumps({'code':200, 'message':'success'}))
    else:
        return HttpResponse(json.dumps({'code':0, 'message':'method not allowed'}))



def get_recite_history(request):
    if request.method == "GET":
        data = card_service.get_recite_history()
        return HttpResponse(json.dumps({'code':200, 'message':'success','data':data}))
    else:
        return HttpResponse(json.dumps({'code':0, 'message':'method not allowed'}))

def generate_img_card(request):
    if request.method == "POST":
        image_file = request.FILES.get('image')
        word = request.POST.get('word')
        word_explain = request.POST.get('explanation')
        if image_file is None or word is None:
            return HttpResponse(json.dumps({'code':0, 'message':'empty param error'}))

        card_service.generate_img_card(image_file, word, word_explain)
        return HttpResponse(json.dumps({'code':200, 'message':'success'}))
    else:
        return HttpResponse(json.dumps({'code':0, 'message':'method not allowed'}))

def get_voice(request):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
        front_id = data.get('front_id')
        audio_file_path = card_service.get_voice(front_id)

        if audio_file_path is not None:
            # Return audio file in HTTP response
            with open(audio_file_path, 'rb') as audio_file:
                response = HttpResponse(audio_file.read(), content_type="audio/mpeg")
                response['Content-Disposition'] = 'inline; filename="generated_audio.mp3"'
            return response
        return HttpResponse(json.dumps({'code': 0, 'message': 'NO DATA'}))
    else:
        return HttpResponse(json.dumps({'code':0, 'message':'method not allowed'}))


def get_image(request):
    if request.method == "GET":
        front_id = request.GET.get("id")
        if front_id is not None:
            image_path,img_type = card_service.get_image(front_id)
            if image_path is not None and img_type is not None:
                return FileResponse(open(image_path, 'rb'), content_type=img_type)
            else:
                return HttpResponse(json.dumps({'code': 0, 'message': 'Image file not found'}), status=404)
        else:
            return HttpResponse(json.dumps({'code': 0, 'message': 'NO DATA'}))
    else:
        return HttpResponse(json.dumps({'code':0, 'message':'method not allowed'}))

def talk_to_trans(request):
    if request.method == "POST":
        voice_file = request.FILES.get('voice')

        # 获取文件名
        file_name = voice_file.name

        # 设置保存路径（在 Django 的 MEDIA_ROOT 目录下）
        save_path = os.path.join(settings.STATIC_URL, 'voices', file_name)

        # 确保目录存在
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        # 将文件保存到本地
        with open(save_path, 'wb') as f:
            for chunk in voice_file.chunks():  # 分块写入文件
                f.write(chunk)


        speech_text, transcription_text = ai_service.get_voice_trans_answer(save_path)
        if speech_text is not None and transcription_text is not None:
            VoiceTranslateHistory.objects.create(voice_text=speech_text, translate_text=transcription_text)

        return HttpResponse(json.dumps({'code':200, 'message':'success', 'data':{
            'voice_text':speech_text,
            'transcription_text':transcription_text
        }}))
    else:
        return HttpResponse(json.dumps({'code':0, 'message':'method not allowed'}))

def get_talk_history(request):
    if request.method == "GET":
        try:
            # 查询指定 user_id 的所有记录
            records = VoiceTranslateHistory.objects.filter(user_id=0)

            # 如果没有找到记录
            if not records:
                return HttpResponse(json.dumps({'code': 404, 'message': 'No records found for this user_id'}))

            # 将查询的结果转换为字典列表
            records_data = list(records.values('voice_id', 'voice_text', 'translate_text'))

            # 返回JSON格式的响应
            return HttpResponse(json.dumps({'code': 200, 'message': 'success', 'data':records_data}))

        except Exception as e:
            return HttpResponse(json.dumps({'code': 500, 'message':str(e)}))
    else:
        return HttpResponse(json.dumps({'code': 0, 'message': 'method not allowed'}))


def del_talk_history(request):
    if request.method == "GET":
        try:
            voice_id = request.GET.get("voice_id")
            if voice_id is not None:
                VoiceTranslateHistory.objects.get(voice_id=voice_id).delete()
            # 返回JSON格式的响应
            return HttpResponse(json.dumps({'code': 200, 'message': 'success'}))

        except Exception as e:
            return HttpResponse(json.dumps({'code': 500, 'message':str(e)}))
    else:
        return HttpResponse(json.dumps({'code': 0, 'message': 'method not allowed'}))

def get_card_base_info(request):
    if request.method == "GET":
        try:
            user_id = request.GET.get("user_id")
            data = card_service.get_card_base_info(user_id)
            # 返回JSON格式的响应
            return HttpResponse(json.dumps({'code': 200, 'message': 'success', 'data':data}))
        except Exception as e:
            return HttpResponse(json.dumps({'code': 500, 'message':str(e)}))
    else:
        return HttpResponse(json.dumps({'code': 0, 'message': 'method not allowed'}))

def get_back_word_list(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            content_type = data["content_type"]
            content_status = int(data["content_status"])
            page = int(data["page"])
            page_size = int(data["page_size"])

            data = card_service.get_back_word_list(content_type, content_status, page, page_size)
            # 返回JSON格式的响应
            return HttpResponse(json.dumps({'code': 200, 'message': 'success', 'data':data}))
        except Exception as e:
            return HttpResponse(json.dumps({'code': 500, 'message':str(e)}))
    else:
        return HttpResponse(json.dumps({'code': 0, 'message': 'method not allowed'}))


# ==================== 句子翻译学习功能 API ====================

def get_sentence_cards(request):
    """获取句子学习卡片"""
    if request.method == "GET":
        try:
            num = request.GET.get('num', 10)
            new_percent = request.GET.get('new_percent', 0.5)
            
            num = int(num)
            new_percent = float(new_percent)
            
            cards = sentence_service.get_sentence_cards(num, new_percent)
            
            if cards is None:
                return HttpResponse(json.dumps({
                    'code': 200, 
                    'message': 'No sentence cards available', 
                    'data': None
                }))
            
            return HttpResponse(json.dumps({
                'code': 200, 
                'message': 'success', 
                'data': cards
            }))
        except Exception as e:
            return HttpResponse(json.dumps({'code': 500, 'message': str(e)}))
    else:
        return HttpResponse(json.dumps({'code': 0, 'message': 'method not allowed'}))


def create_sentence_card(request):
    """创建句子复习卡片"""
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            sentence_id = data.get('sentence_id')
            chinese = data.get('chinese')
            english = data.get('english')
            article_title = data.get('article_title', '')
            article_id = data.get('article_id')
            
            if not sentence_id or not chinese or not english:
                return HttpResponse(json.dumps({
                    'code': 400,
                    'message': 'Missing required parameters'
                }))
            
            result = sentence_service.create_or_update_sentence_card(
                sentence_id=sentence_id,
                chinese=chinese,
                english=english,
                article_title=article_title,
                article_id=article_id
            )
            
            if result['success']:
                return HttpResponse(json.dumps({
                    'code': 200,
                    'message': 'success',
                    'data': {
                        'front_id': result['front_id'],
                        'back_id': result['back_id'],
                        'is_new': result.get('is_new', True)
                    }
                }))
            else:
                return HttpResponse(json.dumps({
                    'code': 500,
                    'message': result.get('error', 'Failed to create card')
                }))
        except Exception as e:
            return HttpResponse(json.dumps({'code': 500, 'message': str(e)}))
    else:
        return HttpResponse(json.dumps({'code': 0, 'message': 'method not allowed'}))


def evaluate_translation(request):
    """AI 评测翻译"""
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            sentence_id = data.get('sentence_id')
            chinese = data.get('chinese')
            user_translation = data.get('user_translation')
            reference_translation = data.get('reference_translation')
            
            if not chinese or not user_translation:
                return HttpResponse(json.dumps({
                    'code': 400, 
                    'message': 'Missing required parameters'
                }))
            
            # 调用 AI 评测
            evaluation = ai_evaluation_service.evaluate_translation(
                chinese, user_translation, reference_translation
            )
            
            # 记录学习日志
            if sentence_id:
                sentence_service.record_learning_log(
                    sentence_id, user_translation, evaluation
                )
            
            return HttpResponse(json.dumps({
                'code': 200, 
                'message': 'success', 
                'data': evaluation
            }))
        except Exception as e:
            return HttpResponse(json.dumps({'code': 500, 'message': str(e)}))
    else:
        return HttpResponse(json.dumps({'code': 0, 'message': 'method not allowed'}))


def create_article(request):
    """创建文章 - 支持图片上传"""
    if request.method == "POST":
        try:
            # 检查是否有文件上传
            if request.FILES.get('image'):
                # 处理 multipart/form-data 请求（包含图片）
                title = request.POST.get('title')
                article_type = request.POST.get('article_type', '')
                exam_type = request.POST.get('exam_type', 'ielts')
                topic = request.POST.get('topic', '')
                difficulty = int(request.POST.get('difficulty', 3))
                content = request.POST.get('content')
                tags_str = request.POST.get('tags', '[]')
                tags = json.loads(tags_str) if tags_str else []
                sentences_str = request.POST.get('sentences', '[]')
                sentences_data = json.loads(sentences_str) if sentences_str else []
                
                # 先创建文章
                result = sentence_service.create_article_with_sentences(
                    title=title,
                    article_type=article_type,
                    exam_type=exam_type,
                    topic=topic,
                    difficulty=difficulty,
                    content=content,
                    tags=tags
                )
                
                if not result['success']:
                    return HttpResponse(json.dumps({
                        'code': 500, 
                        'message': result.get('error', 'Failed to create article')
                    }))
                
                # 上传并保存图片
                image_file = request.FILES['image']
                image_result = sentence_service.update_article_image(
                    result['article_id'], image_file
                )
                
                if image_result['success']:
                    result['image_path'] = image_result['image_path']
                
                # 使用前端传来的已翻译句子，或自动翻译
                article = result['article']
                
                if sentences_data and isinstance(sentences_data, list):
                    # 使用前端传来的已翻译句子
                    sentence_service.create_sentences_manually(
                        result['article_id'], sentences_data
                    )
                else:
                    # 自动翻译句子并生成卡片
                    article_sentences = ArticleSentence.objects.filter(article=article)
                    
                    english_list = [s.english for s in article_sentences]
                    translations = ai_evaluation_service.batch_translate_sentences(english_list)
                    
                    for s, trans in zip(article_sentences, translations):
                        s.chinese = trans
                        s.save()
                    
                    sentence_service.generate_sentence_cards(article, list(article_sentences))
                
                return HttpResponse(json.dumps({
                    'code': 200, 
                    'message': 'success', 
                    'data': {
                        'article_id': result['article_id'],
                        'sentences_count': result['sentences_count'],
                        'image_path': result.get('image_path', '')
                    }
                }))
            else:
                # 处理 JSON 请求（不包含图片）
                data = json.loads(request.body.decode("utf-8"))
                title = data.get('title') or ''
                article_type = data.get('article_type', '')
                exam_type = data.get('exam_type', 'ielts')
                topic = data.get('topic', '') or title
                difficulty = data.get('difficulty', 3)
                content = data.get('content') or ''
                tags = data.get('tags', [])
                sentences = data.get('sentences')

                # 仅提交题目：AI 生成范文 → 分句 → 过滤 → 翻译 → 入库，一步完成
                if not content.strip() and (title.strip() or topic.strip()):
                    result = sentence_service.create_article_from_topic(
                        title=title.strip() or topic.strip(),
                        article_type=article_type,
                        exam_type=exam_type,
                        topic=topic.strip() or title.strip(),
                        difficulty=difficulty,
                        tags=tags
                    )
                    if not result.get('success'):
                        return HttpResponse(json.dumps({
                            'code': 500,
                            'message': result.get('error', '生成失败')
                        }))
                    return HttpResponse(json.dumps({
                        'code': 200,
                        'message': 'success',
                        'data': {
                            'article_id': result['article_id'],
                            'sentences': result['sentences'],
                            'sentences_count': len(result['sentences'])
                        }
                    }))

                if not title or not content:
                    return HttpResponse(json.dumps({
                        'code': 400,
                        'message': '请提供标题和文章内容，或仅提供题目由 AI 生成范文'
                    }))

                # 已有正文：分句 → 过滤 → 翻译 → 入库，一步完成，返回 article_id + sentences
                result = sentence_service.create_article_from_content(
                    title=title,
                    article_type=article_type,
                    exam_type=exam_type,
                    topic=topic,
                    difficulty=difficulty,
                    content=content,
                    tags=tags
                )
                if not result.get('success'):
                    return HttpResponse(json.dumps({
                        'code': 500,
                        'message': result.get('error', '处理失败')
                    }))
                return HttpResponse(json.dumps({
                    'code': 200,
                    'message': 'success',
                    'data': {
                        'article_id': result['article_id'],
                        'sentences': result['sentences'],
                        'sentences_count': len(result['sentences'])
                    }
                }))
        except Exception as e:
            return HttpResponse(json.dumps({'code': 500, 'message': str(e)}))
    else:
        return HttpResponse(json.dumps({'code': 0, 'message': 'method not allowed'}))


def get_articles(request):
    """获取文章列表 - 支持多标签过滤"""
    if request.method == "GET":
        try:
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 10))
            exam_type = request.GET.get('exam_type')
            article_type = request.GET.get('article_type')
            difficulty = request.GET.get('difficulty')
            topic = request.GET.get('topic')
            tags = request.GET.get('tags')  # JSON字符串，如["标签1","标签2"]
            
            if difficulty:
                difficulty = int(difficulty)
            
            # 解析标签
            tags_list = None
            if tags:
                try:
                    tags_list = json.loads(tags)
                except:
                    tags_list = [tags]
            
            result = sentence_service.get_article_list(
                page=page,
                page_size=page_size,
                exam_type=exam_type,
                article_type=article_type,
                difficulty=difficulty,
                topic=topic,
                tags=tags_list
            )
            
            return HttpResponse(json.dumps({
                'code': 200, 
                'message': 'success', 
                'data': result
            }))
        except Exception as e:
            return HttpResponse(json.dumps({'code': 500, 'message': str(e)}))
    else:
        return HttpResponse(json.dumps({'code': 0, 'message': 'method not allowed'}))


def get_article_detail(request):
    """获取文章详情"""
    if request.method == "GET":
        try:
            article_id = request.GET.get('id')
            
            if not article_id:
                return HttpResponse(json.dumps({
                    'code': 400, 
                    'message': 'Article ID is required'
                }))
            
            result = sentence_service.get_article_detail(int(article_id))
            
            if not result['success']:
                return HttpResponse(json.dumps({
                    'code': 404, 
                    'message': result.get('error', 'Article not found')
                }))
            
            return HttpResponse(json.dumps({
                'code': 200, 
                'message': 'success', 
                'data': result['data']
            }))
        except Exception as e:
            return HttpResponse(json.dumps({'code': 500, 'message': str(e)}))
    else:
        return HttpResponse(json.dumps({'code': 0, 'message': 'method not allowed'}))


def delete_article(request):
    """删除文章"""
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            article_id = data.get('article_id')
            
            if not article_id:
                return HttpResponse(json.dumps({
                    'code': 400, 
                    'message': 'Article ID is required'
                }))
            
            result = sentence_service.delete_article(int(article_id))
            
            if not result['success']:
                return HttpResponse(json.dumps({
                    'code': 500, 
                    'message': result.get('error', 'Failed to delete article')
                }))
            
            return HttpResponse(json.dumps({
                'code': 200, 
                'message': 'success'
            }))
        except Exception as e:
            return HttpResponse(json.dumps({'code': 500, 'message': str(e)}))
    else:
        return HttpResponse(json.dumps({'code': 0, 'message': 'method not allowed'}))


def get_sentence_stats(request):
    """获取学习统计"""
    if request.method == "GET":
        try:
            stats = sentence_service.get_learning_stats()
            
            return HttpResponse(json.dumps({
                'code': 200, 
                'message': 'success', 
                'data': stats
            }))
        except Exception as e:
            return HttpResponse(json.dumps({'code': 500, 'message': str(e)}))
    else:
        return HttpResponse(json.dumps({'code': 0, 'message': 'method not allowed'}))


def get_error_sentences(request):
    """获取错题本"""
    if request.method == "GET":
        try:
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 10))
            
            result = sentence_service.get_error_sentences(page=page, page_size=page_size)
            
            return HttpResponse(json.dumps({
                'code': 200, 
                'message': 'success', 
                'data': result
            }))
        except Exception as e:
            return HttpResponse(json.dumps({'code': 500, 'message': str(e)}))
    else:
        return HttpResponse(json.dumps({'code': 0, 'message': 'method not allowed'}))


def sentence_remember(request):
    """记住句子 - 更新艾宾浩斯记忆"""
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            front_id = data.get('front_id')
            back_id = data.get('back_id')
            
            # 复用现有的 remember 逻辑
            card_service.remember(front_id, back_id)
            
            return HttpResponse(json.dumps({
                'code': 200, 
                'message': 'success'
            }))
        except Exception as e:
            return HttpResponse(json.dumps({'code': 500, 'message': str(e)}))
    else:
        return HttpResponse(json.dumps({'code': 0, 'message': 'method not allowed'}))


def sentence_forget(request):
    """忘记句子 - 重置学习进度"""
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            front_id = data.get('front_id')
            back_id = data.get('back_id')
            
            # 复用现有的 forget 逻辑
            card_service.forget(front_id, back_id)
            
            return HttpResponse(json.dumps({
                'code': 200, 
                'message': 'success'
            }))
        except Exception as e:
            return HttpResponse(json.dumps({'code': 500, 'message': str(e)}))
    else:
        return HttpResponse(json.dumps({'code': 0, 'message': 'method not allowed'}))


def split_sentences(request):
    """智能分句 API"""
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            content = data.get('content')
            
            if not content:
                return HttpResponse(json.dumps({
                    'code': 400, 
                    'message': 'Content is required'
                }))
            
            # 分句
            sentences = sentence_service.split_into_sentences(content)
            
            # 批量翻译
            if sentences:
                english_list = [s['english'] for s in sentences]
                translations = ai_evaluation_service.batch_translate_sentences(english_list)
                
                print(f"[DEBUG] 翻译结果数量: {len(translations)}")
                print(f"[DEBUG] 原文数量: {len(sentences)}")
                
                for i, trans in enumerate(translations):
                    sentences[i]['chinese'] = trans
                    print(f"[DEBUG] 句子 {i+1}: EN={sentences[i]['english'][:50]}... CN={trans[:50]}...")
            
            return HttpResponse(json.dumps({
                'code': 200, 
                'message': 'success', 
                'data': sentences
            }))
        except Exception as e:
            print(f"[ERROR] split_sentences 失败: {e}")
            return HttpResponse(json.dumps({'code': 500, 'message': str(e)}))
    else:
        return HttpResponse(json.dumps({'code': 0, 'message': 'method not allowed'}))


def get_article_tags(request):
    """获取所有文章标签"""
    if request.method == "GET":
        try:
            result = sentence_service.get_all_tags()
            return HttpResponse(json.dumps({
                'code': 200,
                'message': 'success',
                'data': result.get('tags', [])
            }))
        except Exception as e:
            return HttpResponse(json.dumps({'code': 500, 'message': str(e)}))
    else:
        return HttpResponse(json.dumps({'code': 0, 'message': 'method not allowed'}))


def get_exam_types(request):
    """获取所有考试类型"""
    if request.method == "GET":
        try:
            result = sentence_service.get_all_exam_types()
            return HttpResponse(json.dumps({
                'code': 200,
                'message': 'success',
                'data': result.get('exam_types', [])
            }))
        except Exception as e:
            return HttpResponse(json.dumps({'code': 500, 'message': str(e)}))
    else:
        return HttpResponse(json.dumps({'code': 0, 'message': 'method not allowed'}))


def get_article_types(request):
    """获取所有文章类型"""
    if request.method == "GET":
        try:
            exam_type = request.GET.get('exam_type')
            result = sentence_service.get_all_article_types(exam_type)
            return HttpResponse(json.dumps({
                'code': 200,
                'message': 'success',
                'data': result.get('article_types', [])
            }))
        except Exception as e:
            return HttpResponse(json.dumps({'code': 500, 'message': str(e)}))
    else:
        return HttpResponse(json.dumps({'code': 0, 'message': 'method not allowed'}))


def get_article_image(request):
    """获取文章图片"""
    if request.method == "GET":
        try:
            path = request.GET.get('path')
            if not path:
                return HttpResponse(json.dumps({'code': 400, 'message': 'Path is required'}))
            
            # 安全处理路径
            file_path = os.path.join(settings.BASE_DIR, path)
            
            # 确保文件存在
            if not os.path.exists(file_path):
                return HttpResponse(json.dumps({'code': 404, 'message': 'Image not found'}))
            
            # 根据文件扩展名获取 MIME 类型
            import mimetypes
            img_type, _ = mimetypes.guess_type(file_path)
            
            return FileResponse(open(file_path, 'rb'), content_type=img_type)
        except Exception as e:
            return HttpResponse(json.dumps({'code': 500, 'message': str(e)}))
    else:
        return HttpResponse(json.dumps({'code': 0, 'message': 'method not allowed'}))


def get_manage_sentences(request):
    """获取管理用的句子列表"""
    if request.method == "GET":
        try:
            from server.models import ArticleSentence, FrontCard, BackCard, CardRelation, SentenceLearningLog
            
            # 获取所有句子
            sentences = ArticleSentence.objects.select_related('article').all()
            
            # 组装数据
            data = []
            for sentence in sentences:
                # 获取卡片关联
                relation = CardRelation.objects.filter(
                    description__contains=f'句子ID:{sentence.id}'
                ).first()
                
                front_id = relation.front_id if relation else None
                back_id = relation.back_id if relation else None
                
                # 获取学习状态
                status = 'new'
                if relation and relation.back_id:
                    try:
                        back_card = BackCard.objects.get(back_id=relation.back_id)
                        if back_card.repeat_num >= 5:
                            status = 'mastered'
                        elif back_card.repeat_num > 0:
                            status = 'learning'
                    except BackCard.DoesNotExist:
                        pass
                
                # 检查是否有错误记录
                has_error = SentenceLearningLog.objects.filter(
                    sentence=sentence, has_error=True
                ).exists()
                if has_error:
                    status = 'error'
                
                data.append({
                    'id': sentence.id,
                    'article_id': sentence.article.id if sentence.article else None,
                    'article_title': sentence.article.title if sentence.article else None,
                    'tags': sentence.article.tags if sentence.article else [],
                    'sequence': sentence.sequence,
                    'english': sentence.english,
                    'chinese': sentence.chinese,
                    'front_id': front_id,
                    'back_id': back_id,
                    'status': status,
                    'create_time': sentence.create_time.strftime('%Y-%m-%d %H:%M:%S') if sentence.create_time else None
                })
            
            return HttpResponse(json.dumps({
                'code': 200,
                'message': 'success',
                'data': {'sentences': data}
            }))
        except Exception as e:
            return HttpResponse(json.dumps({'code': 500, 'message': str(e)}))
    else:
        return HttpResponse(json.dumps({'code': 0, 'message': 'method not allowed'}))


def update_sentence(request):
    """更新句子"""
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            sentence_id = data.get('id')
            english = data.get('english')
            chinese = data.get('chinese')
            
            if not sentence_id:
                return HttpResponse(json.dumps({'code': 400, 'message': 'Sentence ID is required'}))
            
            result = sentence_service.update_sentence(sentence_id, english, chinese)
            
            if result['success']:
                return HttpResponse(json.dumps({'code': 200, 'message': 'success'}))
            else:
                return HttpResponse(json.dumps({'code': 500, 'message': result.get('error', 'Update failed')}))
        except Exception as e:
            return HttpResponse(json.dumps({'code': 500, 'message': str(e)}))
    else:
        return HttpResponse(json.dumps({'code': 0, 'message': 'method not allowed'}))


def delete_sentence(request):
    """删除句子"""
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            sentence_id = data.get('id')
            
            if not sentence_id:
                return HttpResponse(json.dumps({'code': 400, 'message': 'Sentence ID is required'}))
            
            result = sentence_service.delete_sentence(int(sentence_id))
            
            if result['success']:
                return HttpResponse(json.dumps({'code': 200, 'message': 'success'}))
            else:
                return HttpResponse(json.dumps({'code': 500, 'message': result.get('error', 'Delete failed')}))
        except Exception as e:
            return HttpResponse(json.dumps({'code': 500, 'message': str(e)}))
    else:
        return HttpResponse(json.dumps({'code': 0, 'message': 'method not allowed'}))


def batch_delete_sentences(request):
    """批量删除句子"""
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            sentence_ids = data.get('ids', [])
            
            if not sentence_ids:
                return HttpResponse(json.dumps({'code': 400, 'message': 'Sentence IDs are required'}))
            
            success_count = 0
            for sentence_id in sentence_ids:
                result = sentence_service.delete_sentence(int(sentence_id))
                if result['success']:
                    success_count += 1
            
            return HttpResponse(json.dumps({
                'code': 200,
                'message': 'success',
                'data': {'deleted': success_count}
            }))
        except Exception as e:
            return HttpResponse(json.dumps({'code': 500, 'message': str(e)}))
    else:
        return HttpResponse(json.dumps({'code': 0, 'message': 'method not allowed'}))