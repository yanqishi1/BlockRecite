from django.db import models
from django.contrib import admin


# Create your models here.
class FrontCard(models.Model):
    front_id = models.AutoField(primary_key=True)
    # 句子、图片、视频、音频
    front_card_content = models.TextField()
    # 句子0、来自听力的句子1, 图片2、视频3、口语句子：汉翻英4
    content_type = models.IntegerField(default=0)
    # 翻译
    description = models.TextField()
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    # 背诵单词的起始时间
    start_recite_time_point = models.DateTimeField(default=None, null=True)
    # 复习次数，如果记错了，重置为0
    repeat_num = models.IntegerField(default=0)
    # 下次学习时间
    next_study_time = models.DateTimeField()


class BackCard(models.Model):
    back_id = models.AutoField(primary_key=True)
    # 单词
    back_card_content = models.TextField()
    # 句子0、图片1、视频2、音频3、口语句子：汉翻英4
    content_type = models.IntegerField(default=0)
    # 单词的全面释义
    description = models.TextField()
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    # 背诵单词的起始时间
    start_recite_time_point = models.DateTimeField(default=None, null=True)
    # 复习次数，如果记错了，重置为0
    repeat_num = models.IntegerField(default=0)
    # 下次学习时间
    next_study_time = models.DateTimeField()


class CardRelation(models.Model):
    card_id = models.AutoField(primary_key=True)
    front_id = models.IntegerField()
    back_id = models.IntegerField()
    create_time = models.DateTimeField(auto_now_add=True)
    # 单词在(句子/视频/音频)中的解释
    description = models.TextField()

class ReciteHistory(models.Model):
    recite_id = models.AutoField(primary_key=True)
    # 0表示单词，1表示句子
    type = models.IntegerField(default=0)
    # 背诵的单词个数
    recite_num = models.IntegerField(default=0)
    # 时间
    create_time = models.DateTimeField(auto_now_add=True)

class VoiceTranslateHistory(models.Model):
    voice_id = models.AutoField(primary_key=True)
    user_id = models.IntegerField(default=0)
    voice_text = models.TextField()
    translate_text = models.TextField()
    # 时间
    create_time = models.DateTimeField(auto_now_add=True)

@admin.register(FrontCard)
class FrontCardAdmin(admin.ModelAdmin):
    # Define the fields that can be edited in the admin interface
    # list_editable = (
    #     "front_card_content",
    #     "content_type",
    #     "description",
    #     "start_recite_time_point",
    #     "repeat_num",
    #     "next_study_time",
    # )

    list_display = ("front_id","content_type","front_card_content","description","create_time","update_time","start_recite_time_point","repeat_num","next_study_time","content_type")
    ordering = ("create_time",)


@admin.register(BackCard)
class BackCardAdmin(admin.ModelAdmin):
    list_display = ("back_id","back_card_content","content_type","description","create_time","update_time","start_recite_time_point","repeat_num","next_study_time")
    ordering = ("create_time",)


@admin.register(CardRelation)
class CardRelationAdmin(admin.ModelAdmin):
    list_display = ("card_id","front_id","back_id","description","create_time")
    ordering = ("create_time",)

@admin.register(ReciteHistory)
class ReciteHistoryAdmin(admin.ModelAdmin):
    list_display = ("recite_id","recite_num","type","create_time")
    ordering = ("create_time",)

@admin.register(VoiceTranslateHistory)
class VoiceTranslateHistoryAdmin(admin.ModelAdmin):
    list_display = ("voice_id","voice_text","translate_text","create_time")
    ordering = ("create_time",)


# ==================== 句子翻译学习功能数据模型 ====================

class Article(models.Model):
    """文章表 - 支持多种考试类型（雅思、四六级、考研等）"""
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255, verbose_name="文章题目/标题")
    # 图片路径，用于保存文章题目图片
    image_path = models.CharField(max_length=500, blank=True, verbose_name="题目图片路径")
    # 考试类型：ielts, cet4, cet6,考研, 自定义等
    exam_type = models.CharField(max_length=50, default="ielts", verbose_name="考试类型")
    # 文章类型（不同考试有不同的类型，如雅思Task1/Task2，四六级作文类型等）
    article_type = models.CharField(max_length=100, blank=True, verbose_name="文章类型")
    # 自定义标签，JSON格式存储多个标签 ["标签1", "标签2"]
    tags = models.JSONField(default=list, blank=True, verbose_name="自定义标签")
    # 难度等级 1-5
    difficulty = models.IntegerField(default=3, verbose_name="难度等级")
    # 话题分类
    topic = models.CharField(max_length=100, blank=True, verbose_name="话题分类")
    content = models.TextField(verbose_name="完整文章内容")
    is_system = models.BooleanField(default=False, verbose_name="是否系统预设")
    created_by = models.IntegerField(default=0, verbose_name="创建者ID")
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'articles'
        ordering = ['-create_time']

    def __str__(self):
        return self.title


class ArticleSentence(models.Model):
    """文章句子表"""
    id = models.AutoField(primary_key=True)
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='sentences')
    sequence = models.IntegerField(verbose_name="句子在文章中的顺序")
    english = models.TextField(verbose_name="英文原句")
    chinese = models.TextField(verbose_name="中文翻译")
    is_key_sentence = models.BooleanField(default=True, verbose_name="是否重点句")
    create_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'article_sentences'
        ordering = ['article', 'sequence']

    def __str__(self):
        return f"{self.article.title} - 句子{self.sequence}"


class SentenceLearningLog(models.Model):
    """句子学习记录表"""
    id = models.AutoField(primary_key=True)
    user_id = models.IntegerField(default=0, verbose_name="用户ID")
    sentence = models.ForeignKey(ArticleSentence, on_delete=models.CASCADE, related_name='learning_logs')
    user_translation = models.TextField(verbose_name="用户翻译内容")
    ai_evaluation = models.JSONField(null=True, blank=True, verbose_name="AI评测结果")
    has_error = models.BooleanField(default=False, verbose_name="是否有错误")
    study_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sentence_learning_logs'
        ordering = ['-study_date']

    def __str__(self):
        return f"学习记录 - {self.sentence.english[:30]}..."


# 注册到 Django Admin
@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "exam_type", "article_type", "difficulty", "is_system", "create_time")
    list_filter = ("exam_type", "difficulty", "is_system")
    search_fields = ("title", "content")
    ordering = ("-create_time",)


@admin.register(ArticleSentence)
class ArticleSentenceAdmin(admin.ModelAdmin):
    list_display = ("id", "article", "sequence", "chinese", "is_key_sentence")
    list_filter = ("is_key_sentence",)
    search_fields = ("english", "chinese")
    ordering = ("article", "sequence")


@admin.register(SentenceLearningLog)
class SentenceLearningLogAdmin(admin.ModelAdmin):
    list_display = ("id", "user_id", "sentence", "has_error", "study_date")
    list_filter = ("has_error",)
    ordering = ("-study_date",)
