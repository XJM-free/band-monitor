import feedparser
import requests
import os
import re
from datetime import datetime
from time import mktime

# --- 配置区 ---
SC_KEY = os.environ.get("SC_KEY")

# --- 辅助函数 ---

def get_band_list():
    """读取 bands.txt (格式: 名字,UID)"""
    bands = []
    try:
        if not os.path.exists('bands.txt'):
            print("❌ 错误: 找不到 bands.txt 文件")
            return []
            
        with open('bands.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines:
                parts = line.strip().split(',')
                if len(parts) >= 2:
                    bands.append({
                        "name": parts[0].strip(),
                        "uid": parts[1].strip()
                    })
        print(f"📋 已加载 {len(bands)} 个乐队配置")
        return bands
    except Exception as e:
        print(f"❌ 读取文件出错: {e}")
        return []

def clean_html(raw_html):
    """去除微博内容的 HTML 标签，仅保留文字"""
    if not raw_html: return ""
    cleanr = re.compile('<.*?>')
    text = re.sub(cleanr, '', raw_html)
    # 去除多余空行
    return "\n".join([line.strip() for line in text.splitlines() if line.strip()])[:120] + "..."

def send_wechat(title, content):
    """发送微信推送"""
    if not SC_KEY:
        print("⚠️ 未配置 Server酱 Key，跳过推送")
        return
    
    url = f"https://sctapi.ftqq.com/{SC_KEY}.send"
    data = {"title": title, "desp": content}
    try:
        response = requests.post(url, data=data)
        print(f"✅ 微信推送请求已发送 (状态码: {response.status_code})")
    except Exception as e:
        print(f"❌ 推送失败: {e}")

# --- 核心逻辑 (强制抓取版) ---

def check_weibo_force():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔴 开始执行强制抓取测试...")
    
    targets = get_band_list()
    if not targets:
        return

    msg_content = ""
    total_count = 0
    
    # RSSHub 地址 (如果 rsshub.app 连不上，可以尝试换成 rsshub.rssfeed.jp)
    base_url = "https://rsshub.app/weibo/user/"

    for item in targets:
        url = base_url + item['uid']
        print(f"🔍 正在连接: {item['name']} ... ", end="")
        
        try:
            # 增加超时设置，防止卡死
            feed = feedparser.parse(url)
            
            if feed.entries:
                print(f"✅ 获取成功 (最新一条)")
                
                # --- 强制取第一条 (最新的一条) ---
                entry = feed.entries[0]
                
                # 处理内容
                content = clean_html(entry.description)
                link = entry.link
                
                # 处理时间
                if hasattr(entry, 'published_parsed'):
                    pub_date = datetime.fromtimestamp(mktime(entry.published_parsed))
                    date_str = pub_date.strftime('%Y-%m-%d %H:%M')
                else:
                    date_str = "未知时间"

                # 拼接到日报里
                msg_content += f"### 🎸 {item['name']}\n"
                msg_content += f"📅 `{date_str}`\n📝 {content}\n🔗 [点击查看微博]({link})\n\n---\n"
                total_count += 1
                
            else:
                print("⚠️ 无内容 (可能被反爬或该用户无微博)")

        except Exception as e:
            print(f"❌ 连接错误: {e}")

    # --- 结果处理 ---
    if total_count > 0:
        print(f"🚀 抓取完成，共 {total_count} 条，正在推送...")
        header = f"🎸 乐队微博测试日报 ({datetime.now().strftime('%H:%M')})"
        send_wechat(header, msg_content)
    else:
        print("💤 未抓取到任何数据，请检查网络或 RSSHub 节点状态")

if __name__ == "__main__":
    check_weibo_force()
