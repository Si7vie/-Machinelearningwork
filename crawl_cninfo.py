#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股权激励方案数据爬取 - 巨潮资讯网

功能：从巨潮资讯网爬取上市公司股权激励计划公告数据，包括公告元数据和PDF文件
输出：
    - metadata.csv: 存储公告元数据（公司代码、名称、公告标题、日期、PDF链接等）
    - PDF文件: 下载到本地存储
"""

# 导入必要的库
import csv
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests


def write_csv(file_path: str, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    """
    将数据写入CSV文件，自动创建父目录
    
    Args:
        file_path: CSV文件输出路径
        rows: 数据行列表，每行是一个字典
        fields: CSV字段名列表
    """
    output_path = Path(file_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def clean_title(title: str) -> str:
    """
    清洗公告标题中的HTML标签和转义字符
    
    Args:
        title: 原始标题字符串
    
    Returns:
        清洗后的标题字符串
    """
    title = re.sub(r"</?em>", "", title)
    title = re.sub(r"<[^>]+>", "", title)
    return title.strip()


def format_date(ms: Optional[int]) -> str:
    """
    将毫秒级时间戳转换为标准日期字符串
    
    Args:
        ms: 毫秒级时间戳
    
    Returns:
        格式化后的日期字符串（YYYY-MM-DD）
    """
    if not ms:
        return ""
    return datetime.fromtimestamp(ms / 1000).strftime("%Y-%m-%d")


def is_date_in_range(ms: Optional[int], start_date: str, end_date: str) -> bool:
    """
    检查日期是否在指定范围内
    
    Args:
        ms: 毫秒级时间戳
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
    
    Returns:
        日期在范围内返回True，否则返回False
    """
    if not ms:
        return False
    try:
        date_obj = datetime.fromtimestamp(ms / 1000)
        start_obj = datetime.strptime(start_date, "%Y-%m-%d")
        end_obj = datetime.strptime(end_date, "%Y-%m-%d")
        return start_obj <= date_obj <= end_obj
    except Exception:
        return False


def request_with_retry(session, method, url, max_retries=3, retry_delay=5, **kwargs):
    """
    带重试机制的HTTP请求
    
    Args:
        session: requests.Session对象
        method: 请求方法 ('get' 或 'post')
        url: 请求URL
        max_retries: 最大重试次数
        retry_delay: 重试间隔（秒）
        **kwargs: 其他请求参数
    
    Returns:
        响应对象
    """
    for attempt in range(max_retries):
        try:
            if method.lower() == "post":
                response = session.post(url, **kwargs)
            else:
                response = session.get(url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                print(f"请求失败 ({attempt + 1}/{max_retries})，{retry_delay}秒后重试: {e}")
                time.sleep(retry_delay)
            else:
                raise e


def query_cninfo(config: dict) -> list[dict]:
    """
    查询巨潮资讯网股权激励公告
    
    Args:
        config: 配置字典，包含查询参数、日期范围等
    
    Returns:
        公告元数据列表，每条记录包含doc_id、stock_code、company_name等字段
    """
    # 建立会话并设置请求头
    session = requests.Session()
    headers = {
        "User-Agent": config["request"]["user_agent"],
        "Referer": "https://www.cninfo.com.cn/new/fulltextSearch",
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    }
    
    # 初始请求，建立会话
    try:
        request_with_retry(session, "get", "https://www.cninfo.com.cn/new/index", headers=headers, timeout=config["request"]["timeout_seconds"])
    except Exception as e:
        print(f"建立会话失败: {e}")
        return []
    
    # 从配置中提取查询参数
    endpoint = config["endpoint"]
    keyword = " ".join(config["keywords"])
    page_size = int(config["query"]["page_size"])
    max_records = int(config["query"]["max_records"])
    sleep_seconds = float(config["request"]["sleep_seconds"])
    timeout = int(config["request"]["timeout_seconds"])
    se_date = f"{config['date_range']['start']}~{config['date_range']['end']}"
    pdf_dir = config["output"]["pdf_dir"]
    start_date = config["date_range"]["start"]
    end_date = config["date_range"]["end"]
    
    rows = []
    seen_stocks = set()
    page_num = 1
    
    print(f"开始爬取股权激励公告，时间范围: {start_date} ~ {end_date}")
    
    # 循环分页获取数据
    while len(rows) < max_records:
        payload = {
            "pageNum": page_num,
            "pageSize": page_size,
            "column": config["query"].get("column", "szse"),
            "tabName": config["query"].get("tab_name", "fulltext"),
            "stock": "",
            "searchkey": keyword,
            "seDate": se_date,
            "isHLtitle": "true",
        }
        
        try:
            response = request_with_retry(session, "post", endpoint, headers=headers, data=payload, timeout=timeout)
            data = response.json()
            announcements = data.get("announcements") or []
        except Exception as e:
            print(f"请求第{page_num}页失败，已达最大重试次数: {e}")
            break
        
        if not announcements:
            print(f"第{page_num}页无数据，停止爬取")
            break
        
        for item in announcements:
            if len(rows) >= max_records:
                break
            
            # 提取基础信息
            stock_code = item.get("secCode") or ""
            adjunct_url = item.get("adjunctUrl") or ""
            title = clean_title(item.get("announcementTitle") or "")
            announcement_time_ms = item.get("announcementTime")
            
            # 过滤条件1: 股票代码有效且未处理过
            if not stock_code or stock_code in seen_stocks:
                continue
            
            # 过滤条件2: 必须是PDF文件
            if not adjunct_url.lower().endswith(".pdf"):
                continue
            
            # 过滤条件3: 标题必须包含所有必需关键词（股票期权激励计划 + 草案）
            required_keywords = config.get("required_title_keywords", [])
            if required_keywords and not all(kw in title for kw in required_keywords):
                continue
            
            # 过滤条件4: 标题不能包含排除关键词（注销、终止、法律意见书等）
            if any(e in title for e in config.get("query", {}).get("title_exclude", [])):
                continue
            
            # 过滤条件5: 日期必须在指定范围内
            if not is_date_in_range(announcement_time_ms, start_date, end_date):
                continue
            
            # 构建记录
            doc_id = item.get("announcementId") or f"{stock_code}_{len(rows)+1}"
            pdf_url = urljoin(config["pdf_base_url"], adjunct_url)
            seen_stocks.add(stock_code)
            
            # 尝试识别行业
            industry = ""
            target_industries = config.get("target_industries", [])
            if target_industries:
                for industry_keyword in target_industries:
                    if industry_keyword in title or industry_keyword in (item.get("secName") or ""):
                        industry = industry_keyword
                        break
            
            rows.append({
                "doc_id": doc_id,
                "stock_code": stock_code,
                "company_name": item.get("secName") or item.get("tileSecName") or "",
                "industry": industry,
                "announcement_title": title,
                "announcement_type": "股权激励计划",
                "publish_date": format_date(announcement_time_ms),
                "url": f"https://www.cninfo.com.cn/new/disclosure/detail?stockCode={stock_code}&announcementId={doc_id}",
                "pdf_url": pdf_url,
                "local_pdf_path": f"{pdf_dir}/{stock_code}_{doc_id}.pdf",
                "source": "cninfo",
                "crawl_time": datetime.now().isoformat(timespec="seconds"),
                "download_status": "pending",
                "error_message": ""
            })
        
        print(f"第{page_num}页: 获取{len(announcements)}条公告，已筛选{len(rows)}条目标记录")
        
        if not data.get("hasMore"):
            break
        page_num += 1
        time.sleep(sleep_seconds)
    
    return rows


def download_pdf(row: dict, config: dict) -> dict:
    """
    下载单个PDF文件
    
    Args:
        row: 公告记录字典，包含pdf_url和local_pdf_path字段
        config: 配置字典
    
    Returns:
        更新后的记录，包含download_status和error_message字段
    """
    pdf_url = row["pdf_url"]
    local_path = Path(row["local_pdf_path"])
    
    try:
        # 使用配置的pdf_base_url构建正确的PDF链接
        response = request_with_retry(requests.Session(), "get", pdf_url, timeout=config["request"]["timeout_seconds"], headers={
            "User-Agent": config["request"]["user_agent"],
            "Referer": "https://www.cninfo.com.cn/new/fulltextSearch"
        })
        
        # 检查是否是PDF文件
        content = response.content
        if content[:4] == b"%PDF":
            # 创建目录并保存文件
            local_path.parent.mkdir(parents=True, exist_ok=True)
            with open(local_path, "wb") as f:
                f.write(content)
            
            row["download_status"] = "success"
            row["error_message"] = ""
        else:
            row["download_status"] = "failed"
            row["error_message"] = "返回的内容不是PDF文件"
    
    except Exception as e:
        row["download_status"] = "failed"
        row["error_message"] = str(e)
    
    return row


def crawl(config: dict) -> list[dict]:
    """
    爬虫主流程：查询公告 -> 下载PDF -> 保存元数据
    
    Args:
        config: 配置字典
    
    Returns:
        完整的公告记录列表
    """
    # 查询公告元数据
    rows = query_cninfo(config)
    
    if not rows:
        print("未获取到任何公告数据！")
        return rows
    
    print(f"\n共获取 {len(rows)} 条股权激励公告")
    
    # 下载PDF文件
    print(f"\n开始下载 {len(rows)} 个PDF文件到: {config['output']['pdf_dir']}/")
    success_count = 0
    for i, row in enumerate(rows):
        print(f"下载进度: {i+1}/{len(rows)} - {row['company_name']}", end="\r")
        row = download_pdf(row, config)
        if row["download_status"] == "success":
            success_count += 1
        time.sleep(config["request"].get("sleep_seconds", 1) / 2)
    
    print(f"\n\nPDF下载完成: 成功 {success_count}/{len(rows)}")
    
    # 保存元数据
    write_csv(config["output"]["metadata"], rows, FIELDS)
    print(f"元数据已保存至: {config['output']['metadata']}")
    
    return rows


# 配置参数
CONFIG = {
    "project_name": "cninfo_equity_incentive_analysis",
    "endpoint": "https://www.cninfo.com.cn/new/fulltextSearch/full",
    "pdf_base_url": "https://static.cninfo.com.cn",
    "keywords": ["股票期权激励计划", "股权激励计划"],
    "required_title_keywords": ["股票期权激励计划", "草案"],
    "target_industries": ["半导体", "电子", "计算机", "医药", "高端制造", "集成电路", "芯片", "软件", "医疗器械", "生物制药", "智能制造"],
    "date_range": {
        "start": "2021-01-01",
        "end": "2025-12-31"
    },
    "query": {
        "page_size": 50,
        "max_records": 200,
        "column": "szse",
        "tab_name": "fulltext",
        "title_exclude": ["注销", "终止", "作废", "回购", "取消", "调整", "变更", "修订", "补充", "更正", "问询", "自查表", "摘要", "投资者关系活动", "法律意见书", "独立财务顾问报告", "核查意见", "财务顾问", "法律意见", "核查报告", "独立董事意见", "监事会意见", "律师事务所", "证券公司", "独立", "之"]
    },
    "request": {
        "sleep_seconds": 2,
        "timeout_seconds": 30,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    },
    "output": {
        "metadata": "data/metadata/metadata.csv",
        "pdf_dir": "data/pdf"
    }
}

# 字段定义（对应proposal.md中的Metadata Database Schema）
FIELDS = [
    "doc_id", "stock_code", "company_name", "industry",
    "announcement_title", "announcement_type", "publish_date",
    "url", "pdf_url", "local_pdf_path",
    "source", "crawl_time", "download_status", "error_message"
]


if __name__ == "__main__":
    rows = crawl(CONFIG)
    print(f"\n爬取完成！共获取 {len(rows)} 条记录")
    
    # 简单统计
    success_count = sum(1 for r in rows if r["download_status"] == "success")
    print(f"PDF下载成功: {success_count} 个")
    print(f"PDF下载失败: {len(rows) - success_count} 个")
    
    # 按行业统计
    industry_counts = {}
    for row in rows:
        industry = row["industry"] or "其他"
        industry_counts[industry] = industry_counts.get(industry, 0) + 1
    
    print("\n按行业分布:")
    for industry, count in sorted(industry_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {industry}: {count}条")