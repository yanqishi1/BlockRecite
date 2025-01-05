"""
URL configuration for BlockRecite project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from server.views import *
urlpatterns = [
    path("admin/", admin.site.urls),

    path("", home_page),
    path("recite", recite_page),
    path("create_card_page", create_card_page),
    path("setting", setting_page),
    path("test", voice_page),

    path("api/trans_word", trans_word),
    path("api/generate_card", generate_card),
    path("api/get_recite_card", get_recite_card),
    path("api/remember", remember),
    path("api/forget", forget),
    path("api/master", master_remember),
    path("api/ocr", ocr),
    path("api/get_voice",get_voice),
    path("api/get_image",get_image),
    path("api/get_recite_history", get_recite_history),
    path("api/generate_img_card", generate_img_card),
    path("api/talk_to_trans", talk_to_trans),
    path("api/get_talk_history", get_talk_history),
    path("api/del_talk_history", del_talk_history),
    path("api/get_card_base_info",get_card_base_info),
    path("api/back_word_list",get_back_word_list),
]
