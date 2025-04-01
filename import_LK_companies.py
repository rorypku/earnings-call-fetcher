#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import os

def extract_companies_from_md(file_path):
    """从markdown文件中提取公司名称、股票代码、CIK编号和交易所信息"""
    companies = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 使用正则表达式匹配公司名称、股票代码、CIK编号和交易所信息
    # 格式: • Company Name (TICKER) - description - cik:0001234567 - EXCHANGE
    pattern = r'•\s+(.*?)\s+\((.*?)\)\s+-\s+(.*?)cik:(\d+)(?:\s+-\s+([A-Z]+))?'
    matches = re.finditer(pattern, content)
    
    for match in matches:
        company_name = match.group(1).strip()
        ticker = match.group(2).strip()
        cik = match.group(4).strip()
        # 确保CIK是10位数字，不足前面补0
        cik = cik.zfill(10)
        # 提取交易所信息，如果不存在则设为空字符串
        exchange = match.group(5).strip() if match.group(5) else ""
        companies.append((company_name, ticker, cik, exchange))
    
    return companies

def update_config_file(config_path, companies):
    """更新config.py文件中的TARGET_COMPANIES变量"""
    with open(config_path, 'r', encoding='utf-8') as f:
        config_content = f.read()
    
    # 构建新的TARGET_COMPANIES内容
    new_companies_str = "TARGET_COMPANIES = [\n"
    for company, ticker, cik, exchange in companies:
        new_companies_str += f'    ("{company}", "{ticker}", "{cik}", "{exchange}"),\n'
    new_companies_str += "] "
    
    # 使用正则表达式替换TARGET_COMPANIES部分
    pattern = r'TARGET_COMPANIES\s*=\s*\[\s*(?:\(".*?",\s*".*?",\s*".*?"\),\s*)*(?:\(".*?",\s*".*?",\s*".*?",\s*".*?"\),\s*)*(?:#[^\n]*\n)*\s*\]\s*'
    updated_content = re.sub(pattern, new_companies_str, config_content)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)

def main():
    # 文件路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    md_file = os.path.join(script_dir, "list_LK.md")
    config_file = os.path.join(script_dir, "config.py")
    
    # 确保文件存在
    if not os.path.exists(md_file):
        print(f"错误: 找不到文件 {md_file}")
        return
    
    if not os.path.exists(config_file):
        print(f"错误: 找不到文件 {config_file}")
        return
    
    # 提取公司信息
    companies = extract_companies_from_md(md_file)
    print(f"从list_LK.md中提取了 {len(companies)} 家公司")
    
    # 备份config文件
    backup_file = config_file + ".bak"
    with open(config_file, 'r', encoding='utf-8') as src:
        with open(backup_file, 'w', encoding='utf-8') as dst:
            dst.write(src.read())
    print(f"已创建配置文件备份: {backup_file}")
    
    # 更新config文件
    update_config_file(config_file, companies)
    print(f"已成功更新 {config_file} 中的TARGET_COMPANIES")

if __name__ == "__main__":
    main() 