#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import datetime
import time
from urllib.request import urlopen
import certifi
from firecrawl import FirecrawlApp
from dotenv import load_dotenv
import logging
from pathlib import Path
from config import TARGET_COMPANIES, OUTPUT_DIR_NAME, API_REQUEST_DELAY

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# 获取API密钥
EARNINGSCALL_API_KEY = os.getenv("EARNINGSCALL_API_KEY")
FMP_API_KEY = os.getenv("FMP_API_KEY")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")

# 创建Firecrawl应用实例
firecrawl_app = FirecrawlApp(api_key=FIRECRAWL_API_KEY)

def get_jsonparsed_data(url):
    """
    获取并解析JSON数据
    """
    try:
        response = urlopen(url, cafile=certifi.where())
        data = response.read().decode("utf-8")
        return json.loads(data)
    except Exception as e:
        logger.error(f"获取JSON数据失败: {e}")
        return None

def get_earnings_events(ticker, exchange):
    """
    调用earningscall API获取公司的财报日期
    """
    url = f"https://v2.api.earningscall.biz/events?apikey={EARNINGSCALL_API_KEY}&symbol={ticker}&exchange={exchange}"
    
    logger.info(f"获取 {ticker} (交易所: {exchange}) 的财报日期...")
    data = get_jsonparsed_data(url)
    time.sleep(API_REQUEST_DELAY)  # 添加延迟，避免API限制
    
    if not data:
        logger.warning(f"未能获取 {ticker} 的财报日期")
        return None
    
    return data

def process_earnings_data(earnings_data, company_name, ticker, cik):
    """
    处理earningscall API返回的数据，生成结构化的JSON数据
    """
    if not earnings_data or "events" not in earnings_data:
        logger.warning(f"未找到 {ticker} 的财报事件数据")
        return None
    
    structured_data = {
        "company_name": company_name,
        "ticker": ticker,
        "cik": cik,
        "events": []
    }
    
    for event in earnings_data.get("events", []):
        if "year" in event and "quarter" in event and "conference_date" in event:
            structured_data["events"].append({
                "year": event["year"],
                "quarter": event["quarter"],
                "conference_date": event["conference_date"]
            })
    
    return structured_data

def get_sec_filings(cik, start_date, end_date):
    """
    调用FMP API获取SEC文件信息
    """
    url = f"https://financialmodelingprep.com/stable/sec-filings-search/cik?cik={cik}&from={start_date}&to={end_date}&apikey={FMP_API_KEY}"
    
    logger.info(f"获取CIK {cik} 在 {start_date} 至 {end_date} 的SEC文件...")
    data = get_jsonparsed_data(url)
    time.sleep(API_REQUEST_DELAY)  # 添加延迟，避免API限制
    
    if not data:
        logger.warning(f"未能获取 CIK {cik} 的SEC文件信息")
        return []
    
    return data

def find_10q_filing(filings, quarter):
    """
    从SEC文件列表中找到10-Q或10-K表格
    对于Q4季度，寻找10-K文件，其他季度寻找10-Q文件
    """
    # 对于Q4，我们寻找10-K表格
    if quarter == 4:
        form_type = "10-K"
    else:
        form_type = "10-Q"
    
    for filing in filings:
        if filing.get("formType") == form_type and "finalLink" in filing:
            return filing, form_type
    
    return None, None

def scrape_and_save_10q(company_name, year, quarter, final_link, form_type="10-Q"):
    """
    使用Firecrawl抓取10-Q/10-K文件并保存为Markdown
    """
    # 创建保存目录
    company_dir = os.path.join(OUTPUT_DIR_NAME, company_name)
    os.makedirs(company_dir, exist_ok=True)
    
    # 创建文件路径
    file_path = os.path.join(company_dir, f"{company_name}_{year}_Q{quarter}_{form_type.lower()}.md")
    
    # 检查文件是否已存在
    if os.path.exists(file_path):
        logger.info(f"文件已存在，跳过: {file_path}")
        return True
    
    logger.info(f"抓取 {company_name} {year} Q{quarter} 的{form_type}文件...")
    
    try:
        response = firecrawl_app.scrape_url(
            url=final_link, 
            params={
                'formats': ['markdown'],
            }
        )
        
        if not response or 'markdown' not in response:
            logger.error(f"抓取 {final_link} 失败")
            return False
        
        # 保存Markdown内容
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(response['markdown'])
        
        logger.info(f"已保存 {file_path}")
        return True
    
    except Exception as e:
        logger.error(f"抓取或保存{form_type}文件失败: {e}")
        return False

def process_company(company_name, ticker, cik, exchange):
    """
    处理单个公司的所有财报和10-Q/10-K文件
    """
    logger.info(f"开始处理公司: {company_name} ({ticker})")
    
    # 获取财报事件
    earnings_data = get_earnings_events(ticker, exchange)
    if not earnings_data:
        return
    
    # 处理财报数据
    structured_data = process_earnings_data(earnings_data, company_name, ticker, cik)
    if not structured_data:
        return
    
    logger.info(f"找到 {len(structured_data['events'])} 个财报事件")
    
    # 处理每个财报事件
    for event in structured_data["events"]:
        year = event["year"]
        quarter = event["quarter"]
        conference_date = event["conference_date"]
        
        logger.info(f"处理 {company_name} {year} Q{quarter} 财报")
        
        # 确定表格类型和检查文件是否已存在
        form_type = "10-K" if quarter == 4 else "10-Q"
        file_path = os.path.join(OUTPUT_DIR_NAME, company_name, f"{company_name}_{year}_Q{quarter}_{form_type.lower()}.md")
        
        # 如果文件已存在，跳过
        if os.path.exists(file_path):
            logger.info(f"文件已存在，跳过: {file_path}")
            continue
        
        # 解析会议日期
        conf_date = datetime.datetime.fromisoformat(conference_date.replace('Z', '+00:00'))
        
        # 计算查询日期范围（从会议日期前15天到会议日期后15天）
        start_date = (conf_date - datetime.timedelta(days=5)).strftime("%Y-%m-%d")
        end_date = (conf_date + datetime.timedelta(days=30)).strftime("%Y-%m-%d")
        
        # 获取SEC文件
        filings = get_sec_filings(cik, start_date, end_date)
        
        # 查找10-Q或10-K文件
        filing_result, actual_form_type = find_10q_filing(filings, quarter)
        
        if filing_result:
            logger.info(f"找到 {company_name} {year} Q{quarter} 的{actual_form_type}文件")
            # 抓取并保存文件
            scrape_and_save_10q(company_name, year, quarter, filing_result["finalLink"], actual_form_type)
        else:
            logger.warning(f"未找到 {company_name} {year} Q{quarter} 的{form_type}文件")

def main():
    logger.info("开始获取公司10-Q财报")
    
    for company in TARGET_COMPANIES:
        company_name, ticker, cik, exchange = company
        process_company(company_name, ticker, cik, exchange)
        time.sleep(API_REQUEST_DELAY)  # 添加延迟，避免API限制
    
    logger.info("所有公司处理完成")

if __name__ == "__main__":
    main() 