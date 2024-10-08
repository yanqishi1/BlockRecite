from datetime import datetime
from server.util.SQLiteDBUtil import SQLiteDBUtil
from server.models import FrontCard,BackCard,CardRelation
import datetime
from translate import Translator
from server.service.translate_api.stardict import StarDict
from cnocr import CnOcr
import io
from PIL import Image

WORD = 0
SENTENCE = 1
Ebbinghaus = [1,2,4,7,15,30]
# 在任何两种语言之间，中文翻译成英文
translator = Translator(from_lang="chinese", to_lang="english")
cn_OCR = CnOcr()


'''
    生成卡片
'''
def generate_card(front_card,back_cards):
    current_time = datetime.datetime.now()

    front_content = front_card.get('content')
    front_desc = front_card.get('desc', None)
    if front_desc is None:
        front_desc = explain(front_content,SENTENCE)
    front_card = FrontCard.objects.create(front_card_content=front_content,
                                          description=front_desc,
                                          next_study_time=get_recite_time(current_time,0))

    for back_card in back_cards:
        content = back_card.get('content', None)
        desc = back_card.get('desc',None)
        if desc is None:
            desc = explain(content,WORD)

        back_card = BackCard.objects.create(back_card_content=content,
                                              description=desc,
                                              next_study_time=get_recite_time(current_time,0))

        CardRelation.objects.create(front_id=front_card.front_id,back_id=back_card.back_id,description=desc)



def explain(content, type):
    if type==WORD:
        # 预处理
        content = content.replace(" ","")
        if content.endswith("."):
            content = content.replace(".","")

        star_dict = StarDict("./stardict.db")
        return star_dict.query(content)
    elif type==SENTENCE:
        return translator.translate(content)
    else:
        raise Exception("Unknown type")

'''
艾宾浩斯遗忘曲线
'''
def get_recite_time(create_time,recite_num):
    if recite_num==0:
        return create_time + datetime.timedelta(minutes=30)
    elif recite_num==1:
        return create_time + datetime.timedelta(hours=12)
    else:
        return create_time + datetime.timedelta(days=Ebbinghaus[recite_num-1])

'''
复习单词
'''
def get_recite_content(recite_num):
    try:
        sqlite_db = SQLiteDBUtil('db.sqlite3')
        current_time = datetime.datetime.now()
        current_time = current_time.strftime('%Y-%m-%d %H:%M:%S')
        # 定义 SQL 查询
        sql = f"""
            SELECT back_id FROM server_backcard
            WHERE next_study_time <= '{current_time}'
        """

        # 执行 SQL 查询
        db_results = sqlite_db.query(sql)
        back_ids = []
        for result in db_results:
            back_ids.append(str(result[0]))

        if back_ids is None or len(back_ids)==0:
            return None

        back_id_str = ",".join(back_ids)
        sql = f"""select 
                        front.front_card_content, 
                       back.back_card_content,
                       front.description,
                       rel.description,
                       front.front_id,
                       back.back_id
                from server_cardrelation as rel,
                              server_backcard as back,
                              server_frontcard as front
                where
                    rel.back_id =back.back_id
                    and rel.front_id=front.front_id
                    and back.back_id in ({back_id_str})
                order by back.next_study_time
                limit {recite_num}"""

        recite_content = []
        db_results = sqlite_db.query(sql)
        for db_result in db_results:
            card = {}
            # 正面
            card['front_card_content'] = db_result[0]
            # 背面
            card['word'] = db_result[1]
            card['sentence_explain'] = db_result[2]
            card['word_explain'] = db_result[3]

            card['front_id'] = db_result[4]
            card['back_id'] = db_result[5]
            recite_content.append(card)
        return recite_content
    except Exception as e:
        print(e)
        return None

'''
标注记住，进入艾宾浩斯曲线的下一个复习阶段
'''
def remember(front_id,back_id):
    try:
        # 增加复习时间
        back_card = BackCard.objects.get(back_id=back_id)
        if back_card is None:
            return False
        back_card.repeat_num = back_card.repeat_num + 1
        back_card.next_study_time = get_recite_time(back_card.create_time, back_card.repeat_num+1)
        back_card.save()

        front_card = FrontCard.objects.get(front_id=front_id)
        if front_card is None:
            return False
        front_card.repeat_num = front_card.repeat_num + 1
        front_card.next_study_time = get_recite_time(front_card.create_time, front_card.repeat_num+1)
        front_card.save()

        return True
    except Exception as e:
        print(e)
        return False

'''
标注忘记
'''
def forget(front_id,back_id):
    try:
        # 更新复习时间为30min
        back_card = BackCard.objects.get(back_id=back_id)
        if back_card is None:
            return False
        back_card.repeat_num = 0
        back_card.next_study_time = get_recite_time(back_card.create_time, back_card.repeat_num)
        back_card.save()

        front_card = FrontCard.objects.get(front_id=front_id)
        if front_card is None:
            return False
        front_card.repeat_num = 0
        front_card.next_study_time = get_recite_time(front_card.create_time, front_card.repeat_num)
        front_card.save()

        return True
    except Exception as e:
        print(e)
        return False

def convert_to_image(uploaded_file):
    # 将上传的文件内容读取到字节流中
    image_stream = io.BytesIO(uploaded_file.read())
    # 使用 PIL 打开字节流
    image = Image.open(image_stream)
    return image


def ocr(upload_img):
    re_text = None
    if upload_img is None:
        return re_text

    try:
        image = convert_to_image(upload_img)
        results = cn_OCR.ocr(image)

        re_text = ""
        for result in results:
            re_text += result['text']
    except Exception as e:
        print(e)

    return re_text
