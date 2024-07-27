from datetime import datetime
from server.util.SQLiteDBUtil import SQLiteDBUtil
from server.models import FrontCard,BackCard,CardRelation
import datetime


WORD = 0
SENTENCE = 1
Ebbinghaus = [1,2,4,7,15,30]



def generate_card(front_cards,back_card):
    current_time = datetime.datetime.now()

    back_content = back_card.get('content')
    back_desc = back_card.get('desc', None)
    if back_desc is None:
        back_desc = explain(back_content,WORD)
    back_card = BackCard.objects.create(back_card_content=back_content,
                                          description=explain(back_desc,SENTENCE),
                                          next_study_time=get_recite_time(current_time,0))

    for front_card in front_cards:
        content = front_card.get('content', None)
        desc = front_card.get('desc',None)
        if desc is None:
            desc = explain(content,WORD)

        front_card = FrontCard.objects.create(front_card_content=content,
                                              description=desc,
                                              next_study_time=get_recite_time(current_time,0))

        CardRelation.objects.create(front_id=front_card.front_id,back_id=back_card.back_id,description=desc)



def explain(content, type):
    if type==WORD:
        return content
    elif type==SENTENCE:
        return content
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


def get_recite_content(recite_num):
    sqlite_db = SQLiteDBUtil('db.sqlite3')
    current_time = datetime.datetime.now()
    current_time = '2024-07-27 18:00:00'#current_time.strftime('%Y-%m-%d %H:%M:%S')
    # 定义 SQL 查询
    sql = f"""
        SELECT front_id FROM server_frontcard
        WHERE next_study_time <= '{current_time}'
    """

    # 执行 SQL 查询
    db_results = sqlite_db.query(sql)
    front_ids = []
    for result in db_results:
        front_ids.append(str(result[0]))

    if front_ids is None or len(front_ids)==0:
        return None

    front_id_str = ",".join(front_ids)
    sql = f"""select front.front_card_content, 
                   back.back_card_content,
                   front.description,
                   rel.description
            from server_cardrelation as rel,
                          server_backcard as back,
                          server_frontcard as front
            where
                rel.back_id =back.back_id
                and rel.front_id=front.front_id
                and front.front_id in ({front_id_str})"""

    recite_content = []
    db_results = sqlite_db.query(sql)
    for db_result in db_results:
        card = {}
        # 正面
        card['front_card_content'] = db_result[0]+" "+db_result[1]
        # 背面
        card['back_card_content'] = db_result[2]+" "+db_result[3]

        # # 句子
        # card['front_card_content'] = db_result[0]
        # # 单词
        # card['back_card_content'] = db_result[1]
        # # 句子的解释
        # card['front_description'] = db_result[2]
        # # 单词在句子中意思
        # card['rel_description'] = db_result[3]
        recite_content.append(card)
    return recite_content