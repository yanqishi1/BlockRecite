"""
AI 评测服务 - 用于评估用户翻译质量（使用 DeepSeek API）
"""
from server.service.ai_service.deepseek_service import (
    chat_completion_json,
    chat_completion_text,
    _extract_json
)


def evaluate_translation(chinese, user_translation, reference_translation=None):
    """
    评估用户翻译质量

    Args:
        chinese: 中文原文
        user_translation: 用户翻译的英文
        reference_translation: 参考译文（可选）

    Returns:
        dict: 评测结果
        {
            'has_error': bool,
            'error_details': [...],
            'rating': 'excellent'|'good'|'acceptable'|'incorrect',
            'optimized_version': str,
            'learning_tip': str
        }
    """
    try:
        prompt = build_evaluation_prompt(chinese, user_translation, reference_translation)

        messages = [
            {
                "role": "system",
                "content": "你是一位专业的英语写作批改老师，擅长评估中译英翻译质量。请严格按照 JSON 格式返回结果。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        result = chat_completion_json(messages, temperature=0.3, max_tokens=2000)
        evaluation_result = parse_evaluation_result(result)

        return evaluation_result

    except Exception as e:
        print(f"AI 评测失败: {e}")
        # 返回基础评测结果
        return {
            'has_error': False,
            'error_details': [],
            'rating': 'unknown',
            'optimized_version': user_translation,
            'learning_tip': f'评测服务暂时不可用，请稍后重试。错误: {str(e)}'
        }


def build_evaluation_prompt(chinese, user_translation, reference_translation=None):
    """
    构建评测提示词
    """
    reference_part = f'\n参考译文：{reference_translation}' if reference_translation else ''
    
    prompt = f'''请评估以下中译英翻译质量：

中文原文：{chinese}
用户翻译：{user_translation}{reference_part}

请从以下几个方面进行评估：
1. 语法是否正确
2. 拼写是否正确
3. 表达是否地道、自然
4. 是否准确传达中文原意

请严格按照以下 JSON 格式返回评估结果：
{{
  "has_error": true/false,
  "error_details": [
    {{
      "type": "grammar|spelling|expression",
      "position": "错误位置（原文中的片段）",
      "description": "错误描述",
      "suggestion": "修改建议"
    }}
  ],
  "rating": "excellent|good|acceptable|incorrect",
  "optimized_version": "优化后的句子",
  "learning_tip": "学习建议（针对这个句子的语言点）"
}}

rating 定义：
- excellent: 翻译优秀，几乎无瑕疵
- good: 翻译良好，有小问题但不影响理解
- acceptable: 翻译可接受，有错误但能传达基本意思
- incorrect: 翻译错误，无法理解或严重偏离原意

注意：
1. 必须返回合法的 JSON 格式
2. 如果翻译完全正确，error_details 为空数组，has_error 为 false
3. optimized_version 应该提供最佳的表达方式
4. learning_tip 要简洁实用，帮助用户进步'''
    
    return prompt


def parse_evaluation_result(result):
    """
    解析/验证 AI 返回的评测结果

    Args:
        result: 已解析的 JSON 对象（dict）或 None

    Returns:
        dict: 验证后的评测结果
    """
    # 验证必要字段
    default_result = {
        'has_error': False,
        'error_details': [],
        'rating': 'unknown',
        'optimized_version': '',
        'learning_tip': ''
    }

    # 如果解析失败（result 为 None）
    if not result or not isinstance(result, dict):
        return default_result

    # 合并结果
    for key in default_result:
        if key in result:
            default_result[key] = result[key]

    # 确保 error_details 是列表
    if not isinstance(default_result['error_details'], list):
        default_result['error_details'] = []

    # 验证 rating 值
    valid_ratings = ['excellent', 'good', 'acceptable', 'incorrect', 'unknown']
    if default_result['rating'] not in valid_ratings:
        default_result['rating'] = 'unknown'

    return default_result


def batch_translate_sentences(sentences):
    """
    批量翻译句子（英文翻译成中文）
    用于智能分句后的自动翻译

    Args:
        sentences: ['英文句子1', '英文句子2', ...]

    Returns:
        ['中文翻译1', '中文翻译2', ...]
    """
    if not sentences:
        return []

    try:
        sentences_text = "\n".join([f"{i+1}. {s}" for i, s in enumerate(sentences)])

        prompt = f'''请将以下英文句子翻译成中文：

{sentences_text}

请严格按照以下 JSON 格式返回翻译结果：
{{
  "translations": [
    "中文翻译1",
    "中文翻译2",
    ...
  ]
}}

要求：
1. 翻译要准确、自然
2. 必须返回合法的 JSON 格式
3. 保持原文顺序，一一对应
4. 只返回中文翻译，不要包含英文原文'''

        messages = [
            {
                "role": "system",
                "content": "你是一位专业的翻译助手，擅长英译中。请严格按照要求的 JSON 格式返回结果。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        result = chat_completion_json(messages, temperature=0.3, max_tokens=3000)

        if result and 'translations' in result and isinstance(result['translations'], list):
            translations = result['translations']
            # 确保翻译数量和原文数量一致
            if len(translations) == len(sentences):
                return translations
            else:
                # 如果数量不匹配，补齐
                while len(translations) < len(sentences):
                    translations.append(sentences[len(translations)])
                return translations[:len(sentences)]
        else:
            # 返回原文作为后备
            return sentences

    except Exception as e:
        print(f"批量翻译失败: {e}")
        # 返回原文作为后备
        return sentences


def simple_translate(text, from_lang='en', to_lang='zh'):
    """
    简单翻译单个句子
    """
    try:
        prompt = f'请将以下内容翻译成{"中文" if to_lang == "zh" else "英文"}，只返回翻译结果，不要解释：\n\n{text}'

        messages = [
            {
                "role": "system",
                "content": "你是一位专业的翻译助手。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        result = chat_completion_text(messages, temperature=0.3, max_tokens=500)
        return result or text

    except Exception as e:
        print(f"翻译失败: {e}")
        return text


def generate_essay_from_topic(topic, exam_type='ielts', title=None, word_count_target=400):
    """
    根据作文题目/话题，调用 AI 生成一篇英文范文。
    用于「提交题目 → 一键生成范文并分句」的一体化流程。

    Args:
        topic: 作文题目或话题（中英文均可）
        exam_type: 考试类型，如 ielts, cet4, cet6, 考研
        title: 可选，作为文章标题
        word_count_target: 目标字数，默认 400

    Returns:
        str: 英文范文正文；失败时返回空字符串
    """
    try:
        exam_hint = {
            'ielts': '雅思写作风格，学术、地道',
            'cet4': '英语四级写作风格',
            'cet6': '英语六级写作风格',
            '考研': '考研英语写作风格',
            '托福': '托福写作风格',
        }.get(exam_type, '学术英语写作风格')
        title_str = title or topic
        prompt = f'''请根据以下作文题目/话题，写一篇英文范文。

题目/话题：{topic}
考试类型：{exam_type}，要求：{exam_hint}
目标字数：约 {word_count_target} 词。

要求：
1. 只输出范文正文，不要输出题目、解释或中文。
2. 使用完整、地道的英文句子，适合作为中译英练习材料。
3. 段落清晰，句号、问号、感叹号结尾的完整句子。'''

        messages = [
            {
                "role": "system",
                "content": "你是一位专业的英语写作教师，擅长各类考试范文写作。只输出英文范文正文，不要任何解释或中文。"
            },
            {"role": "user", "content": prompt}
        ]

        return chat_completion_text(messages, temperature=0.6, max_tokens=2000)

    except Exception as e:
        print(f"AI 生成范文失败: {e}")
        return ""
