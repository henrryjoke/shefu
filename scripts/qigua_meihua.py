#!/usr/bin/env python3
"""梅花易数起卦模块（薄包装）
合并后逻辑见 qigua.py，此文件仅保留 CLI 以兼容旧调用方式。
"""

import json
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
from qigua import meihua_qigua, format_meihua


def main():
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    if len(sys.argv) < 2:
        result = meihua_qigua("time")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    arg = sys.argv[1]
    if arg == "time":
        result = meihua_qigua("time")
    elif arg == "number":
        nums = [int(x) for x in sys.argv[2:]]
        result = meihua_qigua("number", numbers=nums)
    else:
        print(f"用法: python qigua_meihua.py [time|number <数1> <数2> [数3]]")
        sys.exit(1)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
