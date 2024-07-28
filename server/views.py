from django.shortcuts import render,HttpResponse
from server.service import card_service
import json

def recite_page(request):
    return render(request, "recite.html")

def create_card_page(request):
    return render(request, "CardCreator.html")

def home_page(request):
    return render(request, "Home.html")

def trans(request):
    return HttpResponse(json.dumps({'code':0, 'message':'success','data':'success'}))

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