from flask import Flask, jsonify, request
from gsi import server
from datetime import datetime
import global_data
import time
import threading
import json
import requests
import os
from flask_cors import CORS
from sqlalchemy import and_

import xml.etree.ElementTree as ET
from decimal import Decimal
from models import *

app = Flask(__name__)
# 允许所有域名进行跨域访问
CORS(app)

previous_bomb_state = -1
current_bomb_state = -1
isFirstPlanted = True
is_initalize = False
check_current_round = 0
round_wins_count = 0
flag = 0
mvp_player = ""

# app.json.ensure_ascii = False # 解决中文乱码问题

Session = sessionmaker(bind=ENGINELocal, autocommit=False)
session = Session()

# 读取赛前预录选手信息，包括选手名，战队名和舞台位置
player_info_json = "player_info.json"
with open(player_info_json, "r", encoding="utf-8") as f:
    player_info = json.load(f)

# 获取简称
for key, value in player_info["player"].items():
    if value["player_seat"] == 1:
        left_team = value["team_name"]
    elif value["player_seat"] == 6:
        right_team = value["team_name"]

# 获取全称
left_team_long = player_info["teams"]["left"]
right_team_long = player_info["teams"]["right"]

global_json = {}


@app.route("/scores")
def scores():
    # global left_team, right_team
    ###测试
    # res = {'left': 0, 'right': '0'}
    # res = {'left': 8, 'right': 7, 'left_team': left_team_long, 'right_team': right_team_long}
    # return jsonify({"msg": "请求成功", "data": res})
    global global_json
    try:
        score_data_ct = global_json["map"]["team_ct"]
        score_data_t = global_json["map"]["team_t"]
        # left_team = player_info['teams']['left']
        # right_team = player_info['teams']['right']
        score_data = {
            score_data_ct["name"].strip(): score_data_ct["score"],
            score_data_t["name"].strip(): score_data_t["score"],
        }
        res = {
            "left": score_data[left_team_long],
            "right": score_data[right_team_long],
            "left_team": left_team_long,
            "right_team": right_team_long,
        }
        return jsonify({"msg": "请求成功", "data": res})

    except Exception as e:
        print(f"发生错误：{e}")
        return jsonify({"msg": "内部异常...", "data": {}})


def parse_scoreboard():
    global global_json
    res = {}
    res["left_team"], res["right_team"] = [], []
    try:
        # 获取本局结算数据
        with open("gsi_data.json", "r", encoding="utf-8") as file:
            all_players_data = json.load(file)
        global_json = all_players_data
        # 获取所有回合adr_json
        folder_path = "./adr_json"
        all_adr_json = []
        for adr_file in os.listdir(folder_path):
            file_path = os.path.join(folder_path, adr_file)
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                all_adr_json.append(data)
        # print('all_adr_json', all_adr_json)
        for key, player_data in all_players_data["allplayers"].items():
            # 取到选手预录信息
            this_player_info = player_info["player"][str(key)]
            # 选手本场比赛数据
            this_player_data = player_data["match_stats"]
            # 判断选手是否存活
            # is_dead = 0 if player_data["state"]["health"]>0 else 1
            player_adr = 0
            matches_number = len(all_adr_json)
            for player in all_adr_json:
                player_adr += player[str(key)]
            if this_player_info["team_name"].strip() == left_team:
                res["left_team"].append(
                    {
                        "player_name": this_player_info["player_name"],
                        "team_name": this_player_info["team_name"],
                        "seat": this_player_info["player_seat"],
                        "K": this_player_data["kills"],
                        "D": this_player_data["deaths"],
                        "A": this_player_data["assists"],
                        "KD": str(this_player_data["kills"])
                        + "/"
                        + str(this_player_data["deaths"]),
                        "ADR": int(player_adr / matches_number),
                        # 'is_dead': is_dead
                    }
                )
            else:
                res["right_team"].append(
                    {
                        "player_name": this_player_info["player_name"],
                        "team_name": this_player_info["team_name"],
                        "seat": this_player_info["player_seat"],
                        "K": this_player_data["kills"],
                        "D": this_player_data["deaths"],
                        "A": this_player_data["assists"],
                        "KD": str(this_player_data["kills"])
                        + "/"
                        + str(this_player_data["deaths"]),
                        "ADR": int(player_adr / matches_number),
                        # 'is_dead': is_dead
                    }
                )
        res["left_team"].sort(key=lambda a: a["ADR"], reverse=True)
        res["right_team"].sort(key=lambda a: a["ADR"], reverse=True)
        # print("---------------------------------scoreboard--------------------", res)
        return res

    except Exception as e:
        print(f"发生错误：{e}")
        print(e.__traceback__.tb_lineno)
        return {}


@app.route("/scoreboard")
def scoreboard():
    res = parse_scoreboard()
    return jsonify({"msg": "请求成功", "data": res})


# 响应mvp页面请求
@app.route("/player_list")
def player_list():
    players = []
    for player in parse_scoreboard()["left_team"]:
        players.append(player["player_name"])
    for player in parse_scoreboard()["right_team"]:
        players.append(player["player_name"])
    print(players)
    return jsonify({"message": "选手列表获取成功！", "data": players})


# 修改mvp全局变量
@app.route("/setMvp", methods=["POST"])
def setMvp():
    global mvp_player
    mvp = request.form.get("mvp")
    mvp_player = mvp
    print(f"已设置本局mvp为:{mvp_player}")
    return "", 204


# mvp赛后接口
@app.route("/mvp")
def mvp():
    # board = parse_scoreboard()
    # for player in board["left_team"]:
    #     if player["player_name"] == mvp_player:
    #         return jsonify({"msg": "请求成功", "data": player})

    # for player in board["right_team"]:
    #     if player["player_name"] == mvp_player:
    #         return jsonify({"msg": "请求成功", "data": player})

    Session = sessionmaker(bind=ENGINELocal, autocommit=False)
    session = Session()
    try:
        match_code = (
            session.query(GameList.match_code)
            .order_by(GameList.create_time.desc())
            .first()[0]
        )
        mvp = (
            session.query(DataGame)
            .filter(DataGame.match_code == match_code)
            .order_by(DataGame.rating.desc())
            .first()
        )
        mvp_info = {
            "player_name": mvp.player_name,
            "kills": mvp.kills,
            "deaths": mvp.deaths,
            "assists": mvp.assists,
            "headshotratio": float(mvp.headshotratio),
            "adr": mvp.adr,
            "firstkill": mvp.firstkill,
            "firstdeath": mvp.firstdeath,
            "sniperkills": mvp.sniperkills,
            "muitikills": mvp.muitikills,
            "utilitydmg": mvp.utilitydmg,
            "kast": float(mvp.kast),
            "rating": float(mvp.rating),
        }
        print(mvp.player_name)
        return jsonify({"msg": "请求成功", "data": mvp_info})
    except Exception as e:
        print(f"发生异常：{e}, 在第{e.__traceback__.tb_lineno}行")
        return jsonify(
            {"msg": "请求失败", "data": {}, "description": "未查询到匹配的选手！"}
        )


# 手选mvp接口
app.route("/selectedMVP")
def selectedMVP():
    try:
        match_code = (
            session.query(GameList.match_code)
            .order_by(GameList.create_time.desc())
            .first()[0]
        )
        mvp = (
            session.query(DataGame)
            .filter(
                and_(
                    DataGame.player_name == mvp_player,
                    DataGame.match_code == match_code,
                )
            )
            .order_by(DataGame.rating.desc())
            .first()
        )
        mvp_info = {
            "player_name": mvp.player_name,
            "kills": mvp.kills,
            "deaths": mvp.deaths,
            "assists": mvp.assists,
            "headshotratio": float(mvp.headshotratio),
            "adr": mvp.adr,
            "firstkill": mvp.firstkill,
            "firstdeath": mvp.firstdeath,
            "sniperkills": mvp.sniperkills,
            "muitikills": mvp.muitikills,
            "utilitydmg": mvp.utilitydmg,
            "kast": float(mvp.kast),
            "rating": float(mvp.rating),
        }
        print(mvp.player_name)
        return jsonify({"msg": "请求成功", "data": mvp_info})
    except Exception as e:
        print(f"发生异常：{e}, 在第{e.__traceback__.tb_lineno}行")
        return jsonify(
            {"msg": "请求失败", "data": {}, "description": "未查询到匹配的选手！"}
        )


# 存赛后数据
@app.route("/saveMatchData", methods=["POST"])
def saveMatchData():
    Session = sessionmaker(bind=ENGINELocal, autocommit=False)
    session = Session()

    # 从请求参数中获取 match_code，match_week, match_day, match_num, type, series
    match_code = request.form.get("match_code")

    if not match_code:
        return jsonify({"error": "缺少 match_code 参数"}), 400

    # 拼接访问的 URL
    url = f"https://mega-tpa.5eplaycdn.com/xml/bracket/tournament/match_xml?match_code={match_code}"

    try:
        response = requests.get(url, proxies={"http": None, "https": None})
        response.raise_for_status()
    except Exception as e:
        return jsonify({"error": f"请求数据失败：{str(e)}"}), 500

    # 解析 XML
    try:
        root = ET.fromstring(response.content)
    except ET.ParseError as e:
        return jsonify({"error": f"XML 解析错误：{str(e)}"}), 500

    # 检查 error 节点
    error_node = root.find("error")
    if error_node is None or error_node.text != "0":
        return jsonify({"error": "XML 数据返回错误"}), 400

    data_node = root.find("data")
    if data_node is None:
        return jsonify({"error": "未找到数据节点"}), 400

    # 遍历每个 <item> 节点，解析数据并保存到数据库
    for item in data_node.findall("item"):
        try:
            # 获取昵称作为玩家名称（也可以使用steamid等其它字段，按实际需求处理）
            nickname = item.find("nickname").text.strip()
            kills = int(item.find("kills").text)

            # headshotratio 带有百分号，需要去除后转换为 Decimal
            headshot_str = item.find("headshotratio").text.strip().replace("%", "")
            headshotratio = Decimal(headshot_str)

            deaths = int(item.find("deaths").text)
            assists = int(item.find("assists").text)
            # adr 字段在 XML 中可能是小数，但数据库定义为 Integer，根据需要可以四舍五入或取整
            adr_value = float(item.find("adr").text)
            adr = int(round(adr_value))

            firstkill = int(item.find("firstkill").text)
            firstdeath = int(item.find("firstdeath").text)
            sniperkills = int(item.find("sniperkills").text)
            muitikills = int(item.find("muitikills").text)
            utilitydmg = int(item.find("utilitydmg").text)

            # kast 带百分号
            kast_str = item.find("kast").text.strip().replace("%", "")
            kast = Decimal(kast_str)

            rating = Decimal(item.find("rating").text)
        except Exception as e:
            # 如果某个节点解析出错，则跳过该项或记录日志
            print(e)
            continue

        # 创建或更新 DataGame 记录（由于主键是 match_code 和 player_name 的组合）
        data_game = DataGame(
            match_code=match_code,
            player_name=nickname,
            kills=kills,
            headshotratio=headshotratio,
            deaths=deaths,
            assists=assists,
            adr=adr,
            firstkill=firstkill,
            firstdeath=firstdeath,
            sniperkills=sniperkills,
            muitikills=muitikills,
            utilitydmg=utilitydmg,
            kast=kast,
            rating=rating,
        )
        # 使用 merge 可在记录已存在时进行更新，否则插入新记录
        session.merge(data_game)

    # 记录本场比赛
    match_week = request.form.get("match_week")
    match_day = request.form.get("match_day")
    match_num = request.form.get("match_num")
    type = request.form.get("type")
    series = request.form.get("series")
    description = request.form.get("description")
    team1 = request.form.get("team1")
    team2 = request.form.get("team2")

    must_params = [match_week, match_day, match_num, type, series, team1, team2]

    if any(p == "" or p is None for p in must_params):
        return jsonify({"error": "缺少必需参数"}), 400

    game = GameList(
        match_code=match_code,
        match_week=match_week,
        match_day=match_day,
        match_num=match_num,
        type=type,
        series=series,
        description=description,
        team1=team1,
        team2=team2,
    )
    session.merge(game)

    try:
        session.commit()
    except Exception as e:
        session.rollback()
        return jsonify({"error": f"数据库保存错误：{str(e)}"}), 500

    return jsonify({"message": "数据保存成功"}), 200


# 动态显示队名
@app.route("/teamNames")
def get_team_names():
    team1 = parse_scoreboard()["left_team"][0]["team_name"]
    team2 = parse_scoreboard()["right_team"][0]["team_name"]
    teams = {"team1": team1, "team2": team2}
    return jsonify({"message": "获取队名成功！", "data": teams})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=1111, debug=False)
