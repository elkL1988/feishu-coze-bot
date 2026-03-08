# 飞书-扣子智能体中转服务
# 依赖：flask requests
from flask import Flask, request, jsonify
import requests
import json
import os

# 初始化Flask应用
app = Flask(__name__)

# 配置信息（优先从环境变量读取，也可直接替换为你的实际值）
# 替换规则：把引号内的示例值改成你自己的飞书Webhook和扣子Token
FEISHU_WEBHOOK = os.getenv("FEISHU_WEBHOOK", "https://open.feishu.cn/open-apis/bot/v2/hook/111dceb6-1b3b-4af6-8732-69b216c970ac")
COZE_API_URL = "https://sp94cf59z9.coze.site/stream_run"  # 你的扣子智能体调用地址
COZE_API_TOKEN = os.getenv("COZE_API_TOKEN", "eyJhbGciOiJSUzI1NiIsImtpZCI6IjIzMjMwOGIyLWJkMTMtNGE4Mi1iZWJmLTcxMWZiMTQ2NThiOCJ9.eyJpc3MiOiJodHRwczovL2FwaS5jb3plLmNuIiwiYXVkIjpbIlBlQkVRRlgxS2RTamJJbElRSnVDMkdzYm82TWVnNjBBIl0sImV4cCI6ODIxMDI2Njg3Njc5OSwiaWF0IjoxNzcyOTMwNzM1LCJzdWIiOiJzcGlmZmU6Ly9hcGkuY296ZS5jbi93b3JrbG9hZF9pZGVudGl0eS9pZDo3NjE0NDU2NjgxNjI3Mzg1ODU2Iiwic3JjIjoiaW5ib3VuZF9hdXRoX2FjY2Vzc190b2tlbl9pZDo3NjE0Njc5NTI0OTUyNzY4NTY2In0.GUoAKKgQTIgBspuTggd-s2DF2gYPd8GDns7riCrtTclZG1FVElD796sSEHr05zTdzczDVuVwRZA8yI7eJIOQlgMyTLukHT9aMVQWI7WBfXBS4tu5DkKEeaW5ieBrYF-wDn0Aai2xwhYD8aFl5W4Z8yxriVn8Apz8Wh2u_pj5NBCDhvHg8iF6WdDkM1d-jo-szm7p-tQwcK4MZGOMq2GvZa_-vG_GXrA-vFCV15ZeUbHT9ihEvN8mVGPuffTEKQ4Lnn6lc_f7R65cOHWjh1WUYgBDahOeyCnfqbnecwGpp4KrdXIgwqsmCV9DB2qc1w4J4ShtZixr1l783V4GErSq0g")
BOT_NAME = "@数据理性AI助手"  # 你的飞书机器人名称

# 处理飞书消息回调的核心接口
@app.route("/webhook/feishu", methods=["POST"])
def feishu_webhook():
    try:
        # 接收飞书的POST数据
        data = request.get_json()
        
        # 处理飞书的验证请求（必须保留，否则回调地址验证失败）
        if "challenge" in data:
            return jsonify({"challenge": data["challenge"]})
        
        # 解析并清洗用户消息（去掉@机器人的部分）
        msg_content = data.get("text", {}).get("content", "").strip()
        msg_content = msg_content.replace(BOT_NAME, "").strip()
        
        # 如果消息为空，直接返回成功
        if not msg_content:
            return jsonify({"status": "success"})
        
        # 调用扣子智能体获取回复
        ai_reply = call_coze_ai(msg_content)
        
        # 把AI回复发送回飞书群
        send_to_feishu(ai_reply)
        
        return jsonify({"status": "success"})
    
    except Exception as e:
        # 捕获所有异常，避免服务崩溃
        print(f"处理消息时出错：{str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

# 调用扣子智能体API的函数
def call_coze_ai(prompt):
    try:
        # 配置请求头
        headers = {
            "Authorization": f"Bearer {COZE_API_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # 扣子编程模式的标准请求格式
        payload = {
            "inputs": [{"name": "query", "value": prompt}],
            "stream": False  # 非流式返回，适合群聊场景
        }
        
        # 发送请求到扣子智能体
        response = requests.post(
            COZE_API_URL,
            json=payload,
            headers=headers,
            timeout=30  # 设置30秒超时
        )
        
        # 打印返回结果，方便排查问题
        print(f"扣子API返回：{response.text}")
        
        # 解析返回结果
        result = response.json()
        return result.get("data", {}).get("content", "AI暂时无法回复，请稍后再试")
    
    except Exception as e:
        error_msg = f"调用扣子智能体失败：{str(e)}"
        print(error_msg)
        return error_msg

# 发送消息到飞书群的函数
def send_to_feishu(content):
    try:
        # 飞书自定义机器人的消息格式
        payload = {
            "msg_type": "text",
            "content": {"text": content}
        }
        
        # 发送POST请求到飞书Webhook
        response = requests.post(
            FEISHU_WEBHOOK,
            json=payload,
            timeout=10
        )
        
        # 打印发送结果
        print(f"发送到飞书结果：{response.status_code} - {response.text}")
        
    except Exception as e:
        print(f"发送到飞书失败：{str(e)}")

# 启动服务（适配Railway的端口配置）
if __name__ == "__main__":
    # Railway会自动分配端口，从环境变量读取
    port = int(os.getenv("PORT", 5000))
    # 0.0.0.0表示监听所有网络地址，允许公网访问
    app.run(host="0.0.0.0", port=port, debug=False)  # 生产环境关闭debug