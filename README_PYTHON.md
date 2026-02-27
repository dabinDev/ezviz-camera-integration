# 萤石摄像头客户端 Python 接入示例

## 快速开始

1. 安装依赖
```bash
pip install -r requirements.txt
```

2. 配置你的 AppKey/AppSecret
编辑 `main.py`，替换：
```python
APP_KEY = "YOUR_APP_KEY"
APP_SECRET = "YOUR_APP_SECRET"
```

3. 运行
```bash
python main.py
```

## 文件说明

- `ezviz_auth.py` - 获取 AccessToken
- `ezviz_device.py` - 获取设备列表和直播地址
- `ezviz_player.py` - 拉流播放封装（OpenCV）
- `main.py` - 完整可运行示例
- `requirements.txt` - Python 依赖

## 注意事项

- 如返回 `ezopen://` 地址，需安装 FFmpeg 并转码
- AccessToken 有效期 7 天，过期需重新获取
- 播放时按 `q` 键退出，或按回车键停止程序
