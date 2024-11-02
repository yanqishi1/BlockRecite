from django.shortcuts import render,HttpResponse
import os
from server.service import card_service
import json

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
        return HttpResponse(json.dumps({'code':0, 'message':'success','data':translation}),content_type="application/json; charset=utf-8")
    else:
        return HttpResponse(json.dumps({'code':0, 'message':'method not allowed'}))



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
    num = int(request.GET.get('num'))
    if num is None:
        num = 30
    recite_content = card_service.get_recite_content(num)
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