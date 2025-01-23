from django.db import models
from django.contrib import admin
from enum import IntEnum

class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=64)
    password = models.CharField(max_length=64)
    email = models.EmailField()
    phone = models.CharField(max_length=32)
    user_type = models.IntegerField()
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)


class ContentType(IntEnum):
    """内容类型枚举"""
    SENTENCE = 0       # 普通句子
    LISTENING = 1      # 听力句子
    IMAGE = 2         # 图片内容
    VIDEO = 3         # 视频内容
    CN_TO_EN = 4      # 汉译英句子

    @classmethod
    def choices(cls):
        """返回Django模型可用的choices元组列表"""
        return [(item.value, item.name) for item in cls]

    @classmethod
    def get_type_name(cls, value):
        """根据值获取类型名称"""
        try:
            return cls(value).name
        except ValueError:
            return "UNKNOWN"


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