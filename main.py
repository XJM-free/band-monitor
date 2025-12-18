import feedparser
import requests
import urllib.parse
import os
from datetime import datetime
from time import mktime

# --- 配置区 ---

# 关键词列表
TARGETS = [
    {"name": "万能青年旅店", "keyword": "万能青年旅店 巡演 OR 演出 OR 音乐节"},
    {"name": "痛仰乐队", "keyword": "痛仰乐队 巡演 OR 演出 OR 音乐节"},
    # 你可以继续加，比如 {"name": "新裤子", "keyword": "新裤子 巡演"},
]

# Server酱 Key
SC_KEY = os.environ.get("SC_KEY")

# --- 核心代码 ---

def send_wechat(title, content):
    if not SC_KEY:
        print("⚠️ 未配置 Server酱 Key，无法推送")
        # 如果没有 Key，也在日志里打印一下内容，方便调试
        print("\n--- 模拟推送内容 ---\n" + content + "\n------------------")
        return
    
    url = f"https://sctapi.ftqq.com/{SC_KEY}.send"
    data = {"title": title, "desp": content}
    try:
        requests.post(url, data=data)
        print("✅ 微信推送已发送")
    except Exception as e:
        print(f"❌ 推送失败: {e}")

def check_google_news():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🌍 开始抓取 Google News (Top 5)...")
    
    msg_content = ""
    total_count = 0

    for item in TARGETS:
        encoded_keyword = urllib.parse.quote(item['keyword'])
        url = f"https://news.google.com/rss/search?q={encoded_keyword}&hl=zh-CN&gl=CN&ceid=CN:zh-CN"
        
        try:
            feed = feedparser.parse(url)
            
            # 乐队标题
            msg_content += f"### 🎸 {item['name']}\n"
            
            if not feed.entries:
                msg_content += "暂无相关资讯\n\n"
                continue

            # 只取前 5 条
            entries = feed.entries[:5]
            
            for entry in entries:
                title = entry.title
                link = entry.link
                
                # 处理时间
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_date = datetime.fromtimestamp(mktime(entry.published_parsed))
                    date_str = pub_date.strftime('%Y-%m-%d')
                    
                    # 判断是否是“今天/昨天”的新闻 (24小时内)
                    # 用来给前面的图标做区分
                    is_new = (datetime.now() - pub_date).days < 1
                    icon = "🔥" if is_new else "📄"
                else:
                    date_str = "未知日期"
                    icon = "📄"

                # 拼接 Markdown 格式
                # 格式：图标 [日期] 标题 (链接)
                msg_content += f"{icon} `{date_str}` [{title}]({link})\n\n"
                total_count += 1
            
            msg_content += "---\n" # 分割线

        except Exception as e:
            print(f"❌ 出错 [{item['name']}]: {e}")
            msg_content += f"获取失败: {e}\n\n"

    # 只要抓到了数据（哪怕全是旧的），都推送
    if total_count > 0:
        print("🚀 生成日报成功，正在推送...")
        send_wechat(f"🎸 乐队巡演日报 ({datetime.now().strftime('%m-%d')})", msg_content)
    else:
        print("💤 没有任何数据，不推送")

if __name__ == "__main__":
    check_google_news()
