import sqlite3
from datetime import datetime

def merge_frontcard():

    # 打开两个数据库的连接
    db_win = sqlite3.connect('db_win.sqlite3')
    db_mac = sqlite3.connect('db_mac.sqlite3')

    # 创建游标对象
    cursor_win = db_win.cursor()
    cursor_mac = db_mac.cursor()

    # 获取db_mac中的所有FrontCard数据
    cursor_mac.execute("SELECT * FROM server_frontcard;")
    db_mac_data = cursor_mac.fetchall()

    # 获取db_win中的所有FrontCard数据
    cursor_win.execute("SELECT front_card_content, update_time FROM server_frontcard;")
    db_win_data = cursor_win.fetchall()

    # 将db_win中的数据按front_card_content组织成字典，方便查找
    db_win_dict = {row[0]: row[1] for row in db_win_data}

    # 遍历db_mac中的数据
    for row in db_mac_data:
        front_card_content = row[0]
        update_time = row[3]

        # 检查db_win中是否有相同的front_card_content
        if front_card_content not in db_win_dict:
            cursor_win.execute("""
                INSERT INTO server_frontcard (
                    front_card_content, description, create_time, update_time, repeat_num, next_study_time,
                    content_type, start_recite_time_point
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (row[0], row[1], row[2], row[3], row[4], row[5], row[7], row[8])) # 插入除了front_id外的所有字段
        else:
            # db_win中已有数据，比较update_time
            db_win_update_time = db_win_dict[front_card_content]
            if update_time > db_win_update_time:
                # 如果db_mac中的update_time更新，更新db_win中的记录
                cursor_win.execute("""
                    UPDATE server_frontcard
                    SET front_card_content = ?, description = ?,create_time = ?,update_time = ?,repeat_num = ?,next_study_time = ?,
                     content_type = ?, start_recite_time_point = ?
                    WHERE front_card_content = ?
                """, (row[0], row[1], row[2], row[3], row[4], row[5], row[7], row[8]) + (front_card_content,))

    # 提交更改到db_win
    db_win.commit()

    # 关闭数据库连接
    db_win.close()
    db_mac.close()

    print("FrontCard表合并完成！")


def merge_backcard():
    # 打开两个数据库的连接
    db_win = sqlite3.connect('db_win.sqlite3')
    db_mac = sqlite3.connect('db_mac.sqlite3')

    # 创建游标对象
    cursor_win = db_win.cursor()
    cursor_mac = db_mac.cursor()

    # 获取db_mac中的所有BackCard数据
    cursor_mac.execute("SELECT * FROM server_backcard;")
    db_mac_data = cursor_mac.fetchall()

    # 获取db_win中的所有BackCard数据
    cursor_win.execute("SELECT back_card_content, update_time FROM server_backcard;")
    db_win_data = cursor_win.fetchall()

    # 将db_win中的数据按back_card_content组织成字典，方便查找
    db_win_dict = {row[0]: row[1] for row in db_win_data}

    # 遍历db_mac中的数据
    for row in db_mac_data:
        back_card_content = row[0]  # 假设back_card_content是第2列
        update_time = row[3]  # 假设update_time是第7列

        # 检查db_win中是否有相同的back_card_content
        if back_card_content not in db_win_dict:
            # db_win中没有该条数据，直接插入
            cursor_win.execute("""
                INSERT INTO server_backcard (
                    back_card_content,description, create_time, update_time,repeat_num,next_study_time,content_type, 
                    start_recite_time_point
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (row[0], row[1], row[2], row[3], row[4], row[5], row[7], row[8]))  # 插入除了back_id外的所有字段
        else:
            # db_win中已有数据，比较update_time
            db_win_update_time = db_win_dict[back_card_content]
            if update_time > db_win_update_time:
                # 如果db_mac中的update_time更新，更新db_win中的记录
                cursor_win.execute("""
                    UPDATE server_backcard
                    SET back_card_content = ?,description = ?, create_time = ?, update_time = ?,
                    repeat_num = ?,next_study_time = ?,content_type = ?,  start_recite_time_point = ?
                    WHERE back_card_content = ?
                """, (row[0], row[1], row[2], row[3], row[4], row[5], row[7], row[8]) + (back_card_content,))

    # 提交更改到db_win
    db_win.commit()

    # 关闭数据库连接
    db_win.close()
    db_mac.close()

    print("BackCard表合并完成！")


def merge_relation():

    # 打开两个数据库的连接
    db_win = sqlite3.connect('db_win.sqlite3')
    db_mac = sqlite3.connect('db_mac.sqlite3')

    # 创建游标对象
    cursor_win = db_win.cursor()
    cursor_mac = db_mac.cursor()

    # 获取db_mac中的所有CardRelation数据
    cursor_mac.execute("""
        SELECT front_card_content, back_card_content, server_cardrelation.description
        FROM server_cardrelation
        JOIN server_frontcard ON server_cardrelation.front_id = server_frontcard.front_id
        JOIN server_backcard ON server_cardrelation.back_id = server_backcard.back_id
    """)
    db_mac_data = cursor_mac.fetchall()

    # 遍历db_mac中的数据
    for row in db_mac_data:
        front_card_content = row[0]  # front_card_content
        back_card_content = row[1]  # back_card_content
        description = row[2]  # description

        # 查询db_win中是否存在相同的front_card_content和back_card_content的组合
        cursor_win.execute("""
            SELECT 1
            FROM server_cardrelation cr
            JOIN server_frontcard fc ON cr.front_id = fc.front_id
            JOIN server_backcard bc ON cr.back_id = bc.back_id
            WHERE fc.front_card_content = ? AND bc.back_card_content = ?
            LIMIT 1
        """, (front_card_content, back_card_content))

        existing_relation = cursor_win.fetchone()

        if not existing_relation:
            # 如果没有找到组合，插入新的关系
            cursor_win.execute("""
                INSERT INTO server_cardrelation (front_id, back_id,create_time,description)
                SELECT fc.front_id, bc.back_id, fc.create_time, ?
                FROM server_frontcard fc, server_backcard bc
                WHERE fc.front_card_content = ? AND bc.back_card_content = ?
            """, (description, front_card_content, back_card_content))

    # 提交更改到db_win
    db_win.commit()

    # 关闭数据库连接
    db_win.close()
    db_mac.close()

    print("CardRelation表合并完成！")

if __name__ == '__main__':
    # merge_frontcard()
    merge_backcard()
    merge_relation()