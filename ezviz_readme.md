# 萤石开放平台Android接入文档

## 平台概述

萤石开放平台提供完整的视频设备接入能力，支持Android客户端通过RESTful API实现设备管理、视频播放、云台控制等功能。

## 接入方案概览

萤石开放平台提供多种接入方案，开发者可根据需求选择：

### 1. RESTful API 接入（推荐）
- **适用场景**：自定义UI，灵活控制
- **优势**：完全自定义界面，功能丰富
- **接入方式**：HTTP API调用
- **支持平台**：Android、iOS、Web、小程序

### 2. 轻应用组件接入
- **适用场景**：快速集成，标准化UI
- **优势**：开箱即用，UI组件化
- **接入方式**：JavaScript组件
- **支持平台**：Web、H5、小程序

### 3. 原生SDK接入
- **适用场景**：功能完整，性能优化
- **优势**：本地处理，离线功能
- **接入方式**：原生SDK集成
- **支持平台**：Android、iOS

### 4. 国标GB28181接入
- **适用场景**：标准协议设备接入
- **优势**：标准化，兼容性强
- **接入方式**：GB/T协议
- **支持设备**：支持国标协议的NVR、IPC

### 5. 鸿蒙SDK接入
- **适用场景**：鸿蒙系统应用
- **优势**：原生鸿蒙支持
- **接入方式**：鸿蒙SDK
- **支持平台**：HarmonyOS

## 接入准备

### 1. 申请开发者账号
- 访问 [萤石开放平台](https://open.ezviz.com/)
- 注册开发者账号并完成实名认证

### 2. 创建应用
- 登录开放平台控制台
- 根据选择的接入方案创建对应类型应用
- 获取 `AppKey` 和 `AppSecret`

### 3. 配置应用信息
```
AppKey: 294cdfa6bbeb4f0e9d3d4dcabd4a40e6
AppSecret: 3474700a9958eedec0ed6919c24fbb74
```

### 4. 选择接入方案
根据项目需求选择合适的接入方案：
- **自定义UI需求高** → RESTful API
- **快速上线** → 轻应用组件
- **性能要求高** → 原生SDK
- **标准设备接入** → 国标协议
- **鸿蒙生态** → 鸿蒙SDK

## 认证机制

### 获取访问令牌

**接口地址：** `POST https://open.ys7.com/api/lapp/token/get`

**请求参数：**
```json
{
    "appKey": "your_app_key",
    "appSecret": "your_app_secret"
}
```

**响应示例：**
```json
{
    "code": "200",
    "msg": "操作成功",
    "data": {
        "accessToken": "at.1234567890abcdef",
        "expireTime": 7200
    }
}
```

**Android实现示例：**
```java
public class EzvizAuth {
    private static final String TOKEN_URL = "https://open.ys7.com/api/lapp/token/get";
    
    public static String getAccessToken(String appKey, String appSecret) {
        OkHttpClient client = new OkHttpClient();
        
        RequestBody formBody = new FormBody.Builder()
            .add("appKey", appKey)
            .add("appSecret", appSecret)
            .build();
            
        Request request = new Request.Builder()
            .url(TOKEN_URL)
            .post(formBody)
            .build();
            
        try (Response response = client.newCall(request).execute()) {
            String responseBody = response.body().string();
            JSONObject json = new JSONObject(responseBody);
            
            if ("200".equals(json.getString("code"))) {
                return json.getJSONObject("data").getString("accessToken");
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
        return null;
    }
}
```

## 设备管理API

### 1. 获取设备列表

**接口地址：** `POST https://open.ys7.com/api/lapp/device/list`

**请求参数：**
```json
{
    "accessToken": "your_access_token",
    "pageStart": 0,
    "pageSize": 50
}
```

**Android实现：**
```java
public List<EzvizDevice> getDeviceList(String accessToken) {
    String url = "https://open.ys7.com/api/lapp/device/list";
    
    RequestBody formBody = new FormBody.Builder()
        .add("accessToken", accessToken)
        .add("pageStart", "0")
        .add("pageSize", "50")
        .build();
        
    // 发送请求并解析响应
    // 返回设备列表
}
```

### 2. 获取设备信息

**接口地址：** `POST https://open.ys7.com/api/lapp/device/info`

**请求参数：**
```json
{
    "accessToken": "your_access_token",
    "deviceSerial": "device_serial_number"
}
```

### 3. 获取设备容量

**接口地址：** `POST https://open.ys7.com/api/lapp/device/capacity`

**请求参数：**
```json
{
    "accessToken": "your_access_token",
    "deviceSerial": "device_serial_number"
}
```

## 视频播放API

### 1. 获取直播地址

**接口地址：** `POST https://open.ys7.com/api/lapp/live/address/get`

**请求参数：**
```json
{
    "accessToken": "your_access_token",
    "deviceSerial": "device_serial_number",
    "channelNo": 1,
    "quality": 1
}
```

**响应示例：**
```json
{
    "code": "200",
    "msg": "操作成功",
    "data": {
        "url": "ezopen://open.ys7.com/device_serial_number/1.rec?source=ezviz"
    }
}
```

**Android播放实现：**
```java
public class VideoPlayer {
    private VideoView videoView;
    private MediaPlayer mediaPlayer;
    
    public void playLiveStream(String url) {
        // 使用EZOpen协议播放
        if (url.startsWith("ezopen://")) {
            playEzopenStream(url);
        } else if (url.startsWith("rtmp://")) {
            playRtmpStream(url);
        } else if (url.startsWith("http")) {
            playHlsStream(url);
        }
    }
    
    private void playEzopenStream(String ezopenUrl) {
        // 集成萤石播放SDK或使用第三方播放器
        // 推荐使用ExoPlayer或VLC for Android
    }
}
```

### 2. 查询录像

**接口地址：** `POST https://open.ys7.com/api/lapp/video/by/time`

**请求参数：**
```json
{
    "accessToken": "your_access_token",
    "deviceSerial": "device_serial_number",
    "channelNo": 1,
    "startTime": "2026-03-02 00:00:00",
    "endTime": "2026-03-02 23:59:59",
    "type": 0
}
```

**响应示例：**
```json
{
    "code": "200",
    "msg": "操作成功",
    "data": [
        {
            "fileId": "1234567890abcdef",
            "startTime": 1646179200000,
            "endTime": 1646179800000,
            "recType": 0,
            "downloadUrl": "https://download.ezviz.com/...",
            "playUrl": "https://play.ezviz.com/..."
        }
    ]
}
```

### 3. 云存储录像查询

**接口地址：** `POST https://open.ys7.com/api/lapp/cloud/video/file/list`

**请求参数：**
```json
{
    "accessToken": "your_access_token",
    "deviceSerial": "device_serial_number",
    "channelNo": 1,
    "startTime": 1646179200000,
    "endTime": 1646179800000
}
```

### 4. 获取录像下载地址

**接口地址：** `POST https://open.ys7.com/api/lapp/video/download/get`

**请求参数：**
```json
{
    "accessToken": "your_access_token",
    "fileId": "1234567890abcdef"
}
```

**响应示例：**
```json
{
    "code": "200",
    "msg": "操作成功",
    "data": {
        "downloadUrl": "https://download.ezviz.com/v1/files/1234567890abcdef.mp4"
    }
}
```

**Android下载实现：**
```java
public class VideoDownloader {
    public void downloadVideo(String accessToken, String fileId, String savePath) {
        // 1. 获取下载地址
        String downloadUrl = getDownloadUrl(accessToken, fileId);
        
        // 2. 下载文件
        OkHttpClient client = new OkHttpClient();
        Request request = new Request.Builder()
            .url(downloadUrl)
            .build();
            
        try (Response response = client.newCall(request).execute()) {
            InputStream inputStream = response.body().byteStream();
            FileOutputStream outputStream = new FileOutputStream(savePath);
            
            byte[] buffer = new byte[4096];
            int bytesRead;
            while ((bytesRead = inputStream.read(buffer)) != -1) {
                outputStream.write(buffer, 0, bytesRead);
            }
            
            outputStream.close();
            inputStream.close();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
    
    private String getDownloadUrl(String accessToken, String fileId) {
        String url = "https://open.ys7.com/api/lapp/video/download/get";
        
        RequestBody formBody = new FormBody.Builder()
            .add("accessToken", accessToken)
            .add("fileId", fileId)
            .build();
            
        Request request = new Request.Builder()
            .url(url)
            .post(formBody)
            .build();
            
        try (Response response = new OkHttpClient().newCall(request).execute()) {
            String responseBody = response.body().string();
            JSONObject json = new JSONObject(responseBody);
            
            if ("200".equals(json.getString("code"))) {
                return json.getJSONObject("data").getString("downloadUrl");
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
        return null;
    }
}
```

## 设备控制API

### 1. 云台控制

**接口地址：** `POST https://open.ys7.com/api/lapp/device/ptz/start`

**请求参数：**
```json
{
    "accessToken": "your_access_token",
    "deviceSerial": "device_serial_number",
    "channelNo": 1,
    "direction": "UP",
    "speed": 5,
    "command": "START"
}
```

**Android实现：**
```java
public void ptzControl(String accessToken, String deviceSerial, 
                      String direction, int speed) {
    String url = "https://open.ys7.com/api/lapp/device/ptz/start";
    
    RequestBody formBody = new FormBody.Builder()
        .add("accessToken", accessToken)
        .add("deviceSerial", deviceSerial)
        .add("channelNo", "1")
        .add("direction", direction)
        .add("speed", String.valueOf(speed))
        .add("command", "START")
        .build();
        
    // 发送控制指令
}
```

### 2. 抓拍图片

**接口地址：** `POST https://open.ys7.com/api/lapp/device/capture`

**请求参数：**
```json
{
    "accessToken": "your_access_token",
    "deviceSerial": "device_serial_number",
    "channelNo": 1
}
```

**响应示例：**
```json
{
    "code": "200",
    "msg": "操作成功",
    "data": {
        "picUrl": "https://img.ys7.com/group1/xxx.jpg"
    }
}
```

### 3. 设备布防

**接口地址：** `POST https://open.ys7.com/api/lapp/device/arm`

**请求参数：**
```json
{
    "accessToken": "your_access_token",
    "deviceSerial": "device_serial_number",
    "isArm": 1
}
```

## 其他接入方案详解

### 轻应用组件接入

#### 1. Web/H5接入
```html
<!-- 引入轻应用组件 -->
<script src="https://open.ys7.com/ezuikit/js/ezuikit.js"></script>

<!-- 创建播放器容器 -->
<video id="player" controls></video>

<script>
// 初始化播放器
var player = new EZUIKit.EZUIKitPlayer({
    id: 'player',
    url: 'ezopen://open.ys7.com/device_serial/1.live',
    accessToken: 'your_access_token',
    width: 800,
    height: 450
});
</script>
```

#### 2. 小程序接入
```javascript
// 引入轻应用组件
const EZUIKit = require('./ezuikit-miniprogram/ezuikit');

// 创建播放器
const player = EZUIKit.createPlayer({
    url: 'ezopen://open.ys7.com/device_serial/1.live',
    accessToken: 'your_access_token'
});
```

### 原生SDK接入

#### 1. Android SDK集成
```gradle
dependencies {
    // 萤石原生SDK
    implementation 'com.ezviz:ezviz-sdk:5.0.0'
    // 播放器组件
    implementation 'com.ezviz:ezuikit:4.0.0'
}
```

```java
// SDK初始化
EZOpenSDK.initLib(context, "app_key");

// 设备管理
EZOpenSDK.getInstance().setAccessToken("access_token");

// 播放器使用
EZUIPlayer player = new EZUIPlayer(context);
player.setUrl("ezopen://open.ys7.com/device_serial/1.live");
player.startPlay();
```

#### 2. iOS SDK集成
```swift
// SDK初始化
EZOpenSDK.initLib(appKey: "app_key")

// 设置访问令牌
EZOpenSDK.getInstance().setAccessToken("access_token")

// 播放器使用
let player = EZUIPlayer()
player.url = "ezopen://open.ys7.com/device_serial/1.live"
player.startPlay()
```

### 国标GB28181接入

#### 1. 设备注册
```java
// 国标设备接入
public class GBDeviceManager {
    public void registerDevice(String deviceId, String sipServer) {
        // 配置SIP参数
        SipConfig config = new SipConfig();
        config.setDeviceId(deviceId);
        config.setSipServer(sipServer);
        config.setUsername(deviceId);
        config.setPassword("password");
        
        // 注册到平台
        GB28181Client client = new GB28181Client(config);
        client.register();
    }
}
```

#### 2. 视频流获取
```java
// 获取国标设备视频流
public String getGBStream(String deviceId, int channelId) {
    // 通过国标协议获取视频流
    String streamUrl = String.format(
        "rtsp://%s:554/%s/%s", 
        sipServer, deviceId, channelId
    );
    return streamUrl;
}
```

### 鸿蒙SDK接入

#### 1. 鸿蒙应用配置
```json
// module.json5
{
  "module": {
    "name": "ezviz_harmony",
    "type": "entry",
    "dependencies": [
      "ezviz_harmony_sdk"
    ]
  }
}
```

```typescript
// 鸿蒙SDK使用
import { EZOpenSDK } from 'ezviz_harmony_sdk';

@Entry
@Component
struct VideoPlayer {
  private player: EZUIPlayer;
  
  aboutToAppear() {
    // 初始化SDK
    EZOpenSDK.init('app_key');
    EZOpenSDK.setAccessToken('access_token');
    
    // 创建播放器
    this.player = new EZUIPlayer();
    this.player.setUrl('ezopen://open.ys7.com/device_serial/1.live');
  }
  
  build() {
    Column() {
      // 播放器组件
      PlayerComponent({ player: this.player })
    }
  }
}
```

## Android SDK集成

### 1. 添加依赖

```gradle
dependencies {
    implementation 'com.squareup.okhttp3:okhttp:4.9.3'
    implementation 'com.google.code.gson:gson:2.8.9'
    implementation 'androidx.recyclerview:recyclerview:1.2.1'
    implementation 'com.google.android.exoplayer:exoplayer:2.18.1'
}
```

### 2. 网络权限配置

```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />
```

### 3. 核心类设计

```java
// 设备实体类
public class EzvizDevice {
    private String deviceSerial;
    private String deviceName;
    private String status;
    private boolean isShared;
    private int cameraNum;
    // getter/setter
}

// API管理类
public class EzvizApiManager {
    private static final String BASE_URL = "https://open.ys7.com/api/lapp/";
    private OkHttpClient httpClient;
    private String accessToken;
    
    public EzvizApiManager(String appKey, String appSecret) {
        this.httpClient = new OkHttpClient.Builder()
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .build();
        this.accessToken = authenticate(appKey, appSecret);
    }
    
    // 各种API方法
    public List<EzvizDevice> getDeviceList() { ... }
    public String getLiveAddress(String deviceSerial) { ... }
    public String capturePicture(String deviceSerial) { ... }
}
```

## 错误处理

### 常见错误码

| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| 2001 | 用户不存在 | 检查AppKey和AppSecret |
| 2002 | 用户签名错误 | 验证AppSecret正确性 |
| 2003 | accessToken无效或过期 | 重新获取访问令牌 |
| 4001 | 设备不存在 | 验证设备序列号 |
| 4002 | 设备离线 | 提示用户检查设备网络 |
| 4003 | 设备不支持该功能 | 禁用相关功能按钮 |
| 5001 | 参数错误 | 检查请求参数格式 |
| 6002 | 非法请求 | 检查请求频率限制 |

### 错误处理示例

```java
public class ApiCallback {
    public void handleResponse(String response) {
        try {
            JSONObject json = new JSONObject(response);
            String code = json.getString("code");
            
            if ("200".equals(code)) {
                // 处理成功响应
                onSuccess(json.getJSONObject("data"));
            } else {
                // 处理错误响应
                onError(code, json.getString("msg"));
            }
        } catch (JSONException e) {
            onError("PARSE_ERROR", "响应解析失败");
        }
    }
    
    private void onError(String code, String message) {
        switch (code) {
            case "2003":
                // 重新获取token
                refreshToken();
                break;
            case "4002":
                // 设备离线提示
                showDeviceOfflineDialog();
                break;
            default:
                // 通用错误提示
                showErrorDialog(message);
                break;
        }
    }
}
```

## 最佳实践

### 1. Token管理
- 实现Token自动刷新机制
- 安全存储Token，避免硬编码
- 处理Token过期情况

### 2. 网络优化
- 使用连接池管理HTTP连接
- 实现请求重试机制
- 添加网络状态检测

### 3. 用户体验
- 添加加载状态指示
- 实现离线数据缓存
- 提供网络异常提示

### 4. 安全考虑
- 使用HTTPS通信
- 敏感信息加密存储
- 防止API密钥泄露

## 测试建议

### 1. 单元测试
```java
@Test
public void testGetAccessToken() {
    String token = EzvizAuth.getAccessToken(APP_KEY, APP_SECRET);
    assertNotNull(token);
    assertTrue(token.length() > 0);
}
```

### 2. 集成测试
- 测试完整的API调用流程
- 验证错误处理逻辑
- 测试网络异常情况

## 部署发布

### 1. 混淆配置
```proguard
-keep class com.ezviz.** { *; }
-keep class okhttp3.** { *; }
-keep class com.google.gson.** { *; }
```

### 2. 版本兼容性
- 最低支持Android 5.0 (API 21)
- 目标版本Android 12 (API 31)
- 适配不同屏幕尺寸

## 技术支持

### 官方资源
- 萤石开放平台文档：https://open.ezviz.com/
- 技术支持邮箱：support@ezviz.com
- 开发者社区：https://bbs.ezviz.com/

### 常见问题
1. **视频播放卡顿**：检查网络带宽，降低播放质量
2. **设备控制延迟**：优化网络请求，减少并发调用
3. **Token频繁过期**：检查系统时间，实现自动刷新

---

**文档版本**：v1.0.0  
**更新时间**：2026年3月2日  
**适用平台**：Android 5.0+
