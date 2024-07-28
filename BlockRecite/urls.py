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

from server.views import home_page,recite_page,create_card_page,generate_card,get_recite_card,remember,forget,trans
urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home_page),
    path("recite", recite_page),
    path("create_card_page", create_card_page),
    path("api/trans", trans),
    path("api/generate_card", generate_card),
    path("api/get_recite_card", get_recite_card),
    path("api/remember", remember),
    path("api/forget", forget),
]
