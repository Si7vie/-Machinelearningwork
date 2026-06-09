from __future__ import annotations

import argparse
import json
import os
import re

import requests
from dotenv import load_dotenv

from common import read_jsonl, read_yaml, write_jsonl


def extract_grant_amount(text):
    patterns = [
          r"拟授出.*?([0-9,.]+)\s*万份",
          r"权益总计.*?([0-9,.]+)\s*万份",
          r"股票期权数量.*?([0-9,.]+)\s*万份",
          # 最标准
          r"授予.*?([0-9,.]+)\s*万份",
          r"拟授予.*?([0-9,.]+)\s*万份",
          r"股票期权.*?([0-9,.]+)\s*万份",

          # 总量
          r"权益总量.*?([0-9,.]+)\s*万份",
          r"股票期权总量.*?([0-9,.]+)\s*万份",

          # 不带万份
          r"授予.*?([0-9,]+)\s*份",
          r"拟授予.*?([0-9,]+)\s*份",
          r"股票期权总量.*?([0-9,]+)\s*份",

          # 常见草案表述
          r"拟向激励对象授予.*?([0-9,.]+)\s*万份",
          r"拟向激励对象授予.*?([0-9,]+)\s*份",

          r"授予的股票期权总量.*?([0-9,.]+)\s*万份",
          r"授予的股票期权总量.*?([0-9,]+)\s*份",

          r"不超过\s*([0-9,.]+)\s*万份",
          r"不超过\s*([0-9,]+)\s*份",
          # 权益总计
          r"权益总计\s*([0-9,.]+)\s*万股",
          r"权益总计\s*([0-9,.]+)\s*万份",

          # 授予权益总计
          r"授予权益总计\s*([0-9,.]+)\s*万股",
          r"授予权益总计\s*([0-9,.]+)\s*万份",

          # 拟向激励对象授予
          r"拟向激励对象授予.*?([0-9,.]+)\s*万股",
          r"拟向激励对象授予.*?([0-9,.]+)\s*万份",
          r"股票期权数量.*?([0-9,.]+)\s*万股"
        ]

    for p in patterns:
        m = re.search(p, text, re.S)

        if m:

            value = m.group(1).replace(",", "")

            value = float(value)

            # 如果单位是“份”
            if "万份" not in m.group(0):
                value = value / 10000

            return value

    return None


def extract_grant_ratio(text):
    patterns = [
             r"占.*?总股本.*?([0-9.]+)\s*%",

             r"占.*?股本总额.*?([0-9.]+)\s*%",

             r"占.*?股本比例.*?([0-9.]+)\s*%",

             r"约占.*?总股本.*?([0-9.]+)\s*%",

             r"约占.*?股本总额.*?([0-9.]+)\s*%", 
             r"占.*?公司股本总额.*?([0-9.]+)\s*%",

             r"约占.*?股本总额.*?([0-9.]+)\s*%",       
]

    for p in patterns:
        m = re.search(p, text, re.S)
        if m:
            return float(m.group(1))
    return None


def extract_participant_count(text):

    patterns = [
        r"激励对象.*?共计\s*([0-9,]+)\s*人",
        r"激励对象人数.*?([0-9,]+)\s*人",
        r"首次授予.*?([0-9,]+)\s*人",
        r"激励对象总人数为\s*([0-9,]+)\s*人",
        r"激励对象人数为\s*([0-9,]+)\s*人",
        r"激励对象共计\s*([0-9,]+)\s*人",
        r"激励对象总人数\s*([0-9,]+)\s*人",
        r"首次授予激励对象共\s*([0-9,]+)\s*人",
        r"首次授予激励对象\s*([0-9,]+)\s*人",
        r"涉及激励对象\s*([0-9,]+)\s*人",
        r"涉及\s*([0-9,]+)\s*名激励对象",
        r"共\s*([0-9,]+)\s*名激励对象",
        r"激励对象\s*([0-9,]+)\s*人",
        # 表格底部
        r"合计\s*([0-9,]+)\s*[人名]",
        r"总计\s*([0-9,]+)\s*[人名]",
        r"激励对象.*?不超过\s*([0-9,]+)\s*人"
    ]

    for p in patterns:
        m = re.search(p, text, re.S)
        if m: 
            return int(
                 m.group(1).replace(",", "")
                )
    return None
def extract_exercise_price(text):
    patterns = [
       r"行权价格.*?([0-9.]+)\s*元",
       r"行权价格为\s*([0-9.]+)\s*元",
       r"股票期权行权价格.*?([0-9.]+)\s*元",
       r"授予价格.*?([0-9.]+)\s*元",
    ]

    for p in patterns:
        m = re.search(p, text, re.S)
        if m:
            return float(m.group(1))
    return None


def extract_waiting_period(text):
    patterns = [
        r"等待期.*?([0-9]+)\s*个月",
        r"等待期为\s*([0-9]+)\s*个月",
    ]

    for p in patterns:
        m = re.search(p, text, re.S)
        if m:
            return float(m.group(1))
    return None


def extract_validity_period(text):
    patterns = [
        r"有效期.*?([0-9]+)\s*个月",
        r"有效期最长.*?([0-9]+)\s*个月",
        r"本激励计划有效期.*?([0-9]+)\s*个月",
    ]

    for p in patterns:
        m = re.search(p, text, re.S)
        if m:
            return float(m.group(1))
    return None


def extract_one_rule(section):
    text = section["section_text"]

    result = {
        "doc_id": section["doc_id"],
        "company_name": section.get("stock_name"),
        "stock_code": section.get("stock_code"),

        "grant_amount":
            extract_grant_amount(text),

        "grant_ratio":
            extract_grant_ratio(text),

        "participant_count":
            extract_participant_count(text),

        "exercise_price":
            extract_exercise_price(text),

        "discount_rate":
            None,

        "waiting_period":
            extract_waiting_period(text),

        "validity_period":
            extract_validity_period(text),

        "evidences": [
            {
                "text": text[:500],
                "page_no": section.get("page_no")
            }
        ]
    }

    return result


def strip_json_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text, flags=re.I).strip()
        text = re.sub(r"```$", "", text).strip()
    return text


def call_llm(messages: list[dict], config: dict) -> str:
    load_dotenv()
    llm = config.get("extract", {}).get("llm", {})
    base_url = os.getenv(llm.get("base_url_env", "LLM_BASE_URL"), "").rstrip("/")
    api_key = os.getenv(llm.get("api_key_env", "LLM_API_KEY"), "")
    model = os.getenv(llm.get("model_env", "LLM_MODEL"), "")
    if not base_url:
        raise RuntimeError("Missing LLM_BASE_URL. For SiliconFlow use https://api.siliconflow.cn/v1")
    if not api_key or api_key == "your_key_here":
        raise RuntimeError("Missing real LLM_API_KEY.")
    if not model or model == "your_model_here":
        raise RuntimeError("Missing real LLM_MODEL.")

    response = requests.post(
        f"{base_url}/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": messages,
            "temperature": float(llm.get("temperature", 0)),
            "max_tokens": int(llm.get("max_tokens", 2048)),
        },
        timeout=int(llm.get("timeout_seconds", 60)),
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


def extract_one_llm(section: dict, config: dict) -> dict:
    schema_hint = {
        "doc_id": section["doc_id"],
        "stock_code": section.get("stock_code"),
        "company_name": section.get("stock_name"),
        "report_year": "2024",
        "event_type": "年报风险披露",
        "risk_categories": [
            {
                "category": "市场风险",
                "evidence": {"text": "必须是输入文本中的原文片段", "page_no": section.get("page_no")},
            }
        ],
    }
    prompt = f"""你是上市公司年报风险披露分类助手。请只根据输入的风险披露章节抽取风险类别。

可选类别：
市场风险、行业竞争风险、经营风险、财务风险、政策与合规风险、技术与研发风险、供应链与原材料风险、汇率与利率风险、环境与安全风险、管理与内控风险、其他风险。

规则：
1. 只输出合法 JSON，不要输出解释。
2. risk_categories 可以有多个类别，但不要重复。
3. 每个类别必须给出 evidence.text，且必须是输入文本中的连续原文片段。
4. 不确定时不要猜；无法归入具体类别但原文确有风险披露时，使用"其他风险"。
5. 输出字段必须与 JSON 模板一致。

JSON 模板：
{json.dumps(schema_hint, ensure_ascii=False)}

题头元数据：
doc_id={section["doc_id"]}
stock_code={section.get("stock_code")}
company_name={section.get("stock_name")}
title={section["title"]}
page_no={section.get("page_no")}

输入文本：
{section["section_text"][:16000]}
"""
    content = call_llm(
        [
            {"role": "system", "content": "你只输出合法 JSON。"},
            {"role": "user", "content": prompt},
        ],
        config,
    )
    return json.loads(strip_json_fence(content))


def extract_fields(config_path: str, method: str | None = None) -> list[dict]:
    config = read_yaml(config_path)
    sections_path = config["paths"].get("sections_jsonl", "data/parsed/sections.jsonl")
    output_path = config["paths"]["extract_results"]
    method = method or config.get("extract", {}).get("provider", "rule")
    results = []
    for section in read_jsonl(sections_path):
        if section["found"]:
            if method == "rule":
                results.append(extract_one_rule(section))
            elif method == "llm":
                results.append(extract_one_llm(section, config))
            else:
                raise ValueError(f"Unknown extraction method: {method}")
    if not results:
        raise RuntimeError("No extraction results were produced.")
    write_jsonl(output_path, results)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract annual-report risk categories.")
    parser.add_argument("--config", default="configs/workflow.yaml")
    parser.add_argument("--method", choices=["rule", "llm"], default=None)
    args = parser.parse_args()
    results = extract_fields(args.config, args.method)
    print(f"Extracted {len(results)} records.")


if __name__ == "__main__":
    main()
