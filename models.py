# -*- coding: utf-8 -*-
from uuid import NAMESPACE_DNS
from sqlalchemy import Integer, Column, String, create_engine, func, BigInteger, Float, DateTime, SmallInteger, DECIMAL, TEXT
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import time, os


def to_dict(self):
    return {c.name: getattr(self, c.name, None) for c in self.__table__.columns}


# 创建对象的基类:
Base = declarative_base()
Base.to_dict = to_dict

# 初始化数据库连接:
ENGINELocal = create_engine(
    #//<username>:<password>@<DATABASE_PATH / IPADDRESS:<PORT(3306)>/<DATABASE_NAME>?<UTF-CODE>>
    'mysql+pymysql://vspnjovi:Pubgm2021@rm-uf6f326265lft8bwrdo.mysql.rds.aliyuncs.com:3306/acl_cs_2025?charset=utf8',
    #'mysql+pymysql://root:vspo2024@127.0.0.1:3306/test?charset=utf8',
    max_overflow=200,
    pool_size=100,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True,
    echo=False,
    isolation_level="READ UNCOMMITTED",
    # echo=True,
)

class GameList(Base):
    __tablename__ = 'game_list'

    match_code = Column(String(255), primary_key=True, comment="每场比赛的唯一标识")
    game_num = Column(Integer, nullable=False, unique=True, comment="本赛季第几场比赛")
    match_week = Column(Integer, nullable=False, comment="比赛周")
    match_day = Column(Integer, nullable=False, comment="比赛周中的比赛日")
    match_num = Column(Integer, nullable=False, comment="比赛日的第几场比赛")
    type = Column(Integer, nullable=False, comment="0代表bo1, 1代表bo3")
    series = Column(Integer, nullable=False, unique=True, comment="系列赛，每个bo1和bo3均代表一个系列赛")
    create_time = Column(DateTime, nullable=False, server_default=func.now(), comment="创建时间，默认当前时间")
    update_time = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间，默认当前时间")
    description = Column(String(255), comment="第x周第x日第x场第x局")
    team1 = Column(String(255))
    team2 = Column(String(255))
    
class PlayerList(Base):
    __tablename__ = 'player_list'

    steam_id = Column(String(255), primary_key=True, comment="游戏内id")
    player_name = Column(String(255), nullable=False, unique=True, comment="玩家名称")
    create_time = Column(DateTime, nullable=False, server_default=func.now(), comment="创建时间，默认当前时间")
    update_time = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间，默认当前时间")

class DataGame(Base):
    __tablename__ = 'data_game'

    match_code = Column(String(255), primary_key=True, comment="每场比赛的唯一标识")
    player_name = Column(String(255), primary_key=True, comment="玩家名称")
    kills = Column(Integer, nullable=False, comment="击杀数")
    headshotratio = Column(DECIMAL(5,2), nullable=False, comment="爆头率")
    deaths = Column(Integer, nullable=False, comment="死亡数")
    assists = Column(Integer, nullable=False, comment="助攻数")
    adr = Column(Integer, nullable=False, comment="每回合均伤")
    firstkill = Column(Integer, nullable=False, comment="首杀数")
    firstdeath = Column(Integer, nullable=False, comment="首死数")
    sniperkills = Column(Integer, nullable=False, comment="狙杀数")
    muitikills = Column(Integer, nullable=False, comment="多杀数")
    utilitydmg = Column(Integer, nullable=False, comment="道具伤害")
    kast = Column(DECIMAL(5,2), nullable=False, comment="KAST（存活、爆破、助攻、交易）")
    rating = Column(DECIMAL(5,2), nullable=False, comment="选手评分")
    create_time = Column(DateTime, nullable=False, server_default=func.now(), comment="创建时间，默认当前时间")
    update_time = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间，默认当前时间")

Base.metadata.create_all(ENGINELocal)