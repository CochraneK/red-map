#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ASR 字幕术语纠错：faster-whisper-base 对长征/军事题材错字率高，
用领域词典做后处理后，再交给 extract_subtitle_candidates.py。
只纠正确定的术语映射，不做语义改写。
"""
import re
import sys
from pathlib import Path

# 术语纠错表：错字/错词 -> 正确（按长词优先替换）
TERMS = {
    # 地名
    "刺水": "赤水", "事都刺水": "四渡赤水", "似度次水": "四渡赤水",
    "尊益": "遵义", "尊義": "遵义", "遵益": "遵义",
    "楼山关": "娄山关", "婁山關": "娄山关", "婁山关": "娄山关",
    "核酱線": "合江县", "河江縣": "合江县",
    "貴洋": "贵阳", "貴陽": "贵阳",
    "金沙江": "金沙江", "烏江水溪": "乌江",
    "土城": "土城", "扎西": "扎西",
    "毛兒蓋": "毛儿盖", "毛儿益": "毛儿盖",
    "樣場": "两河口",
    # 部队
    "紅衣軍團": "红一军团", "紅衣軍團": "红一军团", "紅一軍團": "红一军团",
    "紅酒軍團": "红九军团", "紅武軍團": "红五军团", "紅山軍團": "红三军团",
    "紅衣": "红一", "紅酒": "红九", "紅武": "红五", "紅山": "红三",
    "國軍": "国军", "我军": "我军",
    "王家列": "王家烈", "奢約": "薛岳", "巴克斯": "柏辉章",
    "廣東廣棄": "广东广西", "鄉軍": "湘军", "黔軍": "黔军",
    # 人物/职务
    "毛澤東": "毛泽东", "周總理": "周总理", "蒋中正": "蒋介石",
    "朱 deaf": "朱德",
    # 军事术语
    "步鎮": "布阵", "暫靈均衣": "战领均宜",
    "場線": "防线", "防線": "防线", "完整場線": "完整防线",
    "抹衣": "Buy", "幹": "做",
    "前風引進": "前锋已经", "已經": "已经", "暫理": "占领",
    "包圍": "包围", "圍殲": "围歼", "突圍": "突围",
    "機動": "机动", "聲東擊西": "声东击西",
    # 常见ASR噪音
    "講": "讲", "條": "条", "為": "为", "紅": "红", "軍": "军", "團": "团",
    "鎮": "镇", "線": "线", "會": "会", "從": "从", "過": "过", "後": "后",
    "國": "国", "軍隊": "军队", "敵": "敌", "將": "将", "與": "与",
}


def correct(text: str) -> str:
    # 长词优先
    for k in sorted(TERMS, key=len, reverse=True):
        text = text.replace(k, TERMS[k])
    return text


def main():
    if len(sys.argv) < 3:
        print("用法: python tools/correct_asr_terms.py <input.srt> <output.srt>", file=sys.stderr)
        return 1
    src = Path(sys.argv[1]); dst = Path(sys.argv[2])
    lines = src.read_text(encoding="utf-8").split("\n")
    out = []
    for line in lines:
        # srt 格式：序号行/时间行/文本行/空行 —— 只纠正文本行（含中文且非时间行）
        if "-->" in line or not re.search(r"[\u4e00-\u9fff]", line):
            out.append(line)
        else:
            out.append(correct(line))
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text("\n".join(out), encoding="utf-8")
    changed = sum(1 for a, b in zip(lines, out) if a != b)
    print(f"[OK] 纠正 {changed} 行 -> {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
