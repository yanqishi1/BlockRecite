from django.db import models
from django.contrib import admin


# Create your models here.
class FrontCard(models.Model):
    front_id = models.AutoField(primary_key=True)
    front_card_content = models.TextField()
    description = models.TextField()
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    repeat_num = models.IntegerField(default=0)
    next_study_time = models.DateTimeField()


class BackCard(models.Model):
    back_id = models.AutoField(primary_key=True)
    back_card_content = models.TextField()
    description = models.TextField()
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    repeat_num = models.IntegerField(default=0)
    next_study_time = models.DateTimeField()


class CardRelation(models.Model):
    card_id = models.AutoField(primary_key=True)
    front_id = models.IntegerField()
    back_id = models.IntegerField()
    create_time = models.DateTimeField(auto_now_add=True)
    description = models.TextField()


@admin.register(FrontCard)
class FrontCardAdmin(admin.ModelAdmin):
    list_display = ("front_id","front_card_content","description","create_time","update_time","repeat_num","next_study_time")
    ordering = ("create_time",)


@admin.register(BackCard)
class BackCardAdmin(admin.ModelAdmin):
    list_display = ("back_id","back_card_content","description","create_time","update_time","repeat_num","next_study_time")
    ordering = ("create_time",)


@admin.register(CardRelation)
class CardRelationAdmin(admin.ModelAdmin):
    list_display = ("card_id","front_id","back_id","description","create_time")
    ordering = ("create_time",)