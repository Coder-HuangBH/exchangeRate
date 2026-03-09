# exchangeRate

招行汇率查询与监控工具，支持自动监控美元汇率并通过飞书推送通知。

## 功能特性

- 自动获取招商银行最新美元汇率
- 监控现汇卖出价（买入美元参考价）和现汇买入价（卖出美元参考价）
- 支持只配置买入或卖出其中一个阈值
- 当汇率达到设定阈值时，通过飞书机器人推送通知
- 触发通知后自动调整阈值，调整幅度可配置，避免重复提醒
- 支持 GitHub Actions 定时执行（每10分钟）

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/your-username/exchangeRate.git
cd exchangeRate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
export FEISHU_WEBHOOK="https://open.feishu.cn/open-apis/bot/v2/hook/your-webhook"
export BUY_THRESHOLD="720"
export SELL_THRESHOLD="710"
export BUY_ADJUST_STEP="1"
export SELL_ADJUST_STEP="1"
```

### 4. 运行脚本

```bash
python main.py
```

## GitHub Actions 部署

### 1. 配置 Secrets

在 GitHub 仓库中配置以下 Secrets：

| Secret 名称 | 说明 | 示例 |
|------------|------|------|
| `FEISHU_WEBHOOK` | 飞书机器人 Webhook 地址 | `https://open.feishu.cn/open-apis/bot/v2/hook/xxx` |
| `PAT_TOKEN` | GitHub Personal Access Token（用于更新变量） | `ghp_xxxx` |

#### 创建 PAT_TOKEN 步骤

1. 登录 GitHub → **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
2. 点击 **Generate new token (classic)**
3. 勾选 `repo` 权限（完整仓库访问权限）
4. 生成并复制 Token
5. 在仓库 Secrets 中添加 `PAT_TOKEN`

### 2. 配置 Variables

在 GitHub 仓库中配置以下 Variables（买入和卖出阈值至少配置一个）：

| Variable 名称 | 说明 | 是否必填 | 默认值 |
|--------------|------|---------|--------|
| `BUY_THRESHOLD` | 买入阈值（现汇卖出价目标值） | 否 | 无 |
| `SELL_THRESHOLD` | 卖出阈值（现汇买入价目标值） | 否 | 无 |
| `BUY_ADJUST_STEP` | 买入阈值调整幅度 | 否 | 1 |
| `SELL_ADJUST_STEP` | 卖出阈值调整幅度 | 否 | 1 |

### 3. 启用 GitHub Actions

推送代码到仓库后，GitHub Actions 会自动每10分钟执行一次检查。也可以手动触发：

1. 进入仓库 **Actions** 页面
2. 选择 **Check Exchange Rate** 工作流
3. 点击 **Run workflow**

## 飞书机器人配置

### 1. 创建飞书群机器人

1. 打开飞书群聊
2. 点击群设置 → 群机器人 → 添加机器人
3. 选择 **自定义机器人**
4. 复制生成的 Webhook 地址

### 2. 配置 Webhook

将 Webhook 地址配置到 GitHub Secrets 中的 `FEISHU_WEBHOOK`。

## 通知示例

```
汇率提醒
当前时间：2026-03-06 10:00:00

美元现汇卖出价：718.50
目标买入价：720.00
✅ 已达到买入目标！

美元现汇买入价：712.30
目标卖出价：710.00
```

## 汇率说明

| 字段 | 说明 | 用途 |
|------|------|------|
| `rthOfr` | 现汇卖出价 | 银行卖出美元的价格，我们买入美元时参考 |
| `rthBid` | 现汇买入价 | 银行买入美元的价格，我们卖出美元时参考 |

## 阈值调整逻辑

- 当 `rthOfr <= BUY_THRESHOLD` 时，触发买入提醒，并将 `BUY_THRESHOLD` 降低 `BUY_ADJUST_STEP`
- 当 `rthBid >= SELL_THRESHOLD` 时，触发卖出提醒，并将 `SELL_THRESHOLD` 提高 `SELL_ADJUST_STEP`

这样可以避免汇率持续满足条件时重复发送通知。

## 使用场景示例

### 只监控买入机会

只配置 `BUY_THRESHOLD`，不配置 `SELL_THRESHOLD`：

```
BUY_THRESHOLD=720
```

### 只监控卖出机会

只配置 `SELL_THRESHOLD`，不配置 `BUY_THRESHOLD`：

```
SELL_THRESHOLD=710
```

### 自定义调整幅度

希望触发后阈值变化更大：

```
BUY_THRESHOLD=720
BUY_ADJUST_STEP=5
SELL_THRESHOLD=710
SELL_ADJUST_STEP=5
```

## 注意事项

1. GitHub Actions 的定时任务可能有几分钟的延迟
2. 招行 API 可能会更新，如遇问题请检查 API 返回格式
3. 请确保飞书机器人未被移除或禁用
4. 买入和卖出阈值至少需要配置一个，否则脚本会直接退出
