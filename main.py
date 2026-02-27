from ezviz_auth import get_access_token
from ezviz_device import get_device_list, get_live_url, disable_device_encrypt
from ezviz_player import EzvizPlayer
import time
import os

def _get_best_live_url(token: str, device_serial: str, channel_no: int) -> str:
    for protocol in (2, 1, 3, None):
        try:
            url = get_live_url(token, device_serial, channel_no, protocol=protocol)
        except TypeError:
            url = get_live_url(token, device_serial, channel_no)
        if not url.startswith("ezopen://"):
            return url
    return get_live_url(token, device_serial, channel_no)

def main():
    # 1. 配置你的 AppKey/AppSecret（建议从环境变量或配置文件读）
    APP_KEY = os.getenv("EZVIZ_APP_KEY")
    APP_SECRET = os.getenv("EZVIZ_APP_SECRET")
    if not APP_KEY or not APP_SECRET:
        raise RuntimeError(
            "缺少环境变量 EZVIZ_APP_KEY / EZVIZ_APP_SECRET。\n"
            "请先在系统环境变量中设置，或在 PowerShell 中临时设置：\n"
            "$env:EZVIZ_APP_KEY='你的APP_KEY'\n"
            "$env:EZVIZ_APP_SECRET='你的APP_SECRET'"
        )

    # 2. 获取 AccessToken
    token = get_access_token(APP_KEY, APP_SECRET)
    print(f"AccessToken: {token}")

    # 3. 获取设备列表
    devices = get_device_list(token)
    if not devices:
        print("未找到设备")
        return

    # 4. 选择设备
    if len(devices) == 1:
        device = devices[0]
        print(f"找到唯一设备: {device['deviceName']} ({device['deviceSerial']})")
    else:
        print("找到多个设备，请选择:")
        for i, device in enumerate(devices):
            print(f"{i+1}. {device['deviceName']} ({device['deviceSerial']}) - 状态: {'在线' if device['status'] == 1 else '离线'}")
        
        while True:
            try:
                choice = int(input("请输入设备编号: ")) - 1
                if 0 <= choice < len(devices):
                    device = devices[choice]
                    break
                else:
                    print("无效的选择，请重新输入")
            except ValueError:
                print("请输入有效的数字")

    device_serial = device["deviceSerial"]
    channel_no = device.get("channelList", [{}])[0].get("channelNo", 1) if device.get("channelList") else 1
    print(f"使用设备: {device['deviceName']} ({device_serial}), 通道: {channel_no}")

    # 5. 获取直播地址
    try:
        live_url = _get_best_live_url(token, device_serial, channel_no)
    except Exception as e:
        msg = str(e)
        if "[60019]" in msg or "加密已开启" in msg:
            print("设备视频加密已开启，需要验证码(validateCode)才能关闭加密并获取播放地址。")
            validate_code = input("请输入设备验证码(validateCode): ").strip()
            if not validate_code:
                raise
            disable_device_encrypt(token, device_serial, validate_code)
            last_err = None
            for _ in range(5):
                try:
                    live_url = _get_best_live_url(token, device_serial, channel_no)
                    last_err = None
                    break
                except Exception as retry_e:
                    last_err = retry_e
                    if "[60019]" not in str(retry_e) and "加密已开启" not in str(retry_e):
                        raise
                    time.sleep(1)
            if last_err is not None:
                live_url = f"ezopen://{validate_code}@open.ys7.com/{device_serial}/{channel_no}.hd.live"
        else:
            raise
    print(f"直播地址: {live_url}")

    # 6. 播放
    player = EzvizPlayer(live_url)
    player.start()
    input("按回车键停止播放...")
    player.stop()

if __name__ == "__main__":
    main()
