#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import requests
import argparse
from pathlib import Path
from dotenv import load_dotenv

import earningscall
from earningscall import get_company
from config import (
    API_REQUEST_DELAY,
    START_YEAR,
    START_QUARTER,
    END_YEAR,
    END_QUARTER,
    OUTPUT_DIR_NAME,
    TARGET_COMPANIES,
    CREATE_EMPTY_TRANSCRIPT
)

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='获取公司财报会议记录')
    
    parser.add_argument('--start-year', type=int, help='起始年份')
    parser.add_argument('--start-quarter', type=int, choices=[1, 2, 3, 4], help='起始季度')
    parser.add_argument('--end-year', type=int, help='结束年份')
    parser.add_argument('--end-quarter', type=int, choices=[1, 2, 3, 4], help='结束季度')
    parser.add_argument('--output-dir', type=str, help='输出目录名')
    parser.add_argument('--delay', type=float, help='API请求间隔(秒)')
    parser.add_argument('--timeout', type=int, default=10, help='API请求超时(秒)')
    parser.add_argument('--create-empty', action='store_true', help='创建空财报记录文件')
    parser.add_argument('--ticker', type=str, help='只处理指定的股票代码')
    
    return parser.parse_args()

def main():
    # 解析命令行参数
    args = parse_args()
    
    # 加载.env文件中的环境变量
    load_dotenv()
    
    # 设置API密钥
    api_key = os.getenv("EARNINGSCALL_API_KEY")
    if api_key:
        earningscall.api_key = api_key
    else:
        print("错误: 未设置API密钥。请在.env文件中设置EARNINGSCALL_API_KEY")
        return
    
    # 设置请求超时（秒）
    earningscall.timeout = args.timeout if args.timeout else 10
    
    # 设置代理
    http_proxy = os.getenv("HTTP_PROXY")
    https_proxy = os.getenv("HTTPS_PROXY")
    
    if http_proxy or https_proxy:
        # 清理HTTPS代理URL中可能存在的百分号编码问题
        if https_proxy and '%' in https_proxy:
            https_proxy = https_proxy.replace('%', '')
            print(f"已清理HTTPS代理URL: {https_proxy}")
        
        # 直接设置环境变量，这将被requests库自动使用
        if http_proxy:
            os.environ["HTTP_PROXY"] = http_proxy
        if https_proxy:
            os.environ["HTTPS_PROXY"] = https_proxy
        print(f"使用代理: HTTP={http_proxy}, HTTPS={https_proxy}")
    
    # 应用命令行参数覆盖配置
    start_year = args.start_year if args.start_year is not None else START_YEAR
    start_quarter = args.start_quarter if args.start_quarter is not None else START_QUARTER
    end_year = args.end_year if args.end_year is not None else END_YEAR
    end_quarter = args.end_quarter if args.end_quarter is not None else END_QUARTER
    output_dir_name = args.output_dir if args.output_dir else OUTPUT_DIR_NAME
    api_delay = args.delay if args.delay is not None else API_REQUEST_DELAY
    create_empty = args.create_empty if args.create_empty else CREATE_EMPTY_TRANSCRIPT
    
    # 创建输出目录
    output_dir = Path(output_dir_name)
    output_dir.mkdir(exist_ok=True)
    
    # 过滤目标公司
    target_companies = TARGET_COMPANIES
    if args.ticker:
        ticker = args.ticker.upper()
        target_companies = [company for company in TARGET_COMPANIES if company[1] == ticker]
        if not target_companies:
            print(f"错误: 在配置中未找到股票代码 {ticker}")
            return
    
    print(f"时间范围: {start_year}Q{start_quarter} - {end_year}Q{end_quarter}")
    print(f"输出目录: {output_dir_name}")
    print(f"API延迟: {api_delay}秒")
    print(f"API超时: {earningscall.timeout}秒")
    print(f"创建空记录: {create_empty}")
    print(f"开始处理{len(target_companies)}家公司的财报会议记录")
    
    success_count = 0
    failure_count = 0
    
    # 批量获取财报记录
    for company in target_companies:
        try:
            success = get_transcript(company, start_year, start_quarter, end_year, end_quarter, output_dir, api_delay, create_empty)
            if success:
                success_count += 1
            else:
                failure_count += 1
        except Exception as e:
            print(f"处理{company[1]}时发生未知错误: {str(e)}")
            failure_count += 1
    
    print("\n批量抓取完成:")
    print(f"总公司数: {len(target_companies)}")
    print(f"成功: {success_count}")
    print(f"失败: {failure_count}")

def get_transcript(company_info, start_year, start_quarter, end_year, end_quarter, output_dir, api_delay, create_empty):
    """获取指定公司从配置的起始季度到终止季度的财报会议记录"""
    # 根据公司信息元组长度解包相应的值
    if len(company_info) == 4:
        name, ticker, cik, exchange = company_info
    elif len(company_info) == 3:
        name, ticker, cik = company_info
        exchange = None
    else:
        name, ticker = company_info
        cik = None
        exchange = None
    
    print(f"正在处理: {name} ({ticker}){' CIK:'+cik if cik else ''}...")
    
    try:
        # 获取公司信息
        company = get_company(ticker.lower())
        
        # 设置目标时间范围
        target_periods = []
        for year in range(start_year, end_year + 1):
            # 确定当前年份的季度范围
            if year == start_year:
                start_q = start_quarter
            else:
                start_q = 1
                
            if year == end_year:
                end_q = end_quarter
            else:
                end_q = 4
                
            for quarter in range(start_q, end_q + 1):
                target_periods.append((year, quarter))
        
        # 创建公司目录
        events_found = False
        company_dir = output_dir / name
        company_dir.mkdir(exist_ok=True)
        
        # 逐个获取每个季度的财报会议记录
        for year, quarter in target_periods:
            max_retries = 5  # 增加重试次数
            retry_count = 0
            retry_delay = 2  # 初始重试延迟（秒）
            
            while retry_count < max_retries:
                try:
                    # 获取特定季度的财报会议记录
                    transcript = company.get_transcript(year=year, quarter=quarter, level=2)
                    
                    if transcript:
                        events_found = True
                        
                        # 从transcript中获取会议日期
                        # 添加安全检查，避免date属性不存在的错误
                        if hasattr(transcript, 'date') and transcript.date:
                            event_date = transcript.date.strftime("%Y-%m-%d")
                        else:
                            event_date = f"{year}-Q{quarter}"
                            
                        filename = f"{name}_{year}_Q{quarter}.md"
                        output_path = company_dir / filename
                        
                        # 如果文件已存在，跳过
                        if output_path.exists():
                            print(f"  跳过已存在的文件: {filename}")
                            break  # 跳出重试循环
                        
                        with open(output_path, 'w', encoding='utf-8') as f:
                            f.write(f"# {name} ({ticker}) 财报会议记录\n\n")
                            f.write(f"## 基本信息\n\n")
                            f.write(f"- **季度**: Q{quarter} {year}\n")
                            f.write(f"- **日期**: {event_date}\n")
                            if cik:
                                f.write(f"- **CIK**: {cik}\n")
                            if exchange:
                                f.write(f"- **交易所**: {exchange}\n")
                            f.write("\n---\n\n")
                            
                            # 添加每个发言人的详细信息和发言内容
                            if hasattr(transcript, 'speakers') and transcript.speakers:
                                f.write("## 会议内容\n\n")
                                for speaker in transcript.speakers:
                                    if hasattr(speaker, 'speaker_info') and speaker.speaker_info:
                                        speaker_name = speaker.speaker_info.name if hasattr(speaker.speaker_info, 'name') else '未知'
                                        speaker_title = speaker.speaker_info.title if hasattr(speaker.speaker_info, 'title') else '未知'
                                        f.write(f"**{speaker_name} - {speaker_title}**\n\n")
                                    else:
                                        f.write("**未知发言人**\n\n")
                                    
                                    if hasattr(speaker, 'text') and speaker.text:
                                        # 段落分割，提高可读性
                                        paragraphs = speaker.text.split('\n')
                                        for paragraph in paragraphs:
                                            if paragraph.strip():
                                                f.write(f"{paragraph}\n\n")
                                    else:
                                        f.write("*无内容*\n\n")
                            else:
                                f.write("## 会议内容\n\n*无发言记录可用*\n\n")
                                
                        print(f"  已保存: {filename}")
                    else:
                        print(f"  无法获取记录: Q{quarter} {year}")
                        
                        # 如果配置允许，创建空记录文件
                        if create_empty:
                            empty_filename = f"{name}_{year}_Q{quarter}_NO_DATA.md"
                            empty_path = company_dir / empty_filename
                            
                            with open(empty_path, 'w', encoding='utf-8') as f:
                                f.write(f"# {name} ({ticker}) 财报会议记录\n\n")
                                f.write(f"## 基本信息\n\n")
                                f.write(f"- **季度**: Q{quarter} {year}\n")
                                f.write(f"- **状态**: 未找到财报会议记录\n")
                                if cik:
                                    f.write(f"- **CIK**: {cik}\n")
                                if exchange:
                                    f.write(f"- **交易所**: {exchange}\n")
                                f.write("\n")
                            
                            print(f"  已创建空记录文件: {empty_filename}")
                    
                    # 成功获取，跳出重试循环
                    break
                
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.ReadTimeout, ConnectionResetError) as e:
                    retry_count += 1
                    if retry_count < max_retries:
                        print(f"  连接错误: {str(e)}, 第{retry_count}次重试, 等待{retry_delay}秒...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # 指数退避
                    else:
                        print(f"  获取 {ticker} Q{quarter} {year} 财报时连接错误，已达最大重试次数: {str(e)}")
                
                except Exception as e:
                    print(f"  获取 {ticker} Q{quarter} {year} 财报时出错: {str(e)}")
                    break  # 对于非连接错误，不重试
                
            # 添加延迟，避免API请求过于频繁
            time.sleep(api_delay)
        
        if not events_found:
            print(f"  没有找到{name} ({ticker})在指定时间范围内的财报会议记录")
        
        return True
    except Exception as e:
        print(f"  处理{ticker}时出错: {str(e)}")
        return False

if __name__ == "__main__":
    main()
