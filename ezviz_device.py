import requests
from datetime import datetime

def disable_device_encrypt(access_token: str, device_serial: str, validate_code: str) -> None:
    url = "https://open.ys7.com/api/lapp/device/encrypt/off"
    data = {
        "accessToken": access_token,
        "deviceSerial": device_serial,
        "validateCode": validate_code,
    }
    resp = requests.post(url, data=data, timeout=15)
    print(f"关闭加密响应状态码: {resp.status_code}")
    print(f"关闭加密响应内容: {resp.text}")
    result = resp.json()
    if result.get("code") != "200":
        raise Exception(f"关闭视频加密失败: {result.get('msg')}")

def enable_device_encrypt(access_token: str, device_serial: str) -> None:
    url = "https://open.ys7.com/api/lapp/device/encrypt/on"
    data = {
        "accessToken": access_token,
        "deviceSerial": device_serial,
    }
    resp = requests.post(url, data=data, timeout=15)
    result = resp.json()
    if result.get("code") != "200":
        raise Exception(f"开启视频加密失败: {result.get('msg')}")

def set_device_defence(access_token: str, device_serial: str, enable: bool) -> None:
    url = "https://open.ys7.com/api/lapp/device/defence/set"
    data = {
        "accessToken": access_token,
        "deviceSerial": device_serial,
        "isDefence": 1 if enable else 0,
    }
    resp = requests.post(url, data=data, timeout=15)
    result = resp.json()
    if result.get("code") != "200":
        raise Exception(f"设置布防失败: {result.get('msg')}")

def ptz_start(access_token: str, device_serial: str, channel_no: int, direction: int, speed: int = 1) -> None:
    url = "https://open.ys7.com/api/lapp/device/ptz/start"
    data = {
        "accessToken": access_token,
        "deviceSerial": device_serial,
        "channelNo": channel_no,
        "direction": direction,
        "speed": speed,
    }
    resp = requests.post(url, data=data, timeout=10)
    result = resp.json()
    if result.get("code") != "200":
        raise Exception(f"云台控制失败: {result.get('msg')}")

def ptz_stop(access_token: str, device_serial: str, channel_no: int, direction: int) -> None:
    url = "https://open.ys7.com/api/lapp/device/ptz/stop"
    data = {
        "accessToken": access_token,
        "deviceSerial": device_serial,
        "channelNo": channel_no,
        "direction": direction,
    }
    resp = requests.post(url, data=data, timeout=10)
    result = resp.json()
    if result.get("code") != "200":
        raise Exception(f"云台停止失败: {result.get('msg')}")

def capture_picture(access_token: str, device_serial: str, channel_no: int) -> str:
    url = "https://open.ys7.com/api/lapp/device/capture"
    data = {
        "accessToken": access_token,
        "deviceSerial": device_serial,
        "channelNo": channel_no,
    }
    resp = requests.post(url, data=data, timeout=15)
    result = resp.json()
    if result.get("code") != "200":
        raise Exception(f"抓拍失败: {result.get('msg')}")
    data_obj = result.get("data")
    if isinstance(data_obj, dict) and isinstance(data_obj.get("picUrl"), str):
        return data_obj["picUrl"]
    if isinstance(data_obj, str):
        return data_obj
    raise Exception(f"抓拍失败: 返回数据结构异常: {data_obj}")

def get_device_status(access_token: str, device_serial: str, channel_no: int | None = None) -> dict:
    url = "https://open.ys7.com/api/lapp/device/status/get"
    data = {
        "accessToken": access_token,
        "deviceSerial": device_serial,
    }
    if channel_no is not None:
        data["channelNo"] = channel_no
    resp = requests.post(url, data=data, timeout=15)
    result = resp.json()
    if result.get("code") != "200":
        raise Exception(f"获取设备状态失败: {result.get('msg')}")
    data_obj = result.get("data")
    if isinstance(data_obj, dict):
        return data_obj
    return {}

def get_device_info(access_token: str, device_serial: str) -> dict:
    url = "https://open.ys7.com/api/lapp/device/info"
    data = {
        "accessToken": access_token,
        "deviceSerial": device_serial,
    }
    resp = requests.post(url, data=data, timeout=15)
    result = resp.json()
    if result.get("code") != "200":
        raise Exception(f"获取设备信息失败: {result.get('msg')}")
    data_obj = result.get("data")
    if isinstance(data_obj, dict):
        return data_obj
    return {}

def get_device_capacity(access_token: str, device_serial: str) -> dict:
    url = "https://open.ys7.com/api/lapp/device/capacity"
    data = {
        "accessToken": access_token,
        "deviceSerial": device_serial,
    }
    resp = requests.post(url, data=data, timeout=15)
    result = resp.json()
    if result.get("code") != "200":
        raise Exception(f"获取设备能力集失败: {result.get('msg')}")
    data_obj = result.get("data")
    if isinstance(data_obj, dict):
        return data_obj
    return {}

def get_device_camera_list(access_token: str, device_serial: str) -> list:
    url = "https://open.ys7.com/api/lapp/device/camera/list"
    data = {
        "accessToken": access_token,
        "deviceSerial": device_serial,
    }
    resp = requests.post(url, data=data, timeout=15)
    result = resp.json()
    if result.get("code") != "200":
        raise Exception(f"获取通道信息失败: {result.get('msg')}")
    data_obj = result.get("data")
    if isinstance(data_obj, list):
        return data_obj
    return []

def get_sound_switch_status(access_token: str, device_serial: str) -> dict:
    url = "https://open.ys7.com/api/lapp/device/sound/switch/status"
    data = {
        "accessToken": access_token,
        "deviceSerial": device_serial,
    }
    resp = requests.post(url, data=data, timeout=15)
    result = resp.json()
    if result.get("code") != "200":
        raise Exception(f"获取提示音开关状态失败: {result.get('msg')}")
    data_obj = result.get("data")
    if isinstance(data_obj, dict):
        return data_obj
    return {}

def set_sound_switch(access_token: str, device_serial: str, enable: bool) -> None:
    url = "https://open.ys7.com/api/lapp/device/sound/switch/set"
    data = {
        "accessToken": access_token,
        "deviceSerial": device_serial,
        "enable": 1 if enable else 0,
    }
    resp = requests.post(url, data=data, timeout=15)
    result = resp.json()
    if result.get("code") != "200":
        raise Exception(f"设置提示音开关失败: {result.get('msg')}")

def get_scene_switch_status(access_token: str, device_serial: str) -> dict:
    url = "https://open.ys7.com/api/lapp/device/scene/switch/status"
    data = {
        "accessToken": access_token,
        "deviceSerial": device_serial,
    }
    resp = requests.post(url, data=data, timeout=15)
    result = resp.json()
    if result.get("code") != "200":
        raise Exception(f"获取镜头遮蔽开关状态失败: {result.get('msg')}")
    data_obj = result.get("data")
    if isinstance(data_obj, dict):
        return data_obj
    return {}

def set_scene_switch(access_token: str, device_serial: str, enable: bool) -> None:
    url = "https://open.ys7.com/api/lapp/device/scene/switch/set"
    data = {
        "accessToken": access_token,
        "deviceSerial": device_serial,
        "enable": 1 if enable else 0,
    }
    resp = requests.post(url, data=data, timeout=15)
    result = resp.json()
    if result.get("code") != "200":
        raise Exception(f"设置镜头遮蔽开关失败: {result.get('msg')}")

def get_device_list(access_token: str) -> list:
    """
    获取设备列表（含通道信息）
    """
    url = "https://open.ys7.com/api/lapp/device/list"
    data = {"accessToken": access_token}
    resp = requests.post(url, data=data, timeout=20)
    
    print(f"请求URL: {resp.url}")
    print(f"响应状态码: {resp.status_code}")
    print(f"响应内容: {resp.text}")
    
    result = resp.json()
    if result.get("code") == "200":
        return result["data"]
    else:
        raise Exception(f"获取设备列表失败: {result.get('msg')}")

def get_live_url(access_token: str, device_serial: str, channel_no: int = 1, protocol: int | None = None) -> str:
    """
    获取直播地址（返回 ezopen:// 或 https 形式）
    """
    url = "https://open.ys7.com/api/lapp/v2/live/address/get"
    data = {
        "accessToken": access_token,
        "deviceSerial": device_serial,
        "channelNo": channel_no,
        "quality": 1  # 1-高清 2-标清 3-流畅
    }
    if protocol is not None:
        data["protocol"] = protocol
    resp = requests.post(url, data=data, timeout=20)
    
    print(f"直播地址请求URL: {resp.url}")
    print(f"直播地址响应状态码: {resp.status_code}")
    print(f"直播地址响应内容: {resp.text}")
    
    result = resp.json()
    if result.get("code") == "200":
        data_obj = result.get("data")
        if isinstance(data_obj, dict) and "url" in data_obj:
            return data_obj["url"]
        raise Exception(f"获取直播地址失败: 返回数据结构异常: {data_obj}")
    code = result.get("code")
    msg = result.get("msg")
    raise Exception(f"获取直播地址失败[{code}]: {msg}")

def list_record_files_by_time(
    access_token: str,
    device_serial: str,
    channel_no: int,
    start_time: datetime,
    end_time: datetime,
    rec_type: int = 0,
    page_start: int = 0,
    page_size: int = 50,
) -> list:
    url = "https://open.ys7.com/api/lapp/video/by/time"
    start_ms = int(start_time.timestamp() * 1000)
    end_ms = int(end_time.timestamp() * 1000)
    data = {
        "accessToken": access_token,
        "deviceSerial": device_serial,
        "channelNo": channel_no,
        "startTime": start_ms,
        "endTime": end_ms,
        "recType": rec_type,
        "pageStart": page_start,
        "pageSize": page_size,
    }
    resp = requests.post(url, data=data, timeout=25)
    result = resp.json()
    if result.get("code") != "200":
        raise Exception(f"查询录像失败[{result.get('code')}]: {result.get('msg')}")
    data_obj = result.get("data")
    if isinstance(data_obj, list):
        return data_obj
    if isinstance(data_obj, dict) and isinstance(data_obj.get("data"), list):
        return data_obj.get("data")
    return []

def build_ezopen_playback_url(device_serial: str, channel_no: int, begin_time: datetime, end_time: datetime, validate_code: str | None = None) -> str:
    begin = begin_time.strftime("%Y%m%d%H%M%S")
    end = end_time.strftime("%Y%m%d%H%M%S")
    prefix = "ezopen://open.ys7.com"
    if validate_code:
        prefix = f"ezopen://{validate_code}@open.ys7.com"
    return f"{prefix}/{device_serial}/{channel_no}.local.rec?begin={begin}&end={end}"
