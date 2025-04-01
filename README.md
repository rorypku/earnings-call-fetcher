# 财报电话会议记录抓取工具

这个工具用于批量抓取美国上市公司过去一年内的财报电话会议记录。

## 功能

- 自动从配置文件中提取公司信息
- 批量获取每家公司指定时间范围内的所有财报电话会议记录
- 将记录以Markdown格式保存在公司专属文件夹中
- 避免重复下载已存在的记录
- 自动处理API请求频率限制
- 支持通过代理服务器访问API
- 支持命令行参数自定义下载范围和配置

## 安装

1. 确保已安装Python 3.8或更高版本
2. 克隆此仓库:
```bash
git clone https://github.com/yourusername/earnings-call-fetcher.git
cd earnings-call-fetcher
```

3. 安装所需依赖:
```bash
pip install -r requirements.txt
```

## 配置

在项目根目录创建`.env`文件进行配置，或使用以下模板:

```env
# API密钥设置
EARNINGSCALL_API_KEY=your_api_key_here

# 代理设置（如需）
HTTP_PROXY=http://127.0.0.1:10080
HTTPS_PROXY=http://127.0.0.1:10080
```

同时，你可以在`config.py`文件中配置以下参数:
- 起始和结束年份与季度
- API请求间隔时间
- 输出目录
- 目标公司列表

## 使用方法

### 基本使用

配置完成后，直接运行脚本:

```bash
python fetch_earningscall.py
```

### 高级选项

脚本支持多种命令行参数来覆盖默认配置:

```bash
python fetch_earningscall.py --start-year 2022 --start-quarter 1 --end-year 2023 --end-quarter 4 --output-dir transcripts --delay 2 --timeout 15
```

可用的命令行参数:
- `--start-year`: 起始年份
- `--start-quarter`: 起始季度 (1-4)
- `--end-year`: 结束年份
- `--end-quarter`: 结束季度 (1-4)
- `--output-dir`: 输出目录
- `--delay`: API请求间隔(秒)
- `--timeout`: API请求超时(秒)
- `--create-empty`: 当没有找到记录时创建空文件
- `--ticker`: 只处理指定的股票代码

## 文件命名格式

下载的文件将使用以下格式命名:
```
{公司名}_{年份}_Q{季度}.md
```

示例: `Apple Inc._2023_Q3.md`

## 开发

### 项目结构

```
.
├── fetch_earningscall.py  # 主程序
├── config.py              # 配置文件
├── .env                   # 环境变量
├── requirements.txt       # 依赖列表
└── README.md              # 说明文档
```

## 注意事项

- 默认情况下，EarningsCall API可能有访问限制，请查阅API文档了解详情
- 需要在[earningscall.biz](https://earningscall.biz/api-pricing)注册并获取API密钥
- 处理大量公司可能需要较长时间，脚本会在每次API请求之间添加延迟以避免请求过于频繁
- 如果您的网络环境需要使用代理，请确保在`.env`文件中正确配置代理信息

## 许可证

[MIT](LICENSE)

## 贡献

欢迎提交问题和改进建议!