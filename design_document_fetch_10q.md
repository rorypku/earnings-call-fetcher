# Fetch_10q 项目文档

1. 新建一个python脚本，调用earningscall api，获得config.py中每家target_companies的财报日期，具体参数设置如下
- api key：调用.env中EARNINGSCALL_API_KEY
- symbol：config.py中target_companies的股票代码
<earningscall api参考代码>
Get Earnings Events

URL Endpoint :https://v2.api.earningscall.biz/events
HTTP Verb :GET
Parameter :"apikey" - Your API Key is: "premium_MJ3hbK5JZ6hwohSSXT5h4g". Keep it secret, keep it safe.
Parameter :"exchange" - Valid values: "NYSE", "NASDAQ", "AMEX", "TSX", "TSXV" or "OTC".
Parameter :"symbol" - The ticker symbol.
Result :JSON Object
</earningscall api参考代码>

2. earningscall events的返回结果示例如下。根据返回结果建立新的json变量，参数包含公司名称，ticker，cik编号，每个events的year，quarter，conference_date。
<earningscall events返回结果示例>
{
  "company_name": "Apple Inc.",
  "events": [
    {
      "year": 2024,
      "quarter": 2,
      "conference_date": "2024-05-02T17:00:00.000-04:00"
    },
    {
      "year": 2024,
      "quarter": 1,
      "conference_date": "2024-02-01T17:00:00.000-05:00"
    }
  ]
}
</earningscall events返回结果示例>

3. 调用fmp api，查询公司在conference_date前后两天的sec filing，从中找到10-q文件的finalLink。具体参数设置如下：
- fmp api key：从.env中提取FMP_API_KEY
- cik：公司的cik编号
- 起始日期：conference_date前2天
- 终止日期：conference_date后两天

<fmp api参考代码>
#!/usr/bin/env python
try:
    # For Python 3.0 and later
    from urllib.request import urlopen
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
    return json.loads(data)

url = ("https://financialmodelingprep.com/stable/sec-filings-search/cik?cik=0000320193&from=2024-01-01&to=2024-03-01&apikey=YOUR_API_KEY")
print(get_jsonparsed_data(url))
</fmp api参考代码>
<fmp 返回结果示例>
[
	{
		"symbol": "AAPL",
		"cik": "0000320193",
		"filingDate": "2024-02-28 00:00:00",
		"acceptedDate": "2024-02-28 17:09:05",
		"formType": "8-K",
		"link": "https://www.sec.gov/Archives/edgar/data/320193/000114036124010155/0001140361-24-010155-index.htm",
		"finalLink": "https://www.sec.gov/Archives/edgar/data/320193/000114036124010155/ny20022580x1_image01.jpg"
	}
]
<fmp 返回结果示例>

4. 调用firecrawl api抓取上一步获得的finalLink，保存到'/Users/kai/Library/Mobile Documents/iCloud~md~obsidian/Documents/Company Research/{company name}/{company name_year_quarter_10q.md}'（比如'/Users/kai/Library/Mobile Documents/iCloud~md~obsidian/Documents/Company Research/Visa Inc./Visa Inc._2019_Q1_10q.md'）
<firecrawl api参考代码>
# Install with pip install firecrawl-py
from firecrawl import FirecrawlApp

app = FirecrawlApp(api_key='fc-41e655206f4b4459ab4085276ba2b13d')

response = app.scrape_url(url='https://www.sec.gov/Archives/edgar/data/320193/000032019324000006/aapl-20231230.htm', params={
	'formats': [ 'markdown' ],
})
</firecrawl api参考代码>