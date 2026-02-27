# 萤石摄像头客户端程序接入文档

## 目录

1. [概述](#1-概述)
2. [准备工作](#2-准备工作)
3. [SDK集成](#3-sdk集成)
4. [认证与授权](#4-认证与授权)
5. [核心功能接入](#5-核心功能接入)
6. [错误码说明](#6-错误码说明)
7. [常见问题](#7-常见问题)

---

## 1. 概述

### 1.1 文档说明

本文档旨在帮助开发者快速接入萤石开放平台，实现摄像头设备的视频预览、回放、云台控制等功能。

### 1.2 适用范围

- 萤石云视频SDK
- 支持平台：Windows / macOS / Linux / Android / iOS / Web

### 1.3 名词解释

| 名词 | 说明 |
|------|------|
| AppKey | 应用唯一标识，在萤石开放平台创建应用后获取 |
| AppSecret | 应用密钥，与AppKey配对使用 |
| AccessToken | 访问令牌，调用API的凭证 |
| DeviceSerial | 设备序列号，设备唯一标识 |
| ChannelNo | 通道号，多通道设备使用 |

---

## 2. 准备工作

### 2.1 注册萤石开放平台账号

1. 访问 [萤石开放平台](https://open.ys7.com)
2. 注册开发者账号并完成实名认证
3. 创建应用，获取 `AppKey` 和 `AppSecret`

### 2.2 添加设备

确保摄像头设备已添加到萤石云账号下：
- 通过萤石云视频APP添加设备
- 或通过API接口添加设备

### 2.3 开发环境要求

| 平台 | 要求 |
|------|------|
| Windows | Windows 7+ / Visual Studio 2015+ |
| Android | Android 5.0+ / Android Studio 3.0+ |
| iOS | iOS 9.0+ / Xcode 10+ |
| Web | 现代浏览器（Chrome/Firefox/Edge） |

---

## 3. SDK集成

### 3.1 Windows SDK集成

#### 下载SDK

从萤石开放平台下载Windows SDK：
```
https://open.ys7.com/doc/zh/book/index/sdk.html
```

#### 项目配置

1. 将SDK库文件复制到项目目录
2. 配置头文件路径和库文件路径
3. 链接必要的库文件

```cpp
// 引入头文件
#include "OpenNetStream.h"
#include "OpenNetStreamDefine.h"
#include "OpenNetStreamError.h"
```

#### CMake配置示例

```cmake
# CMakeLists.txt
cmake_minimum_required(VERSION 3.10)
project(EzvizDemo)

# 设置SDK路径
set(EZVIZ_SDK_PATH "${CMAKE_SOURCE_DIR}/sdk")

# 包含头文件
include_directories(${EZVIZ_SDK_PATH}/include)

# 链接库文件
link_directories(${EZVIZ_SDK_PATH}/lib)

add_executable(${PROJECT_NAME} main.cpp)
target_link_libraries(${PROJECT_NAME} OpenNetStream)
```

### 3.2 Android SDK集成

#### Gradle配置

```groovy
// build.gradle (app)
dependencies {
    implementation 'com.ezviz.sdk:ezviz-sdk:4.x.x'
}

// 或本地AAR引入
implementation files('libs/ezviz-sdk.aar')
```

#### AndroidManifest.xml权限配置

```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />
<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
<uses-permission android:name="android.permission.RECORD_AUDIO" />
```

### 3.3 iOS SDK集成

#### CocoaPods集成

```ruby
# Podfile
pod 'EZOpenSDK', '~> 4.x'
```

#### 手动集成

1. 将`EZOpenSDK.framework`拖入项目
2. 在`Build Settings`中添加`-ObjC`到`Other Linker Flags`
3. 添加依赖系统库

### 3.4 Web SDK集成

```html
<!-- 引入萤石JS SDK -->
<script src="https://open.ys7.com/sdk/js/2.0/ezuikit.js"></script>

<!-- 播放器容器 -->
<div id="video-container"></div>
```

---

## 4. 认证与授权

### 4.1 获取AccessToken

AccessToken是调用萤石开放平台API的凭证，有效期为7天。

#### HTTP请求

```http
POST https://open.ys7.com/api/lapp/token/get
Content-Type: application/x-www-form-urlencoded

appKey={appKey}&appSecret={appSecret}
```

#### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| appKey | String | 是 | 应用标识 |
| appSecret | String | 是 | 应用密钥 |

#### 响应示例

```json
{
    "code": "200",
    "msg": "操作成功",
    "data": {
        "accessToken": "at.xxxxxxxxxx",
        "expireTime": 1234567890000
    }
}
```

#### 代码示例

**Python**
```python
import requests

def get_access_token(app_key, app_secret):
    url = "https://open.ys7.com/api/lapp/token/get"
    data = {
        "appKey": app_key,
        "appSecret": app_secret
    }
    response = requests.post(url, data=data)
    result = response.json()
    if result["code"] == "200":
        return result["data"]["accessToken"]
    else:
        raise Exception(f"获取Token失败: {result['msg']}")
```

**Java**
```java
public String getAccessToken(String appKey, String appSecret) {
    String url = "https://open.ys7.com/api/lapp/token/get";
    Map<String, String> params = new HashMap<>();
    params.put("appKey", appKey);
    params.put("appSecret", appSecret);
    
    // 发送POST请求
    String response = HttpUtil.post(url, params);
    JSONObject json = JSON.parseObject(response);
    
    if ("200".equals(json.getString("code"))) {
        return json.getJSONObject("data").getString("accessToken");
    }
    throw new RuntimeException("获取Token失败");
}
```

**C#**
```csharp
public async Task<string> GetAccessTokenAsync(string appKey, string appSecret)
{
    using var client = new HttpClient();
    var content = new FormUrlEncodedContent(new[]
    {
        new KeyValuePair<string, string>("appKey", appKey),
        new KeyValuePair<string, string>("appSecret", appSecret)
    });
    
    var response = await client.PostAsync(
        "https://open.ys7.com/api/lapp/token/get", content);
    var json = await response.Content.ReadAsStringAsync();
    var result = JsonSerializer.Deserialize<TokenResponse>(json);
    
    return result.Data.AccessToken;
}
```

### 4.2 Token刷新策略

建议在Token过期前1天进行刷新，可采用以下策略：

```python
import time
import threading

class TokenManager:
    def __init__(self, app_key, app_secret):
        self.app_key = app_key
        self.app_secret = app_secret
        self.access_token = None
        self.expire_time = 0
        self._lock = threading.Lock()
    
    def get_token(self):
        with self._lock:
            # 提前1天刷新
            if time.time() * 1000 > self.expire_time - 86400000:
                self._refresh_token()
            return self.access_token
    
    def _refresh_token(self):
        # 调用API获取新Token
        result = get_access_token(self.app_key, self.app_secret)
        self.access_token = result["accessToken"]
        self.expire_time = result["expireTime"]
```

---

## 5. 核心功能接入

### 5.1 获取设备列表

```http
POST https://open.ys7.com/api/lapp/device/list
Content-Type: application/x-www-form-urlencoded

accessToken={accessToken}&pageStart=0&pageSize=10
```

#### 响应示例

```json
{
    "code": "200",
    "msg": "操作成功",
    "data": [
        {
            "deviceSerial": "D12345678",
            "deviceName": "客厅摄像头",
            "deviceType": "CS-C6CN",
            "status": 1,
            "defence": 0,
            "isEncrypt": 0
        }
    ]
}
```

### 5.2 实时视频预览

#### 5.2.1 获取直播地址

```http
POST https://open.ys7.com/api/lapp/v2/live/address/get
Content-Type: application/x-www-form-urlencoded

accessToken={accessToken}&deviceSerial={deviceSerial}&channelNo=1&protocol=2
```

| 参数 | 说明 |
|------|------|
| protocol | 1-HLS, 2-RTMP, 3-HLS/HTTPS, 4-RTMP/RTMPS |
| quality | 1-高清, 2-流畅 |

#### 5.2.2 Windows SDK播放

```cpp
#include "OpenNetStream.h"

class EzvizPlayer {
public:
    bool Init(const char* accessToken) {
        // 初始化SDK
        int ret = OpenSDK_InitLib(accessToken, "https://open.ys7.com");
        return ret == CYCLESDK_NOERROR;
    }
    
    bool StartPlay(HWND hWnd, const char* deviceSerial, int channelNo) {
        // 分配会话
        char sessionId[64] = {0};
        int ret = OpenSDK_AllocSession(
            OnMessageCallback, 
            this, 
            sessionId, 
            sizeof(sessionId)
        );
        if (ret != CYCLESDK_NOERROR) return false;
        
        // 开始播放
        ret = OpenSDK_StartRealPlay(
            sessionId,
            hWnd,
            deviceSerial,
            channelNo,
            ""  // 验证码（加密设备需要）
        );
        
        m_sessionId = sessionId;
        return ret == CYCLESDK_NOERROR;
    }
    
    void StopPlay() {
        if (!m_sessionId.empty()) {
            OpenSDK_StopRealPlay(m_sessionId.c_str());
            OpenSDK_FreeSession(m_sessionId.c_str());
        }
    }
    
    void Cleanup() {
        OpenSDK_FiniLib();
    }
    
private:
    static void __stdcall OnMessageCallback(
        const char* sessionId, 
        unsigned int msgType, 
        unsigned int errorCode,
        const char* info, 
        void* pUser) 
    {
        // 处理回调消息
        switch (msgType) {
            case cycleSDK_MSG_CYCLEPLAY_PLAY_SUCCESS:
                printf("播放成功\n");
                break;
            case cycleSDK_MSG_CYCLEPLAY_PLAY_FAIL:
                printf("播放失败: %d\n", errorCode);
                break;
        }
    }
    
    std::string m_sessionId;
};
```

#### 5.2.3 Android SDK播放

```java
public class EzvizPlayerActivity extends AppCompatActivity {
    private EZPlayer mPlayer;
    private SurfaceView mSurfaceView;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_player);
        
        mSurfaceView = findViewById(R.id.surface_view);
        
        // 初始化SDK
        EZOpenSDK.getInstance().setAccessToken("your_access_token");
        
        // 创建播放器
        mPlayer = EZOpenSDK.getInstance().createPlayer(
            "D12345678",  // 设备序列号
            1             // 通道号
        );
        
        // 设置播放回调
        mPlayer.setHandler(new Handler(Looper.getMainLooper()) {
            @Override
            public void handleMessage(Message msg) {
                switch (msg.what) {
                    case EZConstants.EZRealPlayConstants.MSG_REALPLAY_PLAY_SUCCESS:
                        Log.d("Player", "播放成功");
                        break;
                    case EZConstants.EZRealPlayConstants.MSG_REALPLAY_PLAY_FAIL:
                        Log.e("Player", "播放失败: " + msg.arg1);
                        break;
                }
            }
        });
        
        // 设置显示Surface
        mPlayer.setSurfaceHold(mSurfaceView.getHolder());
    }
    
    public void startPlay() {
        mPlayer.startRealPlay();
    }
    
    public void stopPlay() {
        mPlayer.stopRealPlay();
    }
    
    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (mPlayer != null) {
            mPlayer.release();
        }
    }
}
```

#### 5.2.4 Web播放器

```html
<!DOCTYPE html>
<html>
<head>
    <title>萤石视频播放</title>
    <script src="https://open.ys7.com/sdk/js/2.0/ezuikit.js"></script>
</head>
<body>
    <div id="video-container" style="width:600px;height:400px;"></div>
    
    <script>
        var player = new EZUIKit.EZUIKitPlayer({
            id: 'video-container',
            accessToken: 'your_access_token',
            url: 'ezopen://open.ys7.com/D12345678/1.live',
            width: 600,
            height: 400,
            template: 'simple',  // simple-极简版, standard-标准版, security-安防版
            
            // 播放成功回调
            handleSuccess: function() {
                console.log('播放成功');
            },
            
            // 播放失败回调
            handleError: function(err) {
                console.error('播放失败:', err);
            }
        });
        
        // 控制方法
        function play() { player.play(); }
        function stop() { player.stop(); }
        function capture() { player.capturePicture('snapshot'); }
        function openSound() { player.openSound(); }
        function closeSound() { player.closeSound(); }
    </script>
</body>
</html>
```

### 5.3 视频回放

#### 5.3.1 查询录像片段

```http
POST https://open.ys7.com/api/lapp/video/by/time
Content-Type: application/x-www-form-urlencoded

accessToken={accessToken}&deviceSerial={deviceSerial}&channelNo=1&startTime=2024010100000&endTime=2024010123595
```

#### 5.3.2 回放代码示例

**Windows**
```cpp
bool StartPlayback(const char* deviceSerial, int channelNo, 
                   const char* startTime, const char* endTime) {
    char sessionId[64] = {0};
    OpenSDK_AllocSession(OnMessageCallback, this, sessionId, sizeof(sessionId));
    
    int ret = OpenSDK_StartPlayBack(
        sessionId,
        m_hWnd,
        deviceSerial,
        channelNo,
        "",           // 验证码
        startTime,    // 格式: "2024-01-01 00:00:00"
        endTime       // 格式: "2024-01-01 23:59:59"
    );
    
    return ret == CYCLESDK_NOERROR;
}
```

**Android**
```java
// 创建回放播放器
EZPlayer player = EZOpenSDK.getInstance().createPlayerWithDeviceSerial(
    deviceSerial, 
    channelNo
);

// 设置回放时间
Calendar startCal = Calendar.getInstance();
startCal.set(2024, 0, 1, 0, 0, 0);

Calendar endCal = Calendar.getInstance();
endCal.set(2024, 0, 1, 23, 59, 59);

// 开始回放
player.startPlayback(startCal, endCal);
```

### 5.4 云台控制

#### 5.4.1 API接口

```http
POST https://open.ys7.com/api/lapp/device/ptz/start
Content-Type: application/x-www-form-urlencoded

accessToken={accessToken}&deviceSerial={deviceSerial}&channelNo=1&direction=0&speed=1
```

| direction | 说明 |
|-----------|------|
| 0 | 上 |
| 1 | 下 |
| 2 | 左 |
| 3 | 右 |
| 4 | 左上 |
| 5 | 左下 |
| 6 | 右上 |
| 7 | 右下 |
| 8 | 放大 |
| 9 | 缩小 |

#### 5.4.2 代码封装

```python
class PTZController:
    BASE_URL = "https://open.ys7.com/api/lapp/device/ptz"
    
    DIRECTION = {
        "up": 0, "down": 1, "left": 2, "right": 3,
        "left_up": 4, "left_down": 5, "right_up": 6, "right_down": 7,
        "zoom_in": 8, "zoom_out": 9
    }
    
    def __init__(self, access_token, device_serial, channel_no=1):
        self.access_token = access_token
        self.device_serial = device_serial
        self.channel_no = channel_no
    
    def start(self, direction, speed=1):
        """开始云台控制"""
        url = f"{self.BASE_URL}/start"
        data = {
            "accessToken": self.access_token,
            "deviceSerial": self.device_serial,
            "channelNo": self.channel_no,
            "direction": self.DIRECTION.get(direction, direction),
            "speed": speed
        }
        return requests.post(url, data=data).json()
    
    def stop(self, direction=None):
        """停止云台控制"""
        url = f"{self.BASE_URL}/stop"
        data = {
            "accessToken": self.access_token,
            "deviceSerial": self.device_serial,
            "channelNo": self.channel_no
        }
        if direction:
            data["direction"] = self.DIRECTION.get(direction, direction)
        return requests.post(url, data=data).json()

# 使用示例
ptz = PTZController(access_token, "D12345678")
ptz.start("left", speed=2)
time.sleep(1)
ptz.stop()
```

### 5.5 抓图与录像

#### 5.5.1 设备抓图

```http
POST https://open.ys7.com/api/lapp/device/capture
Content-Type: application/x-www-form-urlencoded

accessToken={accessToken}&deviceSerial={deviceSerial}&channelNo=1
```

#### 5.5.2 本地截图（SDK）

**Windows**
```cpp
// 截图到文件
int ret = OpenSDK_CapturePicture(sessionId, "D:\\snapshot.jpg");

// 截图到内存
char* pBuf = nullptr;
int bufLen = 0;
ret = OpenSDK_CapturePictureToMemory(sessionId, &pBuf, &bufLen);
// 使用完毕后释放
OpenSDK_FreeData(pBuf);
```

**Android**
```java
// 截图
Bitmap bitmap = mPlayer.capturePicture();
if (bitmap != null) {
    // 保存到文件
    saveBitmapToFile(bitmap, "/sdcard/snapshot.jpg");
}
```

### 5.6 语音对讲

#### 5.6.1 Windows SDK

```cpp
// 开始对讲
int ret = OpenSDK_StartVoiceTalk(
    sessionId,
    deviceSerial,
    channelNo,
    ""  // 验证码
);

// 停止对讲
OpenSDK_StopVoiceTalk(sessionId);
```

#### 5.6.2 Android SDK

```java
// 开始对讲
mPlayer.startVoiceTalk();

// 停止对讲
mPlayer.stopVoiceTalk();
```

### 5.7 设备布防/撤防

```http
POST https://open.ys7.com/api/lapp/device/defence/set
Content-Type: application/x-www-form-urlencoded

accessToken={accessToken}&deviceSerial={deviceSerial}&isDefence=1
```

| isDefence | 说明 |
|-----------|------|
| 0 | 撤防 |
| 1 | 布防 |

### 5.8 消息订阅（Webhook）

#### 配置回调地址

在萤石开放平台配置消息回调URL，接收设备告警等消息。

#### 回调数据格式

```json
{
    "header": {
        "appKey": "your_app_key",
        "messageId": "msg_123456",
        "messageType": "alarm"
    },
    "body": {
        "deviceSerial": "D12345678",
        "channelNo": 1,
        "alarmType": 10000,
        "alarmTime": 1704067200000,
        "picUrl": "https://..."
    }
}
```

#### 回调处理示例

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/ezviz/callback', methods=['POST'])
def ezviz_callback():
    data = request.json
    
    message_type = data['header']['messageType']
    
    if message_type == 'alarm':
        # 处理告警消息
        handle_alarm(data['body'])
    elif message_type == 'device':
        # 处理设备状态变更
        handle_device_status(data['body'])
    
    # 返回成功响应
    return jsonify({"code": "200", "msg": "success"})

def handle_alarm(body):
    device_serial = body['deviceSerial']
    alarm_type = body['alarmType']
    alarm_time = body['alarmTime']
    print(f"收到告警: 设备={device_serial}, 类型={alarm_type}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```

---

## 6. 错误码说明

### 6.1 通用错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| 10001 | 参数错误 | 检查请求参数是否完整正确 |
| 10002 | accessToken过期或异常 | 重新获取accessToken |
| 10005 | appKey被冻结 | 联系萤石客服 |
| 10017 | appKey不存在 | 检查appKey是否正确 |
| 20002 | 设备不存在 | 检查设备序列号 |
| 20006 | 设备不在线 | 检查设备网络连接 |
| 20007 | 设备响应超时 | 重试或检查设备状态 |
| 20008 | 设备开启了视频加密 | 需要提供验证码 |
| 20014 | 设备正在升级 | 等待升级完成 |
| 20018 | 调用次数超限 | 控制调用频率 |
| 49999 | 数据异常 | 联系技术支持 |

### 6.2 SDK错误码

| 错误码 | 说明 |
|--------|------|
| 0 | 成功 |
| 1 | 参数错误 |
| 2 | 内存不足 |
| 3 | 创建失败 |
| 4 | 网络错误 |
| 5 | 认证失败 |
| 6 | 设备不在线 |
| 7 | 连接超时 |
| 8 | 取流失败 |

---

## 7. 常见问题

### Q1: 如何处理视频加密设备？

加密设备需要在播放时提供验证码（设备标签上的6位字母）：

```cpp
// Windows
OpenSDK_StartRealPlay(sessionId, hWnd, deviceSerial, channelNo, "ABCDEF");

// Android
mPlayer.setPlayVerifyCode("ABCDEF");
mPlayer.startRealPlay();
```

### Q2: 如何优化播放延迟？

1. 使用RTMP协议（延迟约1-3秒）
2. 开启硬解码
3. 使用低延迟播放模式

```cpp
// Windows SDK设置低延迟
OpenSDK_SetDataCallBack(sessionId, OnDataCallback, this);
```

### Q3: 如何处理断线重连？

```java
// Android示例
mPlayer.setHandler(new Handler() {
    @Override
    public void handleMessage(Message msg) {
        if (msg.what == MSG_REALPLAY_PLAY_FAIL) {
            // 延迟重连
            new Handler().postDelayed(() -> {
                mPlayer.startRealPlay();
            }, 3000);
        }
    }
});
```

### Q4: 多路视频同时播放注意事项

1. 控制同时播放路数（建议不超过4路）
2. 使用流畅画质减少带宽占用
3. 及时释放不需要的播放器资源

### Q5: AccessToken安全存储建议

1. 不要在客户端硬编码AppSecret
2. 通过自有服务器中转获取AccessToken
3. 使用HTTPS传输

---

## 附录

### A. 相关链接

- [萤石开放平台](https://open.ys7.com)
- [API文档](https://open.ys7.com/doc/zh/)
- [SDK下载](https://open.ys7.com/doc/zh/book/index/sdk.html)
- [开发者论坛](https://bbs.ys7.com)

### B. 更新日志

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0.0 | 2024-01-01 | 初始版本 |

### C. 联系方式

- 技术支持邮箱：open@ys7.com
- 客服电话：400-878-7878

---

## 8. Python 客户端接入示例

### 8.1 环境准备

```bash
# 安装依赖
pip install requests opencv-python-headless numpy
```

### 8.2 获取 AccessToken（服务端/本地均可）

```python
# ezviz_auth.py
import requests

def get_access_token(app_key: str, app_secret: str) -> str:
    """
    获取萤石开放平台 AccessToken
    """
    url = "https://open.ys7.com/api/lapp/token/get"
    data = {
        "appKey": app_key,
        "appSecret": app_secret
    }
    resp = requests.post(url, data=data)
    result = resp.json()
    if result.get("code") == "200":
        return result["data"]["accessToken"]
    else:
        raise Exception(f"获取AccessToken失败: {result.get('msg')}")
```

### 8.3 获取设备列表与播放地址

```python
# ezviz_device.py
import requests

def get_device_list(access_token: str) -> list:
    """
    获取设备列表（含通道信息）
    """
    url = "https://open.ys7.com/api/lapp/device/list"
    params = {"accessToken": access_token}
    resp = requests.get(url, params=params)
    result = resp.json()
    if result.get("code") == "200":
        return result["data"]
    else:
        raise Exception(f"获取设备列表失败: {result.get('msg')}")

def get_live_url(access_token: str, device_serial: str, channel_no: int = 1) -> str:
    """
    获取直播地址（返回 ezopen:// 或 https 形式）
    """
    url = "https://open.ys7.com/api/lapp/live/address/get"
    params = {
        "accessToken": access_token,
        "deviceSerial": device_serial,
        "channelNo": channel_no,
        "quality": 1  # 1-高清 2-标清 3-流畅
    }
    resp = requests.get(url, params=params)
    result = resp.json()
    if result.get("code") == "200":
        return result["data"]["url"]
    else:
        raise Exception(f"获取直播地址失败: {result.get('msg')}")
```

### 8.4 拉流并播放（OpenCV + FFmpeg）

```python
# ezviz_player.py
import cv2
import threading
import time

class EzvizPlayer:
    def __init__(self, stream_url: str):
        self.stream_url = stream_url
        self.cap = None
        self.running = False

    def start(self):
        """启动拉流线程"""
        self.running = True
        self.thread = threading.Thread(target=self._run)
        self.thread.start()

    def _run(self):
        """拉流并显示画面"""
        # 若为 ezopen://，先用 ffmpeg 转为 rtsp/rtmp（需安装 ffmpeg）
        if self.stream_url.startswith("ezopen://"):
            # 示例：用 ffmpeg 转为 rtsp（请替换为你的实际转换逻辑）
            self.stream_url = f"rtsp://...转流后地址..."

        self.cap = cv2.VideoCapture(self.stream_url)
        if not self.cap.isOpened():
            raise Exception("无法打开视频流")

        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                break
            cv2.imshow("Ezviz Live", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            time.sleep(0.03)

    def stop(self):
        """停止拉流"""
        self.running = False
        if self.thread:
            self.thread.join()
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
```

### 8.5 完整客户端示例（可运行）

```python
# main.py
from ezviz_auth import get_access_token
from ezviz_device import get_device_list, get_live_url
from ezviz_player import EzvizPlayer

def main():
    # 1. 配置你的 AppKey/AppSecret（建议从环境变量或配置文件读）
    APP_KEY = "YOUR_APP_KEY"
    APP_SECRET = "YOUR_APP_SECRET"

    # 2. 获取 AccessToken
    token = get_access_token(APP_KEY, APP_SECRET)
    print(f"AccessToken: {token}")

    # 3. 获取设备列表
    devices = get_device_list(token)
    if not devices:
        print("未找到设备")
        return

    # 4. 取第一个设备的第一个通道
    device = devices[0]
    device_serial = device["deviceSerial"]
    channel_no = device.get("channelList", [{}])[0].get("channelNo", 1)
    print(f"使用设备: {device_serial}, 通道: {channel_no}")

    # 5. 获取直播地址
    live_url = get_live_url(token, device_serial, channel_no)
    print(f"直播地址: {live_url}")

    # 6. 播放
    player = EzvizPlayer(live_url)
    player.start()
    input("按回车键停止播放...")
    player.stop()

if __name__ == "__main__":
    main()
```

### 8.6 可选：使用 FFmpeg 拉流（支持 ezopen://）

```bash
# 安装 FFmpeg（Windows/macOS/Linux 均可）
# Windows：下载 https://ffmpeg.org/download.html 并加入 PATH
# macOS：brew install ffmpeg
# Linux（Ubuntu）：sudo apt install ffmpeg

# 命令行直接播放（测试用）
ffmpeg -i "ezopen://open.ys7.com/..." -c:v copy -f mpegts -
```

### 8.7 常见问题（Python）

| 问题 | 可能原因 | 解决方法 |
|------|----------|----------|
| `AccessToken` 失效 | 7天过期 | 重新调用获取接口或定时刷新 |
| 拉流黑屏 | URL 为 `ezopen://` 未转码 | 用 FFmpeg 或萤石播放器 SDK 转码 |
| `cv2.VideoCapture` 打不开 | RTSP/RTMP 地址不可达 | 确认网络、设备在线、地址格式正确 |
| 多路播放卡顿 | 带宽/解码性能不足 | 限流、降低画质、多线程/多进程 |

---

*本文档仅供开发参考，具体接口以萤石开放平台官方文档为准。*
