# BOSS-AI-R 项目

老板口袋军师·实时谈判版 — 后端服务

## 快速启动

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
python -m api.app
# 或
uvicorn api.app:app --reload --port 8000
```

## 项目结构

```
sol_pi_engram_evolution/
├── api/                    # FastAPI 应用
│   ├── app.py              # 主入口 + WebSocket
│   └── __init__.py
├── modules/                # 核心业务模块
│   ├── prompt_decider.py   # 提示决策器（P0）
│   ├── compliance.py       # 合规引擎（P0）
│   ├── realtime_audio.py   # 实时音频（P1）
│   ├── acoustic_emotion.py # 声学情绪（P2）
│   └── billing.py          # 订阅计费（P1）
├── ui/                     # 前端
│   ├── templates/          # Jinja2 模板
│   └── static/             # CSS/JS/图片
├── tests/                  # 测试
├── config.py               # 统一配置
├── logger.py               # 日志系统
└── requirements.txt        # 依赖
```

## API 端点

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | /api/v1/recording/start | 开始录音 |
| POST | /api/v1/recording/{id}/stop | 结束录音 |
| GET | /api/v1/recording/{id}/status | 录音状态 |
| WS | /ws/realtime/{id} | WebSocket 实时通信 |
| POST | /api/v1/compliance/check | 合规检查 |
| GET | /api/v1/compliance/summary/{id} | 合规摘要 |
| POST | /api/v1/subscription | 创建订阅 |
| GET | /api/v1/quota/{id} | 配额信息 |
| GET | /api/v1/cost/{id} | 成本明细 |
| GET | /health | 健康检查 |
| GET | /api/v1/stats | 系统统计 |

## 端口

- API: http://localhost:8000
- 文档: http://localhost:8000/docs
- 主页: http://localhost:8000/
