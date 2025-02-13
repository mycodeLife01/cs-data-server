from flask import Flask, jsonify
from gsi import server
from datetime import datetime
import global_data
import time
import threading
import json
import requests
import os

app = Flask(__name__)

previous_bomb_state = -1
current_bomb_state = -1
isFirstPlanted = True
is_initalize = False
check_current_round = 0
round_wins_count = 0
flag = 0
c4_planted_url = "http://192.168.15.235:8000/api/location/2/0/1/press"
c4_defused_url = "http://192.168.15.235:8000/api/location/2/1/1/press"
c4_exploded_url = "http://192.168.15.235:8000/api/location/2/2/1/press"
c4_all_off = "http://192.168.15.235:8000/api/location/2/0/2/press"

left_win = "http://192.168.15.235:8000/api/location/2/0/3/press"
right_win = "http://192.168.15.235:8000/api/location/2/1/3/press"

phase_off = ["timeout_ct", "timeout_t", "paused", "freezetime"]
C4_OFF = False

# 读取赛前预录选手信息，包括选手名，战队名和舞台位置
player_info_json = "player_info.json"
with open(player_info_json, "r", encoding="utf-8") as f:
    player_info = json.load(f)

# 获取全称
left_team = player_info["teams"]["left"]
right_team = player_info["teams"]["right"]


def initalizeRound():
    global round_wins_count, isFirstPlanted, previous_bomb_state, is_initalize, current_bomb_state
    if not is_initalize:
        round_wins_count = (
            global_data.data["map"]["round"]
            if "round_wins" in global_data.data["map"]
            else 0
        )
        previous_bomb_state = (
            global_data.bomb_state_map.get(global_data.data["bomb"]["state"])
            if "bomb" in global_data.data
            else -1
        )
        global_data.bomb_state = previous_bomb_state
        # print('previous_bomb_state', previous_bomb_state)
        is_initalize = True


# checkGlobalData:用于刷新全局
def checkGlobalData():
    global isFirstPlanted, round_wins_count, left_team, right_team
    current_round = global_data.data["map"]["round"]
    # 输出bomb状态，在当前回合内判断，若current_round!=global_data.round，则更新current_round后再取bomb状态
    if current_round == global_data.round:
        # 有时候bomb里取不到state，需要从round取
        if "bomb" in global_data.data:
            bomb_state_str = global_data.data["bomb"]["state"]
        elif "round" in global_data.data:
            bomb_state_str = global_data.data["round"]["bomb"]
        else:
            # 若都没有，打印当前全部数据检查
            # print(global_data.data)
            pass
        # 更新全局bomb状态
        global_data.bomb_state = global_data.bomb_state_map.get(bomb_state_str)
    else:
        global_data.round = current_round
        isFirstPlanted = True
        print("回合更新，重置了一次!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    # 输出队伍胜利，根据round_wins长度增加触发
    if "round_wins" in global_data.data["map"]:
        round_wins = global_data.data["map"]["round_wins"]
    else:
        # 第一回合没有roundwins
        round_wins = {}

    team_t = global_data.data["map"]["team_t"]["name"]
    team_ct = global_data.data["map"]["team_ct"]["name"]
    current_round_wins_count = len(round_wins)

    if current_round_wins_count != round_wins_count and is_initalize:
        latest_winner = list(round_wins.values())[-1]
        if latest_winner[0] == "t":
            if team_t == left_team:
                print(f"Team{team_t} won!!! Left")
                # requests.post(left_win)
            else:
                print(f"Team{team_t} won!!! Right")
                # requests.post(right_win)
        else:
            if team_ct == left_team:
                print(f"Team{team_ct} won!!! Left")
                # requests.post(left_win)
            else:
                print(f"Team{team_ct} won!!! Right")
                # requests.post(right_win)
        round_wins_count = current_round_wins_count


def sendEventMsg():
    global previous_bomb_state, isFirstPlanted, current_bomb_state, C4_OFF
    phase = global_data.data["round"]["phase"]
    if is_initalize:
        bomb_state = global_data.bomb_state
        # print(bomb_state)
        # 判断炸弹状态是否改变，无改变不打印
        current_bomb_state = bomb_state
    if previous_bomb_state != current_bomb_state:
        # 只有phase在Live时，埋包才有必要发送请求
        if bomb_state == 1 and phase == "live" and isFirstPlanted:
            # requests.post(c4_planted_url)
            print(global_data.bomb_state_msg[bomb_state])

            isFirstPlanted = False
        # 只要包爆炸了或者被拆了，都需要发送请求
        # 拆
        elif bomb_state == 4:
            # requests.post(c4_defused_url)
            print(global_data.bomb_state_msg[bomb_state])
        # 炸
        elif bomb_state == 2:
            # requests.post(c4_exploded_url)
            print(global_data.bomb_state_msg[bomb_state])
        # 其他情况都不发送请求

        previous_bomb_state = current_bomb_state
    if global_data.data["phase_countdowns"]["phase"] in phase_off and not C4_OFF:
        # C4 ALL OFF
        # requests.post(c4_all_off)
        C4_OFF = True
        print("C4 ALL OFF!!!!!!!!!!")
    elif global_data.data["phase_countdowns"]["phase"] == 'paused':
        print('播放暂停音乐')
    elif global_data.data["phase_countdowns"]["phase"] == "live":
        C4_OFF = False


def save_round_data():
    # 用于判断游戏是否结束
    global flag
    # current_round = global_data.data['map']['round']
    # 在一回合结束后导出本局json数据
    if global_data.data["phase_countdowns"]["phase"] == "over":
        current_round = global_data.data["map"]["round"]
        # 储存本回合adr json数据
        adr_data = {}
        for player_id, player_data in global_data.data["allplayers"].items():
            adr_data[player_id] = player_data["state"]["round_totaldmg"]
        folder_path = "./adr_json"
        round_data = os.path.join(folder_path, f"round_{current_round}_data")
        # print('adr_data', adr_data)
        with open(round_data, "w", encoding="utf-8") as file:
            json.dump(adr_data, file, ensure_ascii=False, indent=4)
    # 在游戏结束时，储存最后一回合的json数据
    elif global_data.data["map"]["phase"] == "gameover" and flag == 0:
        current_round = global_data.data["map"]["round"]
        # 储存本回合adr json数据
        adr_data = {}
        for player_id, player_data in global_data.data["allplayers"].items():
            adr_data[player_id] = player_data["state"]["round_totaldmg"]
        folder_path = "./adr_json"
        round_data = os.path.join(folder_path, f"round_{current_round}_data")
        # print('adr_data', adr_data)
        with open(round_data, "w", encoding="utf-8") as file:
            json.dump(adr_data, file, ensure_ascii=False, indent=4)
        flag += 1


def backgroundProcess():
    while True:
        try:
            time = datetime.now()
            checkGlobalData()
            # sendEventMsg()
            save_round_data()
        except Exception as e:
            with open("error.txt", "a", encoding="utf-8") as errorfile:
                errorfile.write(str(e) + str(time) + "\n")


@app.route("/allPlayerState")
def allPlayerState():
    res = []
    try:
        all_players_data = global_data.data["allplayers"]
        for key, player_data in all_players_data.items():
            # 取到选手预录信息
            this_player_info = player_info["player"][str(key)]
            # 选手本场比赛数据
            this_player_data = player_data["match_stats"]
            # 判断选手是否存活
            is_dead = 0 if player_data["state"]["health"] > 0 else 1
            res.append(
                {
                    "player_name": this_player_info["player_name"],
                    "team_name": this_player_info["team_name"],
                    "seat": this_player_info["player_seat"],
                    "K": this_player_data["kills"],
                    "D": this_player_data["deaths"],
                    "A": this_player_data["assists"],
                    "KDA": str(this_player_data["kills"])
                    + "/"
                    + str(this_player_data["deaths"])
                    + "/"
                    + str(this_player_data["assists"]),
                    "is_dead": is_dead,
                }
            )
        res.sort(key=lambda a: a["seat"])
        return jsonify({"msg": "succeed", "data": res})
    except Exception as e:
        print(f"发生错误：{e}")
        return jsonify({"msg": "Error...", "data": []})


# 目前ob的选手数据
@app.route("/observedPlayer")
def observedPlayer():
    res = {}
    try:
        data = global_data.data["player"]
        player_name = data["name"]
        allplayers = allPlayerState()["data"]
        # for player in allplayers:
        #     if allplayers[player]['name'] == player_name:
        #         data['adr'] = adr[player]
        res = data
        return jsonify({"msg": "请求成功", "data": res})
    except Exception as e:
        print(f"发生错误：{e}")
        return jsonify({"msg": "内部异常...", "data": {}})


# 选手坐标
@app.route("/positions")
def positions():
    res = {}
    try:
        data = allPlayerState()["data"]
        for player in data:
            position = data[player]["position"]
            res[player] = position
        return jsonify({"msg": "请求成功", "data": res})
    except Exception as e:
        print(f"发生错误：{e}")
        return jsonify({"msg": "内部异常...", "data": {}})


@app.route("/scores")
def scores():
    # global left_team, right_team
    # res = {'left': 0, 'right': '0'}
    # res = {'left': 8, 'right': 7}
    try:
        score_data_ct = global_data.data["map"]["team_ct"]
        score_data_t = global_data.data["map"]["team_t"]
        # left_team = player_info['teams']['left']
        # right_team = player_info['teams']['right']
        score_data = {
            score_data_ct["name"].strip(): score_data_ct["score"],
            score_data_t["name"].strip(): score_data_t["score"],
        }
        res = {'left': score_data[left_team], 'right': score_data[right_team], 'left_team': left_team, 'right_team': right_team}
        return jsonify({"msg": "请求成功", "data": res})

    except Exception as e:
        print(f"发生错误：{e}")
        return jsonify({"msg": "内部异常...", "data": {}})


@app.route("/countdown")
def countdown():
    res = ""
    try:
        res = global_data.data["phase_countdowns"]["phase_ends_in"]
        return jsonify({"msg": "请求成功", "data": res})
    except Exception as e:
        print(f"发生错误：{e}")
        return jsonify({"msg": "内部异常...", "data": {}})


@app.route("/scoreboard")
def scoreboard():
    res = {}
    res["left_team"], res["right_team"] = [], []
    try:
        # 获取本局结算数据
        with open("gsi_data.json", "r", encoding="utf-8") as file:
            all_players_data = json.load(file)
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
            if this_player_info["team_name"] == left_team:
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

        return jsonify({"msg": "succeed", "data": res})

    except Exception as e:
        print(f"发生错误：{e}")
        print(e.__traceback__.tb_lineno)
        return jsonify({"msg": "内部异常...", "data": {}})


if __name__ == "__main__":
    myServer = server.GSIServer(("127.0.0.1", 3000), "vspo")
    myServer.start_server()

    initalizeRound()
    # 初始化adr
    # adr = {}
    # for i in range(1,11):
    #     adr[i] = 0
    thread = threading.Thread(target=backgroundProcess)
    thread.daemon = True
    thread.start()
    app.run(host="0.0.0.0", port=1234, debug=False)
