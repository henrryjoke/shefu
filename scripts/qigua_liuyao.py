#!/usr/bin/env python3
"""六爻纳甲起卦模块（薄包装）
合并后逻辑见 qigua.py，此文件仅保留 CLI 以兼容旧调用方式。
"""

import json
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
from qigua import liuyao_qigua, liuyao_parse_lines


def main():
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    import argparse
    parser = argparse.ArgumentParser(description="六爻纳甲起卦")
    parser.add_argument("--lines", type=str, default=None,
                        help="手动输入6爻铜钱结果，格式: '正正反,正反反,...' (6组，逗号分隔)")
    parser.add_argument("--day-gan", type=str, default=None, help="日干 (甲-癸)")
    args = parser.parse_args()

    if args.lines:
        lines = liuyao_parse_lines(args.lines)
        result = liuyao_qigua(lines=lines)
    else:
        result = liuyao_qigua()

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
