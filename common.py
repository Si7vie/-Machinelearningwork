import csv
from pathlib import Path
from typing import Any, Dict, List

import yaml


def read_yaml(file_path: str) -> Dict[str, Any]:
    """读取YAML配置文件"""
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def write_csv(file_path: str, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    """将数据写入CSV文件，自动创建目录"""
    output_path = Path(file_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
