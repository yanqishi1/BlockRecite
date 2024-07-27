from django.shortcuts import render,HttpResponse
from server.service import card_service
import json

def index(request):
    return render(request, "index.html")

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
        card_service.generate_card(front_card,back_card)
        return HttpResponse(json.dumps({'code':200, 'message':'success'}))
    else:
        return HttpResponse(json.dumps({'code':0, 'message':'method not allowed'}))


def get_recite_card(request):
    num = request.GET.get('num')
    recite_content = card_service.get_recite_content(num)
    if recite_content is None:
        return HttpResponse(json.dumps({'code': 200, 'message': 'No word need to recite', 'data': None}))
    else:
        return HttpResponse(json.dumps({'code':200, 'message':'success','data':recite_content}))