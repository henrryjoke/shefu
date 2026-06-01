#!/usr/bin/env python3
"""
起卦统一模块 —— 大衍筮法 / 梅花易数 / 六爻纳甲
纯 Python 标准库，零外部依赖。
合并自 qigua_dayan.py / qigua_meihua.py / qigua_liuyao.py，
消除三处常量重复，统一入口 qigua(method, **kwargs)。

用法:
    python qigua.py dayan                   # 大衍筮法起卦
    python qigua.py meihua time             # 梅花时间起卦
    python qigua.py meihua number 37 28 15  # 梅花数字起卦
    python qigua.py liuyao                  # 六爻自动摇卦
    python qigua.py --json                  # 默认大衍筮法 JSON 输出
"""

import json
import os
import random
import sys
from datetime import datetime

# 自动添加脚本目录到路径，确保 import lifa 可用
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import lifa
from lifa import (BAGUA_PIC, BAGUA_WUXING, BAGUA_YAO, BAGUA_NUM,
                  XIANTIAN, YAO_POS_NAMES, WUXING_SHENGKE,
                  LIUSHEN_ORDER, LIUSHEN_START,
                  TGAN, DZHI, yao_pic, yao_to_gua, hexagram_view,
                  HEXAGRAM_UNICODE, hexagram_diagram, hexagram_yao_name)


# ═══════════════════════════════════════════════════════════════
# 运行环境检测
# ═══════════════════════════════════════════════════════════════

_COZE_MODE = os.environ.get("COZE_MODE", "").strip().lower() in ("1", "true", "yes")

# ═══════════════════════════════════════════════════════════════
# 内联数据 (Coze 兼容模式 — 无文件系统访问)
# ═══════════════════════════════════════════════════════════════

_GUACI_JSON = r'''{
  "乾为天": {"palace": "乾", "wuxing": "金", "shang": "乾", "xia": "乾", "yao": [1,1,1,1,1,1], "shi": 6, "ying": 3},
  "天风姤": {"palace": "乾", "wuxing": "金", "shang": "乾", "xia": "巽", "yao": [0,1,1,1,1,1], "shi": 1, "ying": 4},
  "天山遁": {"palace": "乾", "wuxing": "金", "shang": "乾", "xia": "艮", "yao": [0,0,1,1,1,1], "shi": 2, "ying": 5},
  "天地否": {"palace": "乾", "wuxing": "金", "shang": "乾", "xia": "坤", "yao": [0,0,0,1,1,1], "shi": 3, "ying": 6},
  "风地观": {"palace": "乾", "wuxing": "金", "shang": "巽", "xia": "坤", "yao": [0,0,0,0,1,1], "shi": 4, "ying": 1},
  "山地剥": {"palace": "乾", "wuxing": "金", "shang": "艮", "xia": "坤", "yao": [0,0,0,0,0,1], "shi": 5, "ying": 2},
  "火地晋": {"palace": "乾", "wuxing": "金", "shang": "离", "xia": "坤", "yao": [0,0,0,1,0,1], "shi": 4, "ying": 1, "type": "游魂"},
  "火天大有": {"palace": "乾", "wuxing": "金", "shang": "离", "xia": "乾", "yao": [1,1,1,1,0,1], "shi": 3, "ying": 6, "type": "归魂"},
  "坎为水": {"palace": "坎", "wuxing": "水", "shang": "坎", "xia": "坎", "yao": [0,1,0,0,1,0], "shi": 6, "ying": 3},
  "水泽节": {"palace": "坎", "wuxing": "水", "shang": "坎", "xia": "兑", "yao": [1,1,0,0,1,0], "shi": 1, "ying": 4},
  "水雷屯": {"palace": "坎", "wuxing": "水", "shang": "坎", "xia": "震", "yao": [1,0,0,0,1,0], "shi": 2, "ying": 5},
  "水火既济": {"palace": "坎", "wuxing": "水", "shang": "坎", "xia": "离", "yao": [1,0,1,0,1,0], "shi": 3, "ying": 6},
  "泽火革": {"palace": "坎", "wuxing": "水", "shang": "兑", "xia": "离", "yao": [1,0,1,1,1,0], "shi": 4, "ying": 1},
  "雷火丰": {"palace": "坎", "wuxing": "水", "shang": "震", "xia": "离", "yao": [1,0,1,1,0,0], "shi": 5, "ying": 2},
  "地火明夷": {"palace": "坎", "wuxing": "水", "shang": "坤", "xia": "离", "yao": [1,0,1,0,0,0], "shi": 4, "ying": 1, "type": "游魂"},
  "地水师": {"palace": "坎", "wuxing": "水", "shang": "坤", "xia": "坎", "yao": [0,1,0,0,0,0], "shi": 3, "ying": 6, "type": "归魂"},
  "艮为山": {"palace": "艮", "wuxing": "土", "shang": "艮", "xia": "艮", "yao": [0,0,1,0,0,1], "shi": 6, "ying": 3},
  "山火贲": {"palace": "艮", "wuxing": "土", "shang": "艮", "xia": "离", "yao": [1,0,1,0,0,1], "shi": 1, "ying": 4},
  "山天大畜": {"palace": "艮", "wuxing": "土", "shang": "艮", "xia": "乾", "yao": [1,1,1,0,0,1], "shi": 2, "ying": 5},
  "山泽损": {"palace": "艮", "wuxing": "土", "shang": "艮", "xia": "兑", "yao": [1,1,0,0,0,1], "shi": 3, "ying": 6},
  "火泽睽": {"palace": "艮", "wuxing": "土", "shang": "离", "xia": "兑", "yao": [1,1,0,1,0,1], "shi": 4, "ying": 1},
  "天泽履": {"palace": "艮", "wuxing": "土", "shang": "乾", "xia": "兑", "yao": [1,1,0,1,1,1], "shi": 5, "ying": 2},
  "风泽中孚": {"palace": "艮", "wuxing": "土", "shang": "巽", "xia": "兑", "yao": [1,1,0,0,1,1], "shi": 4, "ying": 1, "type": "游魂"},
  "风山渐": {"palace": "艮", "wuxing": "土", "shang": "巽", "xia": "艮", "yao": [0,0,1,0,1,1], "shi": 3, "ying": 6, "type": "归魂"},
  "震为雷": {"palace": "震", "wuxing": "木", "shang": "震", "xia": "震", "yao": [1,0,0,1,0,0], "shi": 6, "ying": 3},
  "雷地豫": {"palace": "震", "wuxing": "木", "shang": "震", "xia": "坤", "yao": [0,0,0,1,0,0], "shi": 1, "ying": 4},
  "雷水解": {"palace": "震", "wuxing": "木", "shang": "震", "xia": "坎", "yao": [0,1,0,1,0,0], "shi": 2, "ying": 5},
  "雷风恒": {"palace": "震", "wuxing": "木", "shang": "震", "xia": "巽", "yao": [0,1,1,1,0,0], "shi": 3, "ying": 6},
  "地风升": {"palace": "震", "wuxing": "木", "shang": "坤", "xia": "巽", "yao": [0,1,1,0,0,0], "shi": 4, "ying": 1},
  "水风井": {"palace": "震", "wuxing": "木", "shang": "坎", "xia": "巽", "yao": [0,1,1,0,1,0], "shi": 5, "ying": 2},
  "泽风大过": {"palace": "震", "wuxing": "木", "shang": "兑", "xia": "巽", "yao": [0,1,1,1,1,0], "shi": 4, "ying": 1, "type": "游魂"},
  "泽雷随": {"palace": "震", "wuxing": "木", "shang": "兑", "xia": "震", "yao": [1,0,0,1,1,0], "shi": 3, "ying": 6, "type": "归魂"},
  "巽为风": {"palace": "巽", "wuxing": "木", "shang": "巽", "xia": "巽", "yao": [0,1,1,0,1,1], "shi": 6, "ying": 3},
  "风天小畜": {"palace": "巽", "wuxing": "木", "shang": "巽", "xia": "乾", "yao": [1,1,1,0,1,1], "shi": 1, "ying": 4},
  "风火家人": {"palace": "巽", "wuxing": "木", "shang": "巽", "xia": "离", "yao": [1,0,1,0,1,1], "shi": 2, "ying": 5},
  "风雷益": {"palace": "巽", "wuxing": "木", "shang": "巽", "xia": "震", "yao": [1,0,0,0,1,1], "shi": 3, "ying": 6},
  "天雷无妄": {"palace": "巽", "wuxing": "木", "shang": "乾", "xia": "震", "yao": [1,0,0,1,1,1], "shi": 4, "ying": 1},
  "火雷噬嗑": {"palace": "巽", "wuxing": "木", "shang": "离", "xia": "震", "yao": [1,0,0,1,0,1], "shi": 5, "ying": 2},
  "山雷颐": {"palace": "巽", "wuxing": "木", "shang": "艮", "xia": "震", "yao": [1,0,0,0,0,1], "shi": 4, "ying": 1, "type": "游魂"},
  "山风蛊": {"palace": "巽", "wuxing": "木", "shang": "艮", "xia": "巽", "yao": [0,1,1,0,0,1], "shi": 3, "ying": 6, "type": "归魂"},
  "离为火": {"palace": "离", "wuxing": "火", "shang": "离", "xia": "离", "yao": [1,0,1,1,0,1], "shi": 6, "ying": 3},
  "火山旅": {"palace": "离", "wuxing": "火", "shang": "离", "xia": "艮", "yao": [0,0,1,1,0,1], "shi": 1, "ying": 4},
  "火风鼎": {"palace": "离", "wuxing": "火", "shang": "离", "xia": "巽", "yao": [0,1,1,1,0,1], "shi": 2, "ying": 5},
  "火水未济": {"palace": "离", "wuxing": "火", "shang": "离", "xia": "坎", "yao": [0,1,0,1,0,1], "shi": 3, "ying": 6},
  "山水蒙": {"palace": "离", "wuxing": "火", "shang": "艮", "xia": "坎", "yao": [0,1,0,0,0,1], "shi": 4, "ying": 1},
  "风水涣": {"palace": "离", "wuxing": "火", "shang": "巽", "xia": "坎", "yao": [0,1,0,0,1,1], "shi": 5, "ying": 2},
  "天水讼": {"palace": "离", "wuxing": "火", "shang": "乾", "xia": "坎", "yao": [0,1,0,1,1,1], "shi": 4, "ying": 1, "type": "游魂"},
  "天火同人": {"palace": "离", "wuxing": "火", "shang": "乾", "xia": "离", "yao": [1,0,1,1,1,1], "shi": 3, "ying": 6, "type": "归魂"},
  "坤为地": {"palace": "坤", "wuxing": "土", "shang": "坤", "xia": "坤", "yao": [0,0,0,0,0,0], "shi": 6, "ying": 3},
  "地雷复": {"palace": "坤", "wuxing": "土", "shang": "坤", "xia": "震", "yao": [1,0,0,0,0,0], "shi": 1, "ying": 4},
  "地泽临": {"palace": "坤", "wuxing": "土", "shang": "坤", "xia": "兑", "yao": [1,1,0,0,0,0], "shi": 2, "ying": 5},
  "地天泰": {"palace": "坤", "wuxing": "土", "shang": "坤", "xia": "乾", "yao": [1,1,1,0,0,0], "shi": 3, "ying": 6},
  "雷天大壮": {"palace": "坤", "wuxing": "土", "shang": "震", "xia": "乾", "yao": [1,1,1,1,0,0], "shi": 4, "ying": 1},
  "泽天夬": {"palace": "坤", "wuxing": "土", "shang": "兑", "xia": "乾", "yao": [1,1,1,1,1,0], "shi": 5, "ying": 2},
  "水天需": {"palace": "坤", "wuxing": "土", "shang": "坎", "xia": "乾", "yao": [1,1,1,0,1,0], "shi": 4, "ying": 1, "type": "游魂"},
  "水地比": {"palace": "坤", "wuxing": "土", "shang": "坎", "xia": "坤", "yao": [0,0,0,0,1,0], "shi": 3, "ying": 6, "type": "归魂"},
  "兑为泽": {"palace": "兑", "wuxing": "金", "shang": "兑", "xia": "兑", "yao": [1,1,0,1,1,0], "shi": 6, "ying": 3},
  "泽水困": {"palace": "兑", "wuxing": "金", "shang": "兑", "xia": "坎", "yao": [0,1,0,1,1,0], "shi": 1, "ying": 4},
  "泽地萃": {"palace": "兑", "wuxing": "金", "shang": "兑", "xia": "坤", "yao": [0,0,0,1,1,0], "shi": 2, "ying": 5},
  "泽山咸": {"palace": "兑", "wuxing": "金", "shang": "兑", "xia": "艮", "yao": [0,0,1,1,1,0], "shi": 3, "ying": 6},
  "水山蹇": {"palace": "兑", "wuxing": "金", "shang": "坎", "xia": "艮", "yao": [0,0,1,0,1,0], "shi": 4, "ying": 1},
  "地山谦": {"palace": "兑", "wuxing": "金", "shang": "坤", "xia": "艮", "yao": [0,0,1,0,0,0], "shi": 5, "ying": 2},
  "雷山小过": {"palace": "兑", "wuxing": "金", "shang": "震", "xia": "艮", "yao": [0,0,1,1,0,0], "shi": 4, "ying": 1, "type": "游魂"},
  "雷泽归妹": {"palace": "兑", "wuxing": "金", "shang": "震", "xia": "兑", "yao": [1,1,0,1,0,0], "shi": 3, "ying": 6, "type": "归魂"}
}'''

_NAJIA_JSON = r'''{
  "八纯卦纳甲": {
    "乾": {
      "内卦": [{"爻位": 1, "干支": "甲子", "天干": "甲", "地支": "子", "五行": "水"}, {"爻位": 2, "干支": "甲寅", "天干": "甲", "地支": "寅", "五行": "木"}, {"爻位": 3, "干支": "甲辰", "天干": "甲", "地支": "辰", "五行": "土"}],
      "外卦": [{"爻位": 4, "干支": "壬午", "天干": "壬", "地支": "午", "五行": "火"}, {"爻位": 5, "干支": "壬申", "天干": "壬", "地支": "申", "五行": "金"}, {"爻位": 6, "干支": "壬戌", "天干": "壬", "地支": "戌", "五行": "土"}]
    },
    "坎": {
      "内卦": [{"爻位": 1, "干支": "戊寅", "天干": "戊", "地支": "寅", "五行": "木"}, {"爻位": 2, "干支": "戊辰", "天干": "戊", "地支": "辰", "五行": "土"}, {"爻位": 3, "干支": "戊午", "天干": "戊", "地支": "午", "五行": "火"}],
      "外卦": [{"爻位": 4, "干支": "戊申", "天干": "戊", "地支": "申", "五行": "金"}, {"爻位": 5, "干支": "戊戌", "天干": "戊", "地支": "戌", "五行": "土"}, {"爻位": 6, "干支": "戊子", "天干": "戊", "地支": "子", "五行": "水"}]
    },
    "艮": {
      "内卦": [{"爻位": 1, "干支": "丙辰", "天干": "丙", "地支": "辰", "五行": "土"}, {"爻位": 2, "干支": "丙午", "天干": "丙", "地支": "午", "五行": "火"}, {"爻位": 3, "干支": "丙申", "天干": "丙", "地支": "申", "五行": "金"}],
      "外卦": [{"爻位": 4, "干支": "丙戌", "天干": "丙", "地支": "戌", "五行": "土"}, {"爻位": 5, "干支": "丙子", "天干": "丙", "地支": "子", "五行": "水"}, {"爻位": 6, "干支": "丙寅", "天干": "丙", "地支": "寅", "五行": "木"}]
    },
    "震": {
      "内卦": [{"爻位": 1, "干支": "庚子", "天干": "庚", "地支": "子", "五行": "水"}, {"爻位": 2, "干支": "庚寅", "天干": "庚", "地支": "寅", "五行": "木"}, {"爻位": 3, "干支": "庚辰", "天干": "庚", "地支": "辰", "五行": "土"}],
      "外卦": [{"爻位": 4, "干支": "庚午", "天干": "庚", "地支": "午", "五行": "火"}, {"爻位": 5, "干支": "庚申", "天干": "庚", "地支": "申", "五行": "金"}, {"爻位": 6, "干支": "庚戌", "天干": "庚", "地支": "戌", "五行": "土"}]
    },
    "巽": {
      "内卦": [{"爻位": 1, "干支": "辛丑", "天干": "辛", "地支": "丑", "五行": "土"}, {"爻位": 2, "干支": "辛亥", "天干": "辛", "地支": "亥", "五行": "水"}, {"爻位": 3, "干支": "辛酉", "天干": "辛", "地支": "酉", "五行": "金"}],
      "外卦": [{"爻位": 4, "干支": "辛未", "天干": "辛", "地支": "未", "五行": "土"}, {"爻位": 5, "干支": "辛巳", "天干": "辛", "地支": "巳", "五行": "火"}, {"爻位": 6, "干支": "辛卯", "天干": "辛", "地支": "卯", "五行": "木"}]
    },
    "离": {
      "内卦": [{"爻位": 1, "干支": "己卯", "天干": "己", "地支": "卯", "五行": "木"}, {"爻位": 2, "干支": "己丑", "天干": "己", "地支": "丑", "五行": "土"}, {"爻位": 3, "干支": "己亥", "天干": "己", "地支": "亥", "五行": "水"}],
      "外卦": [{"爻位": 4, "干支": "己酉", "天干": "己", "地支": "酉", "五行": "金"}, {"爻位": 5, "干支": "己未", "天干": "己", "地支": "未", "五行": "土"}, {"爻位": 6, "干支": "己巳", "天干": "己", "地支": "巳", "五行": "火"}]
    },
    "坤": {
      "内卦": [{"爻位": 1, "干支": "乙未", "天干": "乙", "地支": "未", "五行": "土"}, {"爻位": 2, "干支": "乙巳", "天干": "乙", "地支": "巳", "五行": "火"}, {"爻位": 3, "干支": "乙卯", "天干": "乙", "地支": "卯", "五行": "木"}],
      "外卦": [{"爻位": 4, "干支": "癸丑", "天干": "癸", "地支": "丑", "五行": "土"}, {"爻位": 5, "干支": "癸亥", "天干": "癸", "地支": "亥", "五行": "水"}, {"爻位": 6, "干支": "癸酉", "天干": "癸", "地支": "酉", "五行": "金"}]
    },
    "兑": {
      "内卦": [{"爻位": 1, "干支": "丁巳", "天干": "丁", "地支": "巳", "五行": "火"}, {"爻位": 2, "干支": "丁卯", "天干": "丁", "地支": "卯", "五行": "木"}, {"爻位": 3, "干支": "丁丑", "天干": "丁", "地支": "丑", "五行": "土"}],
      "外卦": [{"爻位": 4, "干支": "丁亥", "天干": "丁", "地支": "亥", "五行": "水"}, {"爻位": 5, "干支": "丁酉", "天干": "丁", "地支": "酉", "五行": "金"}, {"爻位": 6, "干支": "丁未", "天干": "丁", "地支": "未", "五行": "土"}]
    }
  }
}'''

# ═══════════════════════════════════════════════════════════════
# 数据文件加载 (COZE_MODE 下使用内联数据，自动回退)
# ═══════════════════════════════════════════════════════════════

DATA_DIR = os.path.join(BASE_DIR, "..", "data")

GUACI_DB = None
NAJIA_DB = None


def load_gua_db() -> dict:
    """加载 64 卦数据库。
    COZE_MODE 下直接使用内联数据。
    本地环境下优先读文件，文件不可用时回退到内联。
    """
    global GUACI_DB
    if GUACI_DB is not None:
        return GUACI_DB

    if _COZE_MODE:
        GUACI_DB = json.loads(_GUACI_JSON)
        return GUACI_DB

    path = os.path.join(DATA_DIR, "guaci_db.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            GUACI_DB = json.load(f)
    except (FileNotFoundError, IOError):
        GUACI_DB = json.loads(_GUACI_JSON)
    return GUACI_DB


def load_najia_db() -> dict:
    """加载纳甲表。COZE_MODE 下直接使用内联数据。"""
    global NAJIA_DB
    if NAJIA_DB is not None:
        return NAJIA_DB

    if _COZE_MODE:
        NAJIA_DB = json.loads(_NAJIA_JSON)
        return NAJIA_DB

    path = os.path.join(DATA_DIR, "najia_table.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            NAJIA_DB = json.load(f)
    except (FileNotFoundError, IOError):
        NAJIA_DB = json.loads(_NAJIA_JSON)
    return NAJIA_DB


# ═══════════════════════════════════════════════════════════════
# 公共查询函数
# ═══════════════════════════════════════════════════════════════

def find_gua_by_yao(yao: list, db: dict = None) -> str | None:
    """根据六爻数组查找卦名 (yao[0]=初爻, yao[5]=上爻)"""
    if db is None:
        db = load_gua_db()
    for name, info in db.items():
        if info.get("yao") == yao:
            return name
    return None


def find_gua_by_shangxia(shang: str, xia: str, db: dict = None) -> tuple:
    """根据上下卦名查找卦名和卦信息"""
    if db is None:
        db = load_gua_db()
    for name, info in db.items():
        if info["shang"] == shang and info["xia"] == xia:
            return name, info
    return None, None


def bagua_from_num(n: int, offset: int = 0) -> str:
    """数字 → 八卦 (取余数，梅花用)"""
    r = n % 8
    return XIANTIAN[r if r != 0 else 8]


def dongyao_from_num(n: int) -> int:
    """数字 → 动爻 1-6 (梅花用)"""
    r = n % 6
    return r if r != 0 else 6


# ═══════════════════════════════════════════════════════════════
# 1. 大衍筮法
# ═══════════════════════════════════════════════════════════════

def dayan_one_line(rng=None) -> tuple:
    """
    大衍筮法成爻：四营三变成一爻。
    返回 (value, yao, moving)
    - value: 6(老阴)/7(少阳)/8(少阴)/9(老阳)
    - yao: 0(阴)/1(阳)
    - moving: True(动爻)/False(静爻)
    """
    if rng is None:
        rng = random
    stalks = 49  # 大衍之数五十，其用四十有九

    for _ in range(3):  # 三变
        # 分二
        split = rng.randint(1, stalks - 1)
        left = split
        right = stalks - split
        # 挂一
        right -= 1
        # 揲四
        left_rem = left % 4 or 4
        right_rem = right % 4 or 4
        # 归奇
        stalks -= (1 + left_rem + right_rem)

    value = stalks // 4
    if value == 6:
        return value, 0, True   # 老阴 → 阴爻，动
    elif value == 7:
        return value, 1, False  # 少阳 → 阳爻，静
    elif value == 8:
        return value, 0, False  # 少阴 → 阴爻，静
    else:  # value == 9
        return value, 1, True   # 老阳 → 阳爻，动


def dayan_qigua(seed: int = None) -> dict:
    """完整大衍筮法起卦：十八变 → 六爻 → 本卦 + 变卦"""
    rng = random.Random(seed) if seed is not None else random

    lines = []
    for pos in range(1, 7):
        value, yao, moving = dayan_one_line(rng)
        lines.append({
            "pos": pos, "value": value, "yao": yao,
            "moving": moving, "changed_yao": yao if not moving else (1 - yao),
        })

    ben_yao = [l["yao"] for l in lines]
    bian_yao = [l["changed_yao"] for l in lines]
    dong_yao = [l["pos"] for l in lines if l["moving"]]

    db = load_gua_db()
    ben_gua_name = find_gua_by_yao(ben_yao, db)
    bian_gua_name = find_gua_by_yao(bian_yao, db) if dong_yao else None

    gua_info = db.get(ben_gua_name, {})
    shang_name = gua_info.get("shang", "?")
    xia_name = gua_info.get("xia", "?")

    li = lifa.now_ganzhi()

    result = {
        "method": "大衍筮法",
        "method_desc": "四营十八变·蓍草模拟",
        "lines": lines,
        "ben_gua": {
            "name": ben_gua_name,
            "yao": ben_yao,
            "shang": shang_name, "xia": xia_name,
            "wuxing": gua_info.get("wuxing", "?"),
            "shang_pic": BAGUA_PIC.get(shang_name, "?"),
            "xia_pic": BAGUA_PIC.get(xia_name, "?"),
        },
        "dong_yao": dong_yao,
        "calendar": {
            "year": li["年干支"], "month": li["月干支"], "day": li["日干支"],
            "month_zhi": li["月建"], "day_zhi": li["日支"],
        },
        "bian_gua": None,
    }

    if bian_gua_name:
        bian_info = db.get(bian_gua_name, {})
        result["bian_gua"] = {
            "name": bian_gua_name, "yao": bian_yao,
            "shang": bian_info.get("shang", "?"),
            "xia": bian_info.get("xia", "?"),
            "wuxing": bian_info.get("wuxing", "?"),
            "shang_pic": BAGUA_PIC.get(bian_info.get("shang", "?"), "?"),
            "xia_pic": BAGUA_PIC.get(bian_info.get("xia", "?"), "?"),
        }

    return result


# ═══════════════════════════════════════════════════════════════
# 2. 梅花易数
# ═══════════════════════════════════════════════════════════════

def meihua_qigua_by_time(year: int = None, month: int = None,
                          day: int = None, hour: int = None) -> tuple:
    """时间起卦 → (上卦名, 下卦名, 动爻位)"""
    now = datetime.now()
    y = year if year is not None else now.year
    m = month if month is not None else now.month
    d = day if day is not None else now.day
    h = hour if hour is not None else now.hour

    shang_sum = y + m + d
    shang_num = shang_sum % 8 or 8
    xia_sum = y + m + d + h
    xia_num = xia_sum % 8 or 8
    dy = xia_sum % 6 or 6

    return XIANTIAN[shang_num], XIANTIAN[xia_num], dy


def meihua_qigua_by_numbers(*numbers) -> tuple:
    """数字起卦 → (上卦名, 下卦名, 动爻位)"""
    nums = list(numbers)
    shang_gua = bagua_from_num(nums[0])
    xia_gua = bagua_from_num(nums[1])
    dy = dongyao_from_num(nums[2]) if len(nums) >= 3 else dongyao_from_num(nums[0] + nums[1])
    return shang_gua, xia_gua, dy


def meihua_calc_hugua(ben_yao: list) -> tuple:
    """计算互卦：二三四爻为下互，三四五爻为上互"""
    xia_hu_yao = ben_yao[1:4]   # 二三四爻
    shang_hu_yao = ben_yao[2:5]  # 三四五爻
    return yao_to_gua(shang_hu_yao), yao_to_gua(xia_hu_yao)


def meihua_calc_biangua(ben_yao: list, dongyao: int) -> tuple:
    """计算变卦：动爻阴阳翻转"""
    changed = ben_yao[:]
    changed[dongyao - 1] = 1 - changed[dongyao - 1]
    shang_name = yao_to_gua(changed[3:6])  # 四五六→上卦
    xia_name = yao_to_gua(changed[0:3])    # 一二三→下卦
    return shang_name, xia_name, changed


def meihua_calc_tiyong(ben_gua_info: dict, dongyao: int) -> tuple:
    """体用判定：动爻在体卦则用卦为对方"""
    shang = ben_gua_info["shang"]
    xia = ben_gua_info["xia"]
    if dongyao in (4, 5, 6):  # 上卦动
        return xia, shang       # 体=下卦, 用=上卦
    else:
        return shang, xia       # 体=上卦, 用=下卦


def meihua_tiyong_relation(ti: str, yong: str) -> tuple:
    """体用生克关系"""
    ti_wx = BAGUA_WUXING[ti]
    yong_wx = BAGUA_WUXING[yong]
    sk = WUXING_SHENGKE[ti_wx]
    if ti_wx == yong_wx:
        return "体用比和", "体用同气"
    elif yong_wx == sk["被生"]:
        return "用生体", "用生体，事成顺遂"
    elif yong_wx == sk["生"]:
        return "体生用", "体生用，泄气耗力"
    elif yong_wx == sk["克"]:
        return "体克用", "体克用，需主动争取"
    else:
        return "用克体", "用克体，事有阻碍"


def meihua_qigua(method: str = "time", **kwargs) -> dict:
    """梅花易数起卦主入口"""
    db = load_gua_db()

    if method == "time":
        shang_gua, xia_gua, dongyao = meihua_qigua_by_time(
            kwargs.get("year"), kwargs.get("month"),
            kwargs.get("day"), kwargs.get("hour"))
        desc = "时间起卦"
    elif method == "number":
        numbers = kwargs.get("numbers", [])
        shang_gua, xia_gua, dongyao = meihua_qigua_by_numbers(*numbers)
        desc = f"数字起卦 ({', '.join(str(n) for n in numbers)})"
    else:
        raise ValueError(f"不支持的方法: {method}")

    ben_gua_name, ben_gua_info = find_gua_by_shangxia(shang_gua, xia_gua, db)
    if ben_gua_name is None:
        return {"error": f"未找到卦: 上{shang_gua} 下{xia_gua}"}

    # 互卦
    hu_shang, hu_xia = meihua_calc_hugua(ben_gua_info["yao"])
    hu_name, hu_info = find_gua_by_shangxia(hu_shang, hu_xia, db)

    # 变卦
    bg_shang, bg_xia, bg_yao = meihua_calc_biangua(ben_gua_info["yao"], dongyao)
    bg_name, bg_info = find_gua_by_shangxia(bg_shang, bg_xia, db)

    # 体用
    ti, yong = meihua_calc_tiyong(ben_gua_info, dongyao)
    relation, relation_desc = meihua_tiyong_relation(ti, yong)

    return {
        "method": desc,
        "calendar": lifa.now_ganzhi(),
        "ben_gua": {
            "name": ben_gua_name,
            "shang": ben_gua_info["shang"], "xia": ben_gua_info["xia"],
            "wuxing": ben_gua_info["wuxing"], "yao": ben_gua_info["yao"],
            "shang_pic": BAGUA_PIC[ben_gua_info["shang"]],
            "xia_pic": BAGUA_PIC[ben_gua_info["xia"]],
        },
        "hu_gua": {
            "name": hu_name or f"上{hu_shang}下{hu_xia}",
            "shang": hu_shang, "xia": hu_xia,
            "shang_pic": BAGUA_PIC[hu_shang], "xia_pic": BAGUA_PIC[hu_xia],
        },
        "bian_gua": {
            "name": bg_name or f"上{bg_shang}下{bg_xia}",
            "shang": bg_shang, "xia": bg_xia,
            "wuxing": bg_info["wuxing"] if bg_info else "?",
            "yao": bg_yao,
            "shang_pic": BAGUA_PIC[bg_shang], "xia_pic": BAGUA_PIC[bg_xia],
        },
        "dong_yao": dongyao,
        "ti_yong": {
            "ti": ti, "ti_wuxing": BAGUA_WUXING[ti],
            "yong": yong, "yong_wuxing": BAGUA_WUXING[yong],
            "relation": relation, "relation_desc": relation_desc,
            "ti_pic": BAGUA_PIC[ti], "yong_pic": BAGUA_PIC[yong],
        },
        "hexagram_views": {
            "ben": hexagram_view(ben_gua_info["yao"], dongyao),
            "hu": hexagram_view(hu_info["yao"]) if hu_info else "N/A",
            "bian": hexagram_view(bg_yao),
        },
    }


# ═══════════════════════════════════════════════════════════════
# 3. 六爻纳甲
# ═══════════════════════════════════════════════════════════════

def liuyao_toss_coins(rng=None) -> dict:
    """模拟三枚铜钱摇卦"""
    if rng is None:
        rng = random
    coins = [rng.choice(["正", "反"]) for _ in range(3)]
    backs = sum(1 for c in coins if c == "反")

    if backs == 0:
        return {"value": "老阴", "yao": 0, "changing": True, "coins": coins, "bei": 0}
    elif backs == 1:
        return {"value": "少阳", "yao": 1, "changing": False, "coins": coins, "bei": 1}
    elif backs == 2:
        return {"value": "少阴", "yao": 0, "changing": False, "coins": coins, "bei": 2}
    else:
        return {"value": "老阳", "yao": 1, "changing": True, "coins": coins, "bei": 3}


def liuyao_toss_hexagram(rng=None) -> list:
    """摇六次得卦"""
    lines = []
    for i in range(1, 7):
        result = liuyao_toss_coins(rng)
        result["position"] = i
        lines.append(result)
    return lines


def liuyao_parse_lines(line_str: str) -> list:
    """解析手动输入的六爻铜钱结果: '正正反,反反反,...'"""
    parts = [s.strip() for s in line_str.split(",")]
    lines = []
    for s in parts:
        backs = s.count("反")
        if backs == 0:
            lines.append({"value": "老阴", "yao": 0, "changing": True,
                          "coins": list(s), "bei": 0, "position": len(lines) + 1})
        elif backs == 1:
            lines.append({"value": "少阳", "yao": 1, "changing": False,
                          "coins": list(s), "bei": 1, "position": len(lines) + 1})
        elif backs == 2:
            lines.append({"value": "少阴", "yao": 0, "changing": False,
                          "coins": list(s), "bei": 2, "position": len(lines) + 1})
        else:
            lines.append({"value": "老阳", "yao": 1, "changing": True,
                          "coins": list(s), "bei": 3, "position": len(lines) + 1})
    return lines


def liuyao_get_najia(najia_db: dict, gua_info: dict) -> list:
    """为非纯卦装纳甲：下卦取纯卦内卦纳甲，上卦取纯卦外卦纳甲"""
    xia_gua = gua_info["xia"]
    shang_gua = gua_info["shang"]
    table = najia_db["八纯卦纳甲"]
    return table[xia_gua]["内卦"] + table[shang_gua]["外卦"]


def liuyao_calc_liuqin(gua_wuxing: str, yao_dizhi_wx: str) -> str:
    """六亲判定"""
    if gua_wuxing == yao_dizhi_wx:
        return "兄弟"
    # 五行生克 (简化版：直接用 WUXING_SHENGKE 的 "生" 和 "克")
    sx = {"水": "木", "木": "火", "火": "土", "土": "金", "金": "水"}
    kx = {"水": "火", "火": "金", "金": "木", "木": "土", "土": "水"}

    if sx.get(gua_wuxing) == yao_dizhi_wx:
        return "子孙"
    if kx.get(gua_wuxing) == yao_dizhi_wx:
        return "妻财"
    if sx.get(yao_dizhi_wx) == gua_wuxing:
        return "父母"
    if kx.get(yao_dizhi_wx) == gua_wuxing:
        return "官鬼"
    return "?"


def liuyao_get_liushen(day_gan: str) -> list:
    """根据日干获取六神排列 (从初爻到上爻)"""
    start_idx = LIUSHEN_START.get(day_gan, 0)
    return [LIUSHEN_ORDER[(start_idx + i) % 6] for i in range(6)]


def liuyao_qigua(lines: list = None, seed: int = None) -> dict:
    """六爻纳甲起卦主入口"""
    db = load_gua_db()
    najia_db = load_najia_db()

    if lines is None:
        rng = random.Random(seed) if seed is not None else random
        lines = liuyao_toss_hexagram(rng)

    cal = lifa.now_ganzhi()
    day_gan = cal["日干"]
    day_zhi = cal["日支"]

    ben_yao = [line["yao"] for line in lines]
    bian_yao = []
    changing_positions = []
    for line in lines:
        if line["changing"]:
            changing_positions.append(line["position"])
            bian_yao.append(1 - line["yao"])
        else:
            bian_yao.append(line["yao"])

    ben_gua_name, ben_gua_info = find_gua_by_shangxia(
        yao_to_gua(ben_yao[3:6]), yao_to_gua(ben_yao[0:3]), db)
    bian_gua_name, bian_gua_info = find_gua_by_shangxia(
        yao_to_gua(bian_yao[3:6]), yao_to_gua(bian_yao[0:3]), db)

    if ben_gua_name is None or bian_gua_name is None:
        return {"error": f"未匹配到卦: {ben_yao}"}

    najia_lines = liuyao_get_najia(najia_db, ben_gua_info)
    liushen = liuyao_get_liushen(day_gan)
    shi_pos = ben_gua_info["shi"]
    ying_pos = ben_gua_info["ying"]

    yao_detail = []
    for i, line in enumerate(lines):
        pos = i + 1
        nj = najia_lines[i]
        dizhi_wx = nj["五行"]
        liuqin = liuyao_calc_liuqin(ben_gua_info["wuxing"], dizhi_wx)

        detail = {
            "pos": pos,
            "阴阳": "—" if line["yao"] == 1 else "- -",
            "卦画": yao_pic(line["yao"]) + (" ○" if line["changing"] and line["yao"] == 1
                                              else " ×" if line["changing"] and line["yao"] == 0
                                              else ""),
            "摇卦结果": line["value"],
            "铜钱": "".join(line["coins"]),
            "纳甲": nj["干支"], "天干": nj["天干"], "地支": nj["地支"],
            "地支五行": dizhi_wx, "六亲": liuqin,
            "六神": liushen[i],
            "世应": "世" if pos == shi_pos else "应" if pos == ying_pos else "",
            "动变": "动" if line["changing"] else "",
        }

        if (pos) in changing_positions:
            bn = liuyao_get_najia(najia_db, bian_gua_info)[i]
            detail["变爻"] = {
                "变卦": bian_gua_name,
                "变纳甲": bn["干支"], "变地支": bn["地支"],
                "变五行": bn["五行"],
                "变六亲": liuyao_calc_liuqin(ben_gua_info["wuxing"], bn["五行"]),
            }
        yao_detail.append(detail)

    return {
        "占卜时间": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "年干支": cal["年干支"],
        "月建": cal["月建"], "月干支": cal["月干支"],
        "月建五行": cal["月建五行"],
        "日干支": cal["日干支"],
        "日干": day_gan, "日支": day_zhi,
        "日建五行": cal["日建五行"],
        "本卦": {
            "name": ben_gua_name,
            "palace": ben_gua_info["palace"],
            "wuxing": ben_gua_info["wuxing"],
            "shang": ben_gua_info["shang"], "xia": ben_gua_info["xia"],
            "上卦图": BAGUA_PIC[ben_gua_info["shang"]],
            "下卦图": BAGUA_PIC[ben_gua_info["xia"]],
            "shi": shi_pos, "ying": ying_pos,
        },
        "变卦": {
            "name": bian_gua_name,
            "palace": bian_gua_info["palace"],
            "wuxing": bian_gua_info["wuxing"],
            "shang": bian_gua_info["shang"], "xia": bian_gua_info["xia"],
            "上卦图": BAGUA_PIC[bian_gua_info["shang"]],
            "下卦图": BAGUA_PIC[bian_gua_info["xia"]],
        },
        "动爻": changing_positions,
        "爻位详情": yao_detail,
    }


# ═══════════════════════════════════════════════════════════════
# 统一入口
# ═══════════════════════════════════════════════════════════════

def qigua(method: str = "dayan", **kwargs) -> dict:
    """统一起卦入口

    Args:
        method: "dayan" | "meihua" | "liuyao"
        **kwargs:
            - seed: int (dayan/liuyao 随机种子)
            - meihua_method: "time" | "number" (梅花子方法)
            - year/month/day/hour: int (梅花时间)
            - numbers: list (梅花数字)
            - lines: list (六爻手动输入，6个dict)
            - line_str: str (六爻手动输入，逗号分隔 "正正反,正反反,...")

    Returns:
        包含卦象所有信息的 dict
    """
    if method == "dayan":
        seed = kwargs.get("seed", kwargs.get("dayan_seed"))
        return dayan_qigua(seed=seed)

    elif method == "meihua":
        mh_method = kwargs.pop("meihua_method", kwargs.pop("method", "time"))
        return meihua_qigua(method=mh_method, **kwargs)

    elif method == "liuyao":
        if "line_str" in kwargs:
            lines = liuyao_parse_lines(kwargs["line_str"])
        else:
            lines = kwargs.get("lines")
        seed = kwargs.get("seed", kwargs.get("liuyao_seed"))
        return liuyao_qigua(lines=lines, seed=seed)

    else:
        return {"error": f"不支持的起卦方式: {method}，可用: dayan / meihua / liuyao"}


# ═══════════════════════════════════════════════════════════════
# 表格化汇总渲染
# ═══════════════════════════════════════════════════════════════

def hexagram_row(gua_name: str) -> str:
    """表格单行: Unicode卦符 + 卦名"""
    uc = HEXAGRAM_UNICODE.get(gua_name, "  ")
    return f"{uc} {gua_name}"


def hexagram_summary_table(ben_name: str, ben_shang: str, ben_xia: str,
                           dongyao_list: list = None,
                           bian_name: str = None, bian_shang: str = None, bian_xia: str = None,
                           hu_name: str = None, hu_shang: str = None, hu_xia: str = None,
                           calendar: dict = None, method: str = "") -> str:
    """本卦/变卦/互卦 三栏对照表

    示例:
        ┌──────────┬──────────┬──────────┐
        │   本卦    │   互卦    │   变卦    │
        │ ䷟ 雷风恒 │ ䷪ 泽天夬 │ ䷡ 雷天大壮│
        │ ☳☴ 动1   │ ☱☰      │ ☳☰      │
        └──────────┴──────────┴──────────┘
    """
    dongyao_list = dongyao_list or []
    lines = []

    lines.append("┌" + "─" * 24 + "┬" + "─" * 24 + "┬" + "─" * 24 + "┐")

    # 标题行
    headers = ["本卦", "互卦" if hu_name else "变卦", "变卦" if hu_name else "体用"]
    hdr = "│"
    for h in headers:
        hdr += f"{h:^24}│"
    lines.append(hdr)
    lines.append("├" + "─" * 24 + "┼" + "─" * 24 + "┼" + "─" * 24 + "┤")

    # 卦名行
    ben_uc = HEXAGRAM_UNICODE.get(ben_name, "  ")
    col1 = f" {ben_uc} {ben_name}"
    if hu_name:
        hu_uc = HEXAGRAM_UNICODE.get(hu_name, "  ")
        col2 = f" {hu_uc} {hu_name}"
    else:
        col2 = " —"
    if bian_name:
        bian_uc = HEXAGRAM_UNICODE.get(bian_name, "  ")
        col3 = f" {bian_uc} {bian_name}"
    else:
        col3 = " —"
    lines.append(f"│{col1:<24}│{col2:<24}│{col3:<24}│")

    # 上下卦行
    ben_pic = BAGUA_PIC.get(ben_shang, "?") + BAGUA_PIC.get(ben_xia, "?")
    col1 = f" {ben_pic} {ben_shang}上{ben_xia}下"
    if hu_shang and hu_xia:
        hu_pic = BAGUA_PIC.get(hu_shang, "?") + BAGUA_PIC.get(hu_xia, "?")
        col2 = f" {hu_pic} {hu_shang}上{hu_xia}下"
    else:
        col2 = ""
    if bian_shang and bian_xia:
        bian_pic = BAGUA_PIC.get(bian_shang, "?") + BAGUA_PIC.get(bian_xia, "?")
        col3 = f" {bian_pic} {bian_shang}上{bian_xia}下"
    else:
        col3 = ""
    lines.append(f"│{col1:<24}│{col2:<24}│{col3:<24}│")

    # 动爻行
    if dongyao_list:
        dy_str = "动爻: " + ",".join(f"{d}" for d in dongyao_list)
    else:
        dy_str = "静卦 (无动爻)"
    lines.append(f"│{dy_str:<24}│{'':24}│{'':24}│")

    # 历法行
    if calendar:
        y = calendar.get("年干支", calendar.get("year", ""))
        m = calendar.get("月干支", calendar.get("month", ""))
        cal_str = f"{y}年 {m}月"
        lines.append(f"│{cal_str:<24}│{'起卦: '+method:<24}│{'':24}│")

    lines.append("└" + "─" * 24 + "┴" + "─" * 24 + "┴" + "─" * 24 + "┘")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# 输出格式化
# ═══════════════════════════════════════════════════════════════

def format_output(result: dict, method: str = "dayan") -> str:
    """将起卦结果格式化为可读中文"""
    output = []

    if method == "dayan":
        output.append(format_dayan(result))
    elif method == "meihua":
        output.append(format_meihua(result))
    elif method == "liuyao":
        output.append(format_liuyao(result))
    return "\n".join(output)


def format_dayan(result: dict) -> str:
    """大衍筮法格式化输出 — 新版：Unicode卦画 + 结构化"""
    ben = result["ben_gua"]
    dong = result["dong_yao"]
    cal = result["calendar"]
    method_str = result.get("method", "大衍筮法")
    method_desc = result.get("method_desc", "")

    lines = []

    # ── 卦画可视化 ──
    lines.append(hexagram_diagram(
        ben["yao"],
        gua_name=ben["name"],
        shang=ben["shang"],
        xia=ben["xia"],
        dongyao_list=dong
    ))

    # ── 信息摘要 ──
    lines.append(f"\n  起卦: {method_str} ({method_desc})")
    lines.append(f"  历法: {cal['year']}年 {cal['month']}月 {cal['day']}日")
    dong_str = "、".join(f"第{d}爻" for d in dong) if dong else "无 (静卦)"
    lines.append(f"  动爻: {dong_str}")

    if result["bian_gua"]:
        bian = result["bian_gua"]
        lines.append(f"  变卦: {bian['name']}  {bian.get('shang_pic','')}{bian.get('xia_pic','')}")

    return "\n".join(lines)


def format_meihua(result: dict) -> str:
    """梅花易数格式化 — 新版：三栏对照表 + 卦画 + 体用"""
    cal = result["calendar"]
    b = result["ben_gua"]
    h = result["hu_gua"]
    bg = result["bian_gua"]
    dong = result["dong_yao"]
    ty = result["ti_yong"]

    lines = []

    # ── 卦画可视化 (本卦) ──
    lines.append(hexagram_diagram(
        b["yao"], gua_name=b["name"],
        shang=b["shang"], xia=b["xia"],
        dongyao_list=[dong]
    ))
    lines.append("")

    # ── 三栏对照表 ──
    lines.append(hexagram_summary_table(
        ben_name=b["name"], ben_shang=b["shang"], ben_xia=b["xia"],
        dongyao_list=[dong],
        bian_name=bg["name"], bian_shang=bg["shang"], bian_xia=bg["xia"],
        hu_name=h["name"], hu_shang=h["shang"], hu_xia=h["xia"],
        calendar=cal, method=result["method"]
    ))

    # ── 体用 ──
    lines.append(f"\n  体: {ty['ti']}{ty['ti_pic']} ({ty['ti_wuxing']})  "
                 f"用: {ty['yong']}{ty['yong_pic']} ({ty['yong_wuxing']})  "
                 f"→ {ty['relation']} ({ty['relation_desc']})")

    return "\n".join(lines)


def format_liuyao(result: dict) -> str:
    """六爻纳甲格式化 — 新版：Unicode卦画 + 纳甲详表"""
    b = result["本卦"]
    bg = result["变卦"]
    changing = result["动爻"]

    lines = []

    # ── 本卦卦画可视化 ──
    ben_yao = [1 if (d["阴阳"] == "—") else 0 for d in result["爻位详情"]]

    lines.append(hexagram_diagram(
        ben_yao,
        gua_name=b["name"],
        shang=b["shang"], xia=b["xia"],
        dongyao_list=changing,
        shi_pos=b["shi"], ying_pos=b["ying"]
    ))

    # ── 摘要行 ──
    lines.append(f"\n  起卦: 六爻纳甲 (铜钱摇卦法)")
    lines.append(f"  时间: {result['占卜时间']}")
    lines.append(f"  历法: {result['年干支']}年 {result['月干支']}月 {result['日干支']}日")
    lines.append(f"  本卦: {b['name']} ({b['palace']}宫·{b['wuxing']})  世爻{b['shi']}·应爻{b['ying']}")
    lines.append(f"  变卦: {bg['name']} ({bg['palace']}宫·{bg['wuxing']})")
    dong_str = "、".join(str(d) for d in changing) if changing else "无 (静卦)"
    lines.append(f"  动爻: {dong_str}")

    # ── 纳甲详表 ──
    lines.append(f"\n  {'位':<3} {'爻':<12} {'纳甲':<6} {'六亲':<6} {'六神':<6} {'世应':<4} {'动变':<4}")
    lines.append("  " + "-" * 44)
    for d in result["爻位详情"]:
        row = (f"  {d['pos']:<3} {d['卦画']:<12} {d['纳甲']:<6} "
               f"{d['六亲']:<6} {d['六神']:<6} {d['世应']:<4} {d['动变']:<4}")
        lines.append(row)

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def main():
    if sys.stdout.encoding != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    if len(sys.argv) < 2:
        # 默认大衍筮法
        result = qigua("dayan")
        print(format_output(result, "dayan"))
        return

    arg = sys.argv[1]

    # 兼容旧版 --json 参数
    if arg in ("--json",):
        result = qigua("dayan")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if arg == "dayan":
        seed = int(sys.argv[2]) if len(sys.argv) > 2 else None
        result = qigua("dayan", seed=seed)
        print(format_output(result, "dayan"))

    elif arg == "meihua":
        if len(sys.argv) < 3:
            result = qigua("meihua")
            print(format_output(result, "meihua"))
        elif sys.argv[2] == "time":
            result = qigua("meihua", meihua_method="time")
            print(format_output(result, "meihua"))
        elif sys.argv[2] == "number":
            nums = [int(x) for x in sys.argv[3:]]
            result = qigua("meihua", meihua_method="number", numbers=nums)
            print(format_output(result, "meihua"))
        else:
            print("用法: python qigua.py meihua [time|number <数1> <数2> [数3]]")
            sys.exit(1)

    elif arg == "liuyao":
        if len(sys.argv) > 2 and sys.argv[2] == "--lines":
            result = qigua("liuyao", line_str=sys.argv[3])
        else:
            result = qigua("liuyao")
        print(format_output(result, "liuyao"))

    else:
        print("用法: python qigua.py [dayan|meihua|liuyao] [选项]")
        print("  dayan              大衍筮法起卦（默认）")
        print("  meihua time        梅花时间起卦")
        print("  meihua number a b c  梅花数字起卦")
        print("  liuyao             六爻自动摇卦")
        print("  --json             大衍筮法 JSON 输出（兼容旧版）")
        sys.exit(1)


if __name__ == "__main__":
    main()
