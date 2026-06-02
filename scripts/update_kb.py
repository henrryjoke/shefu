#!/usr/bin/env python3
"""类象库 + 画像更新引擎

每轮射覆复盘(S3)后自动执行：
  1. 读取当前类象库和画像
  2. 处理本轮结果（命中/遗漏/新发现）
  3. 更新置信度和权重
  4. 输出更新摘要

用法：
  python update_kb.py --round-file round_result.json
  python update_kb.py --round-json '{"本卦":"...","实际物品":"..."}'
  python update_kb.py --summary  # 仅显示当前类象库和画像摘要
"""

import json
import sys
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(BASE_DIR)
DATA_DIR = os.path.join(SKILL_DIR, "data")

KX_DB_PATH = os.path.join(DATA_DIR, "类象库.json")
PROFILE_PATH = os.path.join(SKILL_DIR, "profile.json")

# ── 置信度调整参数 ──
HIT_INCREMENT = 0.05       # 命中：小幅提升
HIT_CAP = 0.95             # 置信度上限
MISS_DECREMENT = -0.10     # 错误信号：降权
MISS_FLOOR = 0.10          # 置信度下限
OVERLOOK_INCREMENT = 0.02  # 遗漏但存在的信号：微量提升
NEW_DISCOVERY_INIT = 0.30  # 新发现：从推测级开始
PROFILE_HIT_BOOST = 0.08   # 画像命中权重增量
PROFILE_MISS_PENALTY = -0.10  # 画像错误权重减量
PROFILE_OVERLOOK_BOOST = 0.03  # 画像遗漏信号增量
PROFILE_WEIGHT_CAP = 2.0
PROFILE_WEIGHT_FLOOR = 0.3


def load_json(path):
    """加载 JSON 文件（带异常捕获和降级）"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"  ⚠️ 文件不存在: {path}，返回空结构")
        return {}
    except json.JSONDecodeError as e:
        print(f"  ⚠️ JSON 解析失败: {path} — {e}，返回空结构")
        return {}
    except Exception as e:
        print(f"  ⚠️ 读取失败: {path} — {e}，返回空结构")
        return {}


def save_json(path, data):
    """保存 JSON 文件（原子写入：先写临时文件，再替换）"""
    import tempfile
    dir_name = os.path.dirname(path)
    # 先写到同目录下的临时文件
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".tmp", prefix=".", dir=dir_name)
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        # 原子替换
        os.replace(tmp_path, path)
        print(f"  ✓ 已保存: {os.path.basename(path)}")
    except Exception:
        # 清理临时文件
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def clamp(value, lo, hi):
    return max(lo, min(hi, value))


def find_mapping(kx_db, trigram, dimension):
    """在类象库中模糊查找指定卦的指定维度映射"""
    if trigram not in kx_db.get("trigrams", {}):
        return None

    t = kx_db["trigrams"][trigram]

    # 模糊匹配辅助：判断两个字符串是否语义相近
    def fuzzy_match(target, candidate):
        if not target or not candidate:
            return False
        t = target.replace(" ", "")
        c = candidate.replace(" ", "")
        # 直接包含
        if t in c or c in t:
            return True
        # 关键词拆分匹配（按 / 分隔）
        target_words = set(t.split("/"))
        candidate_words = set(c.split("/"))
        overlap = target_words & candidate_words
        if overlap:
            return True
        # 部分子串匹配（处理如"金属小件"→"金属"的情况）
        for tw in target_words:
            for cw in candidate_words:
                if tw in cw or cw in tw:
                    return True
        return False

    # 遍历所有维度
    for dim_name, entries in t.get("dimensions", {}).items():
        for entry in entries:
            if fuzzy_match(dimension, entry.get("value", "")):
                return entry, dim_name

    # 遍历参考物品
    for entry in t.get("reference_objects", []):
        if fuzzy_match(dimension, entry.get("item", "")) or fuzzy_match(dimension, entry.get("source", "")):
            return entry, "reference_objects"

    # 遍历信号组合
    for combo in t.get("signal_combinations", []):
        desc = combo.get("description", "")
        if fuzzy_match(dimension, desc):
            return combo, "signal_combinations"

    return None, None


def update_confidence(entry, delta, cap=HIT_CAP, floor=MISS_FLOOR):
    """更新条目置信度"""
    if isinstance(entry, dict):
        old = entry.get("confidence", 0.5)
        entry["confidence"] = round(clamp(old + delta, floor, cap), 2)
        return old, entry["confidence"]
    return None, None


def update_kx_db(kx_db, round_data):
    """更新类象库"""
    print("\n📚 类象库更新：")
    changes = {"confirmed": [], "overlooked": [], "new_discoveries": [], "errors": []}

    # ── 处理命中信号 ──
    for signal in round_data.get("命中信号", []):
        trigram = signal.get("卦", "")
        dimension = signal.get("维度", "")
        if not trigram or not dimension:
            continue

        entry, dim_name = find_mapping(kx_db, trigram, dimension)
        if entry:
            old, new = update_confidence(entry, HIT_INCREMENT)
            if old and new:
                changes["confirmed"].append({
                    "trigram": trigram, "dimension": dimension,
                    "confidence": f"{old:.2f} → {new:.2f}"
                })
                print(f"  ✅ 命中: {trigram}::{dimension} {old:.2f} → {new:.2f}")
        else:
            print(f"  ⚠️ 命中但未找到对应映射: {trigram}::{dimension}")

    # ── 处理遗漏信号（存在但未激活） ──
    for signal in round_data.get("遗漏信号", []):
        trigram = signal.get("卦", "")
        dimension = signal.get("维度", "")
        if not trigram or not dimension:
            continue

        entry, dim_name = find_mapping(kx_db, trigram, dimension)
        if entry:
            old, new = update_confidence(entry, OVERLOOK_INCREMENT)
            if old and new:
                changes["overlooked"].append({
                    "trigram": trigram, "dimension": dimension,
                    "confidence": f"{old:.2f} → {new:.2f}"
                })
                print(f"  👁  遗漏: {trigram}::{dimension} {old:.2f} → {new:.2f}")
        else:
            # 存在于信号组合中但未独立映射 → 添加
            pass

    # ── 处理错误信号 ──
    for signal in round_data.get("错误信号", []):
        trigram = signal.get("卦", "")
        dimension = signal.get("维度", "")
        if not trigram or not dimension:
            continue

        entry, dim_name = find_mapping(kx_db, trigram, dimension)
        if entry:
            old, new = update_confidence(entry, MISS_DECREMENT, floor=MISS_FLOOR)
            if old and new:
                changes["errors"].append({
                    "trigram": trigram, "dimension": dimension,
                    "confidence": f"{old:.2f} → {new:.2f}"
                })
                print(f"  ❌ 错误: {trigram}::{dimension} {old:.2f} → {new:.2f}")

    # ── 处理新发现 ──
    for discovery in round_data.get("新发现", []):
        trigram = discovery.get("卦", "")
        dimension = discovery.get("维度", "")
        item_desc = discovery.get("物品对应", "")
        if not trigram or not dimension:
            continue

        t = kx_db["trigrams"].get(trigram)
        if not t:
            print(f"  ⚠️ 未知卦名: {trigram}")
            continue

        # 添加到 reference_objects
        new_entry = {
            "item": item_desc or dimension,
            "confidence": NEW_DISCOVERY_INIT,
            "source": f"新发现-第{round_data.get('round', '?')}轮: {item_desc}",
            "validations": 1,
            "role": "reference"
        }
        t.setdefault("reference_objects", []).append(new_entry)
        changes["new_discoveries"].append({
            "trigram": trigram, "item": item_desc,
            "confidence": NEW_DISCOVERY_INIT
        })
        print(f"  🆕 新发现: {trigram} → {item_desc} (初始置信度: {NEW_DISCOVERY_INIT})")

    # ── 追加验证记录 ──
    kx_db["validation_log"].append({
        "round": round_data.get("round", kx_db.get("_meta", {}).get("total_validations", 0) + 1),
        "本卦": round_data.get("本卦", ""),
        "变卦": round_data.get("变卦", ""),
        "动爻": round_data.get("动爻", ""),
        "实际物品": round_data.get("实际物品", ""),
        "品类": round_data.get("品类", ""),
        "命中": round_data.get("AI命中", False),
        "命中信号": round_data.get("命中信号", []),
        "遗漏信号": round_data.get("遗漏信号", []),
        "错误信号": round_data.get("错误信号", []),
        "核心教训": round_data.get("核心教训", "")
    })

    # 更新元数据
    kx_db["_meta"]["total_validations"] = kx_db.get("_meta", {}).get("total_validations", 0) + 1
    kx_db["_meta"]["last_validation_round"] = round_data.get("round",
        kx_db["_meta"]["total_validations"])
    kx_db["_meta"]["updated"] = datetime.now().strftime("%Y-%m-%d")

    return changes


def update_profile(profile, round_data):
    """更新用户画像（v0.3.0 特征维度偏好版）"""
    print("\n👤 画像更新：")
    changes = {}

    hit = round_data.get("AI命中", False)
    bg = round_data.get("背景环境", "")
    category = round_data.get("品类", "")
    round_num = round_data.get("round", 0)

    # ── 特征维度偏好 ──
    dim_prefs = profile.get("特征维度偏好", {})
    for signal in round_data.get("命中信号", []):
        dim = signal.get("维度", "")
        if dim in dim_prefs and not dim.startswith("_"):
            old_w = dim_prefs[dim] if isinstance(dim_prefs[dim], (int, float)) else dim_prefs[dim].get("weight", 1.0)
            new_w = round(clamp(old_w + PROFILE_HIT_BOOST, PROFILE_WEIGHT_FLOOR, PROFILE_WEIGHT_CAP), 2)
            dim_prefs[dim] = new_w
            print(f"  ✅ {dim}权重: {old_w:.2f} → {new_w:.2f}")

    for signal in round_data.get("错误信号", []):
        dim = signal.get("维度", "")
        if dim in dim_prefs and not dim.startswith("_"):
            old_w = dim_prefs[dim] if isinstance(dim_prefs[dim], (int, float)) else dim_prefs[dim].get("weight", 1.0)
            new_w = round(clamp(old_w + PROFILE_MISS_PENALTY, PROFILE_WEIGHT_FLOOR, PROFILE_WEIGHT_CAP), 2)
            dim_prefs[dim] = new_w
            print(f"  ❌ {dim}权重: {old_w:.2f} → {new_w:.2f}")

    profile["特征维度偏好"] = dim_prefs

    # ── 场景先验 ──
    scene_data = profile.get("场景先验", {})
    if isinstance(scene_data, dict):
        scenes = scene_data.get("常见场景", ["未记录"])
        if bg and bg != "未记录":
            if scenes == ["未记录"]:
                scenes = [bg]
            elif bg not in scenes:
                scenes.append(bg)
                if len(scenes) > 5:
                    scenes.pop(0)
            scene_data["常见场景"] = scenes
        profile["场景先验"] = scene_data

    # ── 最近20轮 ──
    recent = profile.get("最近20轮", [])
    recent.append({
        "round": round_num or len(recent) + 1,
        "本卦": round_data.get("本卦", ""),
        "实际物品": round_data.get("实际物品", ""),
        "品类": category,
        "命中": hit,
        "背景": bg or "未记录"
    })
    if len(recent) > 20:
        recent = recent[-20:]
    profile["最近20轮"] = recent

    # ── 全局统计 ──
    stats = profile.get("全局统计", {})
    total = len(recent)
    hits = sum(1 for r in recent if r.get("命中") == True)
    stats["特征命中率"] = round(hits / total, 2) if total > 0 else 0.0

    # Most common category
    cat_counts = {}
    for r in recent:
        c = r.get("品类", "未知")
        cat_counts[c] = cat_counts.get(c, 0) + 1
    if cat_counts:
        stats["最多品类"] = max(cat_counts, key=cat_counts.get)
    profile["全局统计"] = stats

    profile["_meta"]["total_rounds"] = total
    profile["_meta"]["updated"] = datetime.now().strftime("%Y-%m-%d")

    return changes


def print_summary(kx_db, profile):
    """打印当前类象库和画像摘要"""
    print("\n" + "=" * 50)
    print("📊 类象库 + 画像摘要")
    print("=" * 50)

    print(f"\n类象库: v{kx_db['_meta']['version']} | "
          f"总验证轮次: {kx_db['_meta']['total_validations']} | "
          f"更新: {kx_db['_meta']['updated']}")

    print(f"\n画像: 用户={profile['_meta']['user']} | "
          f"总轮次={profile['_meta']['total_rounds']}")

    stats = profile.get("全局统计", {})
    if stats:
        print(f"  特征命中率: {stats.get('特征命中率', 0):.0%} | "
              f"最常见品类: {stats.get('最多品类', '待累积')}")

    # 特征维度偏好
    dim_prefs = profile.get("特征维度偏好", {})
    if isinstance(dim_prefs, dict):
        # Remove meta keys
        real_dims = {k: v for k, v in dim_prefs.items() if not k.startswith("_")}
        if real_dims:
            print("  特征维度偏好:")
            for dim, w in real_dims.items():
                actual_w = w if isinstance(w, (int, float)) else (w.get("weight", 1.0) if isinstance(w, dict) else 1.0)
                if actual_w != 1.0:
                    print(f"    {dim}: {actual_w:.2f}")

    # 维度权重
    print("\n  维度权重调整 (≠1.0 的):")
    dim_prefs = profile.get("特征维度偏好", {})
    has_adjust = False
    if isinstance(dim_prefs, dict):
        for dim, d in dim_prefs.items():
            if dim.startswith("_"):
                continue
            w = d if isinstance(d, (int, float)) else (d.get("weight", 1.0) if isinstance(d, dict) else 1.0)
            if w != 1.0:
                has_adjust = True
                print(f"    {dim}: {w:.2f}")
    if not has_adjust:
        print("    (全部默认 1.0)")

    # 高置信度映射
    print("\n  高置信度映射 (≥0.80):")
    for name, t in kx_db.get("trigrams", {}).items():
        items = []
        for dim_name, entries in t.get("dimensions", {}).items():
            for e in entries:
                if e.get("confidence", 0) >= 0.80 and e.get("validations", 0) > 0:
                    items.append(f"{dim_name}={e['value']}({e['confidence']:.2f})")
        for e in t.get("reference_objects", []):
            if e.get("confidence", 0) >= 0.80 and e.get("validations", 0) > 0:
                items.append(f"物={e['item']}({e['confidence']:.2f})")
        if items:
            print(f"    {name}{t['symbol']}: {', '.join(items[:3])}")
    print()


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    import argparse
    parser = argparse.ArgumentParser(description="类象库 + 画像更新引擎")
    parser.add_argument("--round-file", type=str, help="本轮结果 JSON 文件路径")
    parser.add_argument("--round-json", type=str, help="本轮结果 JSON 字符串")
    parser.add_argument("--summary", action="store_true", help="仅显示当前摘要，不更新")
    parser.add_argument("--dry-run", action="store_true", help="预览模式：计算但不保存")
    args = parser.parse_args()

    # 加载
    if not os.path.exists(KX_DB_PATH):
        print(f"❌ 类象库不存在: {KX_DB_PATH}")
        sys.exit(1)

    kx_db = load_json(KX_DB_PATH)
    profile = load_json(PROFILE_PATH) if os.path.exists(PROFILE_PATH) else None

    if args.summary:
        print_summary(kx_db, profile or {})
        return

    # 解析轮次结果
    if args.round_file:
        with open(args.round_file, "r", encoding="utf-8") as f:
            round_data = json.load(f)
    elif args.round_json:
        round_data = json.loads(args.round_json)
    else:
        print_summary(kx_db, profile or {})
        return

    # 验证必填字段
    required = ["实际物品", "本卦"]
    missing = [f for f in required if f not in round_data]
    if missing:
        print(f"❌ 缺少必填字段: {missing}")
        sys.exit(1)

    print(f"\n🔮 处理第 {round_data.get('round', '?')} 轮射覆结果")
    print(f"   物品: {round_data.get('实际物品', '?')} | 品类: {round_data.get('品类', '?')}")

    # 更新
    kx_changes = update_kx_db(kx_db, round_data)
    profile_changes = update_profile(profile, round_data) if profile else {}

    # 保存
    if args.dry_run:
        print("\n🔍 (预览模式—未保存)")
    else:
        save_json(KX_DB_PATH, kx_db)
        if profile:
            save_json(PROFILE_PATH, profile)

    # 最终摘要
    print("\n" + "=" * 50)
    print("📋 本轮更新摘要")
    print("=" * 50)
    c = kx_changes
    if c:
        print(f"  确认映射: {len(c.get('confirmed', []))} 条 | 置信度提升: +{HIT_INCREMENT}")
        print(f"  遗漏标记: {len(c.get('overlooked', []))} 条 | 置信度微调: +{OVERLOOK_INCREMENT}")
        print(f"  新发现:    {len(c.get('new_discoveries', []))} 条 | 初始置信度: {NEW_DISCOVERY_INIT}")
        print(f"  错误降权: {len(c.get('errors', []))} 条 | 置信度降低: {MISS_DECREMENT}")
    print()


if __name__ == "__main__":
    main()
