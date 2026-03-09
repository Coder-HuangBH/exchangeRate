import os
import json
import requests
from datetime import datetime, timezone, timedelta

API_URL = "https://fx.cmbchina.com/api/v1/fx/rate"
BEIJING_TZ = timezone(timedelta(hours=8))

def get_beijing_time():
    return datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')

def get_env_float(key, default=None):
    value = os.environ.get(key, "")
    return float(value) if value.strip() else default

FEISHU_WEBHOOK = os.environ.get("FEISHU_WEBHOOK", "").strip() or None
BUY_THRESHOLD = get_env_float("BUY_THRESHOLD")
SELL_THRESHOLD = get_env_float("SELL_THRESHOLD")
BUY_ADJUST_STEP = get_env_float("BUY_ADJUST_STEP", 1)
SELL_ADJUST_STEP = get_env_float("SELL_ADJUST_STEP", 1)
GITHUB_TOKEN = os.environ.get("PAT_TOKEN") or os.environ.get("GITHUB_TOKEN")
GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY")


def get_exchange_rate():
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        for item in data.get("body", []):
            if item.get("ccyNbr") == "美元":
                return {
                    "rthOfr": float(item.get("rthOfr", 0)),
                    "rthBid": float(item.get("rthBid", 0)),
                }
        return None
    except Exception as e:
        print(f"获取汇率失败: {e}")
        send_feishu_notification(f"获取汇率失败: {e}")
        return None


def send_feishu_notification(message):
    if not FEISHU_WEBHOOK:
        print("未配置飞书webhook")
        return False
    try:
        payload = {
            "msg_type": "text",
            "content": {"text": message}
        }
        response = requests.post(
            FEISHU_WEBHOOK,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=10
        )
        response.raise_for_status()
        print("飞书通知发送成功")
        return True
    except Exception as e:
        print(f"发送飞书通知失败: {e}")
        return False


def update_github_variable(variable_name, new_value):
    if not GITHUB_TOKEN or not GITHUB_REPOSITORY:
        print("未配置GitHub Token或仓库信息，无法更新变量")
        return False
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/actions/variables/{variable_name}"
        print(f"请求URL: {url}, GITHUB_REPOSITORY: {GITHUB_REPOSITORY}")
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        data = {"name": variable_name, "value": str(new_value)}
        response = requests.patch(url, headers=headers, json=data, timeout=10)
        if response.status_code == 204:
            print(f"成功更新变量 {variable_name} 为 {new_value}")
            return True
        else:
            print(f"更新变量失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"更新GitHub变量失败: {e}")
        return False


def main():
    print(f"开始执行汇率检查 - {get_beijing_time()}")
    print(f"买入阈值: {BUY_THRESHOLD}, 卖出阈值: {SELL_THRESHOLD}")
    print(f"买入调整幅度: {BUY_ADJUST_STEP}, 卖出调整幅度: {SELL_ADJUST_STEP}")
    
    if BUY_THRESHOLD is None and SELL_THRESHOLD is None:
        print("未配置任何阈值，退出")
        return
    
    rate_data = get_exchange_rate()
    if not rate_data:
        print("未获取到美元汇率数据")
        return
    
    rthOfr = rate_data["rthOfr"]
    rthBid = rate_data["rthBid"]
    
    print(f"当前美元现汇卖出价: {rthOfr}")
    print(f"当前美元现汇买入价: {rthBid}")
    
    should_notify = False
    update_results = []
    notification_lines = [
        "汇率提醒",
        f"当前时间：{get_beijing_time()}",
        "",
    ]
    
    notification_lines.append(f"美元现汇卖出价：{rthOfr}")
    if BUY_THRESHOLD is not None:
        notification_lines.append(f"目标买入价：{BUY_THRESHOLD}")
        
        if rthOfr <= BUY_THRESHOLD:
            notification_lines.append("✅ 已达到买入目标！")
            should_notify = True
            new_buy_threshold = BUY_THRESHOLD - BUY_ADJUST_STEP
            success = update_github_variable("BUY_THRESHOLD", new_buy_threshold)
            update_results.append(f"买入阈值更新: {BUY_THRESHOLD} → {new_buy_threshold} ({'成功' if success else '失败'})")
    
    notification_lines.append("")
    notification_lines.append(f"美元现汇买入价：{rthBid}")
    if SELL_THRESHOLD is not None:
        notification_lines.append(f"目标卖出价：{SELL_THRESHOLD}")
        
        if rthBid >= SELL_THRESHOLD:
            notification_lines.append("✅ 已达到卖出目标！")
            should_notify = True
            new_sell_threshold = SELL_THRESHOLD + SELL_ADJUST_STEP
            success = update_github_variable("SELL_THRESHOLD", new_sell_threshold)
            update_results.append(f"卖出阈值更新: {SELL_THRESHOLD} → {new_sell_threshold} ({'成功' if success else '失败'})")
    
    if should_notify:
        if update_results:
            notification_lines.append("")
            notification_lines.append("变量更新结果：")
            notification_lines.extend(update_results)
        message = "\n".join(notification_lines)
        send_feishu_notification(message)
    else:
        print("当前汇率未达到目标")


if __name__ == "__main__":
    main()
