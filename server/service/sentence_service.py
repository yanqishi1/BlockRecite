"""
句子翻译学习服务
"""
import datetime
import json
import os
import re
from django.db import transaction
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from django.conf import settings

from server.models import (
    Article, ArticleSentence, SentenceLearningLog,
    FrontCard, BackCard, CardRelation
)
from server.service import ai_evaluation_service


# 内容类型常量
CONTENT_TYPE_SENTENCE = 5  # 写作句子翻译类型（中译英）
# content_type 定义：
# 0 = 阅读单词
# 1 = 听力单词
# 2 = 图片单词
# 3 = 听力句子
# 4 = 口语句子：汉翻英
# 5 = 写作句子翻译（中译英）


def split_into_sentences(text):
    """
    将文章分割成句子
    基本规则：按句号、问号、感叹号分割
    过滤太短/太长的句子
    """
    # 清理文本
    text = text.strip()
    
    # 按句子边界分割
    sentence_pattern = r'(?<=[.!?])\s+|(?<=[。！？])\s*'
    raw_sentences = re.split(sentence_pattern, text)
    
    sentences = []
    for i, s in enumerate(raw_sentences):
        s = s.strip()
        # 过滤条件：长度在 10-300 字符之间，且不是纯数字
        if len(s) >= 10 and len(s) <= 300 and not s.isdigit():
            sentences.append({
                'sequence': i + 1,
                'english': s
            })
    
    return sentences


def save_article_image(image_file, article_id):
    """
    保存文章题目图片
    
    Args:
        image_file: 上传的图片文件
        article_id: 文章ID
    
    Returns:
        str: 图片相对路径
    """
    try:
        # 创建保存目录
        target_dir = os.path.join('static', 'article_images')
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
        
        # 生成文件名
        file_ext = os.path.splitext(image_file.name)[1]
        file_name = f"article_{article_id}{file_ext}"
        file_path = os.path.join(target_dir, file_name)
        
        # 保存文件
        with open(file_path, 'wb+') as destination:
            for chunk in image_file.chunks():
                destination.write(chunk)
        
        return file_path
    except Exception as e:
        print(f"保存图片失败: {e}")
        return None


def create_article_with_sentences(title, article_type, exam_type, topic, difficulty, content, 
                                   tags=None, image_path='', user_id=0):
    """
    创建文章并自动生成句子
    
    Args:
        title: 文章标题/题目
        article_type: 文章类型（如Task1, Task2等）
        exam_type: 考试类型（ielts, cet4, cet6, 考研等）
        topic: 话题分类
        difficulty: 难度等级 1-5
        content: 文章内容
        tags: 自定义标签列表
        image_path: 题目图片路径
        user_id: 创建者ID
    
    Returns:
        dict: 创建结果
    """
    try:
        with transaction.atomic():
            # 创建文章
            article = Article.objects.create(
                title=title,
                exam_type=exam_type,
                article_type=article_type,
                topic=topic,
                difficulty=difficulty,
                content=content,
                tags=tags or [],
                image_path=image_path,
                created_by=user_id,
                is_system=False
            )
            
            # 分割句子
            sentences_data = split_into_sentences(content)
            
            # 创建句子记录
            sentences = []
            for sent_data in sentences_data:
                sentence = ArticleSentence.objects.create(
                    article=article,
                    sequence=sent_data['sequence'],
                    english=sent_data['english'],
                    chinese='',  # 后续可以调用翻译API填充
                    is_key_sentence=True
                )
                sentences.append(sentence)
            
            return {
                'success': True,
                'article_id': article.id,
                'sentences_count': len(sentences),
                'article': article
            }
    except Exception as e:
        print(f"创建文章失败: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def create_sentences_manually(article_id, sentences_data):
    """
    手动添加句子到文章
    
    Args:
        article_id: 文章ID
        sentences_data: [{'english': '...', 'chinese': '...'}, ...]
    
    Returns:
        dict: 创建结果
    """
    try:
        with transaction.atomic():
            article = Article.objects.get(id=article_id)
            
            # 删除旧句子
            ArticleSentence.objects.filter(article=article).delete()
            
            # 创建新句子
            sentences = []
            for i, sent_data in enumerate(sentences_data, 1):
                sentence = ArticleSentence.objects.create(
                    article=article,
                    sequence=i,
                    english=sent_data.get('english', ''),
                    chinese=sent_data.get('chinese', ''),
                    is_key_sentence=sent_data.get('is_key_sentence', True)
                )
                sentences.append(sentence)
            
            # 生成学习卡片
            generate_sentence_cards(article, sentences)
            
            return {
                'success': True,
                'sentences_count': len(sentences)
            }
    except Exception as e:
        print(f"创建句子失败: {e}")
        return {
            'success': False,
            'error': str(e)
        }


# 用于「根据题目生成范文并入库」时的最小单词数，少于此视为太简单而过滤
MIN_WORDS_FOR_SENTENCE = 6


def create_article_from_topic(title, article_type, exam_type, topic, difficulty, tags=None,
                              word_count_target=400):
    """
    根据作文题目调用 AI 生成范文，分句、过滤太简单句子、翻译后写入数据库。
    一步完成：生成 → 分句 → 过滤 → 翻译 → 建文章与句子。

    Args:
        title: 文章标题/题目（也可作为 AI 话题）
        article_type: 文章类型
        exam_type: 考试类型
        topic: 话题（可与 title 一致）
        difficulty: 难度 1-5
        tags: 标签列表
        word_count_target: AI 范文目标字数

    Returns:
        dict: { 'success': bool, 'article_id': int, 'sentences': [...], 'error': str }
        sentences 元素为 { id, sequence, english, chinese, is_key_sentence }
    """
    try:
        essay = ai_evaluation_service.generate_essay_from_topic(
            topic=topic or title,
            exam_type=exam_type or 'ielts',
            title=title,
            word_count_target=word_count_target
        )
        if not (essay and essay.strip()):
            return {'success': False, 'error': 'AI 未能生成范文，请稍后重试或更换题目。'}

        raw = split_into_sentences(essay)
        # 过滤太短的句子（单词数过少视为太简单）
        filtered = [
            s for s in raw
            if len(s.get('english', '').split()) >= MIN_WORDS_FOR_SENTENCE
        ]
        if not filtered:
            return {'success': False, 'error': '未得到适合练习的句子，请尝试更换题目或放宽条件。'}

        english_list = [s['english'] for s in filtered]
        translations = ai_evaluation_service.batch_translate_sentences(english_list)
        sentences_data = [
            {'english': en, 'chinese': translations[i] if i < len(translations) else '', 'is_key_sentence': True}
            for i, en in enumerate(english_list)
        ]

        with transaction.atomic():
            # 先创建文章（会自带按全文分句的句子，后面会替换）
            result = create_article_with_sentences(
                title=title or '未命名文章',
                article_type=article_type or '',
                exam_type=exam_type or 'ielts',
                topic=topic or '',
                difficulty=difficulty if difficulty is not None else 3,
                content=essay,
                tags=tags or []
            )
            if not result.get('success'):
                return {'success': False, 'error': result.get('error', '创建文章失败')}
            article_id = result['article_id']
            article = result['article']

            # 删除自动生成的句子，改为只保留过滤后的句子
            ArticleSentence.objects.filter(article=article).delete()
            create_sentences_manually(article_id, sentences_data)

            # 返回带 id 的句子列表供前端使用
            created = list(
                ArticleSentence.objects.filter(article_id=article_id).order_by('sequence')
            )
            sentences = [
                {
                    'id': s.id,
                    'sequence': s.sequence,
                    'english': s.english,
                    'chinese': s.chinese,
                    'is_key_sentence': getattr(s, 'is_key_sentence', True)
                }
                for s in created
            ]
        return {
            'success': True,
            'article_id': article_id,
            'sentences': sentences
        }
    except Exception as e:
        print(f"create_article_from_topic 失败: {e}")
        return {'success': False, 'error': str(e)}


def create_article_from_content(title, article_type, exam_type, topic, difficulty, content, tags=None):
    """
    根据已有正文：分句、过滤太简单句子、翻译后写入数据库，一步完成。
    """
    try:
        raw = split_into_sentences(content)
        filtered = [
            s for s in raw
            if len(s.get('english', '').split()) >= MIN_WORDS_FOR_SENTENCE
        ]
        if not filtered:
            return {'success': False, 'error': '未得到适合练习的句子，请尝试输入更长的文章。'}
        english_list = [s['english'] for s in filtered]
        translations = ai_evaluation_service.batch_translate_sentences(english_list)
        sentences_data = [
            {'english': en, 'chinese': translations[i] if i < len(translations) else '', 'is_key_sentence': True}
            for i, en in enumerate(english_list)
        ]
        with transaction.atomic():
            result = create_article_with_sentences(
                title=title or '未命名文章',
                article_type=article_type or '',
                exam_type=exam_type or 'ielts',
                topic=topic or '',
                difficulty=difficulty if difficulty is not None else 3,
                content=content,
                tags=tags or []
            )
            if not result.get('success'):
                return {'success': False, 'error': result.get('error', '创建文章失败')}
            article_id = result['article_id']
            article = result['article']
            ArticleSentence.objects.filter(article=article).delete()
            create_sentences_manually(article_id, sentences_data)
            created = list(
                ArticleSentence.objects.filter(article_id=article_id).order_by('sequence')
            )
            sentences = [
                {
                    'id': s.id,
                    'sequence': s.sequence,
                    'english': s.english,
                    'chinese': s.chinese,
                    'is_key_sentence': getattr(s, 'is_key_sentence', True)
                }
                for s in created
            ]
        return {
            'success': True,
            'article_id': article_id,
            'sentences': sentences
        }
    except Exception as e:
        print(f"create_article_from_content 失败: {e}")
        return {'success': False, 'error': str(e)}


def update_article_image(article_id, image_file):
    """
    更新文章图片
    
    Args:
        article_id: 文章ID
        image_file: 图片文件
    
    Returns:
        dict: 更新结果
    """
    try:
        article = Article.objects.get(id=article_id)
        
        # 保存新图片
        image_path = save_article_image(image_file, article_id)
        if image_path:
            # 删除旧图片
            if article.image_path and os.path.exists(article.image_path):
                try:
                    os.remove(article.image_path)
                except:
                    pass
            
            article.image_path = image_path
            article.save()
            
            return {
                'success': True,
                'image_path': image_path
            }
        else:
            return {
                'success': False,
                'error': '保存图片失败'
            }
    except Article.DoesNotExist:
        return {
            'success': False,
            'error': '文章不存在'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def generate_sentence_cards(article, sentences):
    """
    为句子生成学习卡片
    正面：中文句子
    背面：英文句子
    """
    current_time = datetime.datetime.now()
    
    for sentence in sentences:
        # 检查是否已存在卡片
        existing = FrontCard.objects.filter(
            content_type=CONTENT_TYPE_SENTENCE,
            front_card_content=sentence.chinese
        ).first()
        
        if existing:
            continue
        
        # 创建正面卡片（中文句子作为题目）
        front_card = FrontCard.objects.create(
            front_card_content=sentence.chinese,
            content_type=CONTENT_TYPE_SENTENCE,
            description=f"来自文章《{article.title}》",
            start_recite_time_point=current_time,
            next_study_time=get_recite_time(current_time, 0)
        )
        
        # 创建背面卡片（英文句子作为答案）
        back_card = BackCard.objects.create(
            back_card_content=sentence.english,
            content_type=CONTENT_TYPE_SENTENCE,
            description=f"参考译文 | 文章ID:{article.id}",
            start_recite_time_point=current_time,
            next_study_time=get_recite_time(current_time, 0)
        )
        
        # 创建关联
        CardRelation.objects.create(
            front_id=front_card.front_id,
            back_id=back_card.back_id,
            description=f"句子ID:{sentence.id}"
        )


def create_or_update_sentence_card(sentence_id, chinese, english, article_title="", article_id=None):
    """
    为单个句子创建或更新复习卡片
    用于用户标记"需复习"时创建卡片
    
    Args:
        sentence_id: 句子ID
        chinese: 中文句子（正面）
        english: 英文句子（背面）
        article_title: 文章标题
        article_id: 文章ID
    
    Returns:
        dict: 结果包含 front_id 和 back_id
    """
    try:
        # 检查是否已存在卡片
        existing_relation = CardRelation.objects.filter(
            description=f"句子ID:{sentence_id}"
        ).first()
        
        if existing_relation:
            # 更新现有卡片
            front_card = FrontCard.objects.get(front_id=existing_relation.front_id)
            back_card = BackCard.objects.get(back_id=existing_relation.back_id)
            
            front_card.front_card_content = chinese
            front_card.content_type = CONTENT_TYPE_SENTENCE
            front_card.description = f"来自文章《{article_title}》"
            front_card.save()
            
            back_card.back_card_content = english
            back_card.content_type = CONTENT_TYPE_SENTENCE
            back_card.description = f"参考译文 | 文章ID:{article_id}"
            back_card.save()
            
            return {
                'success': True,
                'front_id': front_card.front_id,
                'back_id': back_card.back_id,
                'is_new': False
            }
        else:
            # 创建新卡片
            current_time = datetime.datetime.now()
            
            front_card = FrontCard.objects.create(
                front_card_content=chinese,
                content_type=CONTENT_TYPE_SENTENCE,
                description=f"来自文章《{article_title}》",
                start_recite_time_point=current_time,
                next_study_time=get_recite_time(current_time, 0)
            )
            
            back_card = BackCard.objects.create(
                back_card_content=english,
                content_type=CONTENT_TYPE_SENTENCE,
                description=f"参考译文 | 文章ID:{article_id}",
                start_recite_time_point=current_time,
                next_study_time=get_recite_time(current_time, 0)
            )
            
            CardRelation.objects.create(
                front_id=front_card.front_id,
                back_id=back_card.back_id,
                description=f"句子ID:{sentence_id}"
            )
            
            return {
                'success': True,
                'front_id': front_card.front_id,
                'back_id': back_card.back_id,
                'is_new': True
            }
    except Exception as e:
        print(f"创建复习卡片失败: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def get_recite_time(start_time, recite_num):
    """
    艾宾浩斯遗忘曲线计算下次复习时间
    """
    ebbinghaus = [1, 2, 4, 7, 15, 30]
    
    if recite_num == 0:
        return start_time + datetime.timedelta(minutes=30)
    elif recite_num == 1:
        return start_time + datetime.timedelta(hours=12)
    else:
        days = ebbinghaus[min(recite_num - 1, len(ebbinghaus) - 1)]
        return start_time + datetime.timedelta(days=days)


def get_sentence_cards(num=10, new_word_percent=0.5):
    """
    获取待学习的句子卡片
    复用现有卡片系统的逻辑
    """
    try:
        current_time = datetime.datetime.now()
        
        # 获取新句子（未学习过的）
        target_new_num = int(num * new_word_percent)
        if new_word_percent > 0 and target_new_num == 0:
            target_new_num = 1
        if target_new_num > num:
            target_new_num = num
        
        # 查询新句子
        new_cards = FrontCard.objects.filter(
            content_type=CONTENT_TYPE_SENTENCE,
            repeat_num=0
        ).order_by('next_study_time')[:target_new_num]
        
        # 查询需要复习的句子
        review_cards = FrontCard.objects.filter(
            content_type=CONTENT_TYPE_SENTENCE,
            repeat_num__gt=0,
            repeat_num__lt=5,
            next_study_time__lte=current_time
        ).order_by('next_study_time')[:num - target_new_num]
        
        # 合并并去重
        front_cards = list(new_cards) + list(review_cards)
        
        if not front_cards:
            return None
        
        # 组装卡片数据
        result = []
        for front_card in front_cards[:num]:
            try:
                # 获取关联的背面卡片
                relation = CardRelation.objects.filter(front_id=front_card.front_id).first()
                if not relation:
                    continue
                    
                back_card = BackCard.objects.get(back_id=relation.back_id)
                
                # 解析句子ID
                sentence_id = None
                if relation.description and '句子ID:' in relation.description:
                    try:
                        sentence_id = int(relation.description.split('句子ID:')[1])
                    except:
                        pass
                
                # 获取文章图片（如果有）
                image_url = None
                if sentence_id:
                    try:
                        sentence = ArticleSentence.objects.select_related('article').get(id=sentence_id)
                        if sentence.article.image_path:
                            image_url = '/' + sentence.article.image_path
                    except:
                        pass
                
                card = {
                    'front_id': front_card.front_id,
                    'back_id': back_card.back_id,
                    'content_type': CONTENT_TYPE_SENTENCE,
                    'chinese_sentence': front_card.front_card_content,
                    'english_sentence': back_card.back_card_content,
                    'context_hint': front_card.description,
                    'sentence_id': sentence_id,
                    'repeat_num': front_card.repeat_num,
                    'image_url': image_url
                }
                result.append(card)
            except Exception as e:
                print(f"组装卡片数据失败: {e}")
                continue
        
        return result
    except Exception as e:
        print(f"获取句子卡片失败: {e}")
        return None


def get_article_list(page=1, page_size=10, exam_type=None, article_type=None,
                     difficulty=None, topic=None, tags=None):
    """
    获取文章列表 - 支持多种标签过滤

    Args:
        page: 页码
        page_size: 每页数量
        exam_type: 考试类型（ielts, cet4, cet6, 考研等）- 支持多选
        article_type: 文章类型 - 支持多选
        difficulty: 难度等级 - 支持多选
        topic: 话题分类
        tags: 标签列表，用于过滤包含这些标签的文章
    """
    queryset = Article.objects.all()

    # 支持多个考试类型筛选
    if exam_type:
        exam_types = exam_type.split(',') if isinstance(exam_type, str) and ',' in exam_type else [exam_type]
        exam_type_filter = Q()
        for et in exam_types:
            if et.strip():
                exam_type_filter |= Q(exam_type=et.strip())
        queryset = queryset.filter(exam_type_filter)

    # 支持多个文章类型筛选
    if article_type:
        article_types = article_type.split(',') if isinstance(article_type, str) and ',' in article_type else [article_type]
        article_type_filter = Q()
        for at in article_types:
            if at.strip():
                article_type_filter |= Q(article_type=at.strip())
        queryset = queryset.filter(article_type_filter)

    # 支持多个难度筛选
    if difficulty is not None:
        difficulties = difficulty.split(',') if isinstance(difficulty, str) and ',' in difficulty else [difficulty]
        difficulty_filter = Q()
        for diff in difficulties:
            try:
                diff_value = int(diff.strip())
                difficulty_filter |= Q(difficulty=diff_value)
            except ValueError:
                continue
        queryset = queryset.filter(difficulty_filter)

    if topic:
        queryset = queryset.filter(topic__icontains=topic)
    if tags and isinstance(tags, list):
        # 支持多个标签过滤 - 文章包含任意一个标签即可
        tag_filter = Q()
        for tag in tags:
            tag_filter |= Q(tags__contains=tag)
        queryset = queryset.filter(tag_filter)
    
    queryset = queryset.order_by('-create_time')
    
    paginator = Paginator(queryset, page_size)
    try:
        paginated_data = paginator.page(page)
    except PageNotAnInteger:
        paginated_data = paginator.page(1)
    except EmptyPage:
        paginated_data = paginator.page(paginator.num_pages)
    
    # 组装数据
    data = []
    for article in paginated_data:
        sentence_count = ArticleSentence.objects.filter(article=article).count()
        learned_count = SentenceLearningLog.objects.filter(
            sentence__article=article
        ).values('sentence').distinct().count()
        
        # 计算进度
        progress = 0
        if sentence_count > 0:
            progress = int((learned_count / sentence_count) * 100)
        
        # 图片URL转换
        image_url = None
        if article.image_path:
            # 返回相对路径，前端拼接为完整URL
            image_url = '/' + article.image_path.replace('\\', '/')
        
        data.append({
            'id': article.id,
            'title': article.title,
            'exam_type': article.exam_type,
            'article_type': article.article_type,
            'tags': article.tags,
            'topic': article.topic,
            'difficulty': article.difficulty,
            'image_path': article.image_path,
            'image_url': image_url,
            'sentence_count': sentence_count,
            'learned_count': learned_count,
            'progress': progress,
            'create_time': article.create_time.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return {
        'total': paginator.count,
        'page': paginated_data.number,
        'page_size': page_size,
        'total_pages': paginator.num_pages,
        'data': data
    }


def get_article_detail(article_id):
    """
    获取文章详情
    """
    try:
        article = Article.objects.get(id=article_id)
        sentences = ArticleSentence.objects.filter(article=article).order_by('sequence')
        
        # 图片URL转换
        image_url = None
        if article.image_path:
            image_url = '/' + article.image_path.replace('\\', '/')
        
        return {
            'success': True,
            'data': {
                'id': article.id,
                'title': article.title,
                'exam_type': article.exam_type,
                'article_type': article.article_type,
                'tags': article.tags,
                'topic': article.topic,
                'difficulty': article.difficulty,
                'content': article.content,
                'image_path': article.image_path,
                'image_url': image_url,
                'sentences': [
                    {
                        'id': s.id,
                        'sequence': s.sequence,
                        'english': s.english,
                        'chinese': s.chinese,
                        'is_key_sentence': s.is_key_sentence
                    }
                    for s in sentences
                ]
            }
        }
    except Article.DoesNotExist:
        return {
            'success': False,
            'error': '文章不存在'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def delete_article(article_id):
    """
    删除文章及相关数据
    """
    try:
        with transaction.atomic():
            article = Article.objects.get(id=article_id)
            
            # 删除文章图片
            if article.image_path and os.path.exists(article.image_path):
                try:
                    os.remove(article.image_path)
                except:
                    pass
            
            # 删除相关的学习卡片
            sentences = ArticleSentence.objects.filter(article=article)
            for sentence in sentences:
                # 找到相关的卡片关联
                relations = CardRelation.objects.filter(
                    description__contains=f'句子ID:{sentence.id}'
                )
                for relation in relations:
                    # 删除正背面卡片
                    FrontCard.objects.filter(front_id=relation.front_id).delete()
                    BackCard.objects.filter(back_id=relation.back_id).delete()
                    relation.delete()
            
            # 删除文章（会级联删除句子）
            article.delete()
            
            return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def record_learning_log(sentence_id, user_translation, ai_evaluation, user_id=0):
    """
    记录学习日志
    """
    try:
        sentence = ArticleSentence.objects.get(id=sentence_id)
        
        log = SentenceLearningLog.objects.create(
            user_id=user_id,
            sentence=sentence,
            user_translation=user_translation,
            ai_evaluation=ai_evaluation,
            has_error=ai_evaluation.get('has_error', False) if ai_evaluation else False
        )
        
        return {'success': True, 'log_id': log.id}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_learning_stats(user_id=0):
    """
    获取学习统计
    """
    try:
        # 总句子数
        total_sentences = ArticleSentence.objects.count()
        
        # 已学习的句子数（有学习记录）
        learned_sentences = SentenceLearningLog.objects.filter(
            user_id=user_id
        ).values('sentence').distinct().count()
        
        # 有错误的句子数
        error_sentences = SentenceLearningLog.objects.filter(
            user_id=user_id,
            has_error=True
        ).values('sentence').distinct().count()
        
        # 今日学习数
        today = timezone.now().date()
        today_learned = SentenceLearningLog.objects.filter(
            user_id=user_id,
            study_date__date=today
        ).count()
        
        return {
            'total_sentences': total_sentences,
            'learned_sentences': learned_sentences,
            'error_sentences': error_sentences,
            'today_learned': today_learned
        }
    except Exception as e:
        return {
            'total_sentences': 0,
            'learned_sentences': 0,
            'error_sentences': 0,
            'today_learned': 0,
            'error': str(e)
        }


def get_error_sentences(user_id=0, page=1, page_size=10):
    """
    获取错题本
    """
    try:
        # 获取有错误的学习记录
        logs = SentenceLearningLog.objects.filter(
            user_id=user_id,
            has_error=True
        ).select_related('sentence', 'sentence__article').order_by('-study_date')
        
        paginator = Paginator(logs, page_size)
        try:
            paginated_data = paginator.page(page)
        except PageNotAnInteger:
            paginated_data = paginator.page(1)
        except EmptyPage:
            paginated_data = paginator.page(paginator.num_pages)
        
        data = []
        for log in paginated_data:
            data.append({
                'log_id': log.id,
                'sentence_id': log.sentence.id,
                'chinese': log.sentence.chinese,
                'english': log.sentence.english,
                'user_translation': log.user_translation,
                'ai_evaluation': log.ai_evaluation,
                'article_title': log.sentence.article.title,
                'image_path': log.sentence.article.image_path,
                'study_date': log.study_date.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return {
            'total': paginator.count,
            'page': paginated_data.number,
            'page_size': page_size,
            'data': data
        }
    except Exception as e:
        return {
            'total': 0,
            'page': page,
            'page_size': page_size,
            'data': [],
            'error': str(e)
        }


def get_all_tags():
    """
    获取所有文章的标签列表（用于标签云/筛选）
    """
    try:
        # 获取所有文章的标签
        all_tags = set()
        articles = Article.objects.exclude(tags__isnull=True).exclude(tags=[])
        
        for article in articles:
            if isinstance(article.tags, list):
                all_tags.update(article.tags)
        
        return {
            'success': True,
            'tags': sorted(list(all_tags))
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'tags': []
        }


def get_all_exam_types():
    """
    获取所有考试类型
    """
    try:
        exam_types = Article.objects.values_list('exam_type', flat=True).distinct()
        return {
            'success': True,
            'exam_types': sorted(list(set(exam_types)))
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'exam_types': []
        }


def get_all_article_types(exam_type=None):
    """
    获取所有文章类型
    
    Args:
        exam_type: 可选，按考试类型筛选
    """
    try:
        queryset = Article.objects.exclude(article_type__isnull=True).exclude(article_type='')
        if exam_type:
            queryset = queryset.filter(exam_type=exam_type)
        
        article_types = queryset.values_list('article_type', flat=True).distinct()
        return {
            'success': True,
            'article_types': sorted(list(set(article_types)))
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'article_types': []
        }


def update_sentence(sentence_id, english=None, chinese=None):
    """
    更新句子内容
    
    Args:
        sentence_id: 句子ID
        english: 英文内容（可选）
        chinese: 中文内容（可选）
    """
    try:
        sentence = ArticleSentence.objects.get(id=sentence_id)
        
        if english is not None:
            sentence.english = english
        if chinese is not None:
            sentence.chinese = chinese
        
        sentence.save()
        
        # 同时更新关联的卡片
        try:
            relations = CardRelation.objects.filter(
                description__contains=f'句子ID:{sentence_id}'
            )
            for relation in relations:
                if english:
                    BackCard.objects.filter(back_id=relation.back_id).update(
                        back_card_content=english
                    )
                if chinese:
                    FrontCard.objects.filter(front_id=relation.front_id).update(
                        front_card_content=chinese
                    )
        except Exception as e:
            print(f"更新卡片失败: {e}")
        
        return {'success': True}
    except ArticleSentence.DoesNotExist:
        return {'success': False, 'error': '句子不存在'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def delete_sentence(sentence_id):
    """
    删除句子及其关联的卡片
    
    Args:
        sentence_id: 句子ID
    """
    try:
        sentence = ArticleSentence.objects.get(id=sentence_id)
        
        # 删除关联的卡片
        relations = CardRelation.objects.filter(
            description__contains=f'句子ID:{sentence_id}'
        )
        for relation in relations:
            FrontCard.objects.filter(front_id=relation.front_id).delete()
            BackCard.objects.filter(back_id=relation.back_id).delete()
            relation.delete()
        
        # 删除句子
        sentence.delete()
        
        return {'success': True}
    except ArticleSentence.DoesNotExist:
        return {'success': False, 'error': '句子不存在'}
    except Exception as e:
        return {'success': False, 'error': str(e)}
