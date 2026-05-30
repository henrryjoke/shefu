#!/usr/bin/env python3
"""大衍筮法起卦模块（薄包装）
合并后逻辑见 qigua.py，此文件仅保留 CLI 以兼容旧调用方式。
"""

import json
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
from qigua import dayan_qigua, format_dayan


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    import argparse
    parser = argparse.ArgumentParser(description="大衍筮法起卦")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    parser.add_argument("--seed", type=int, default=None, help="随机种子（调试用）")
    args = parser.parse_args()

    result = dayan_qigua(seed=args.seed)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_dayan(result))


if __name__ == "__main__":
    main()
