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
        if self.stream_url.startswith("ezopen://"):
            raise Exception("当前返回的是 ezopen:// 播放地址，OpenCV 无法直接播放。请在获取播放地址接口中选择可直接播放的协议（如 HLS/RTMP/HTTP-FLV），或使用萤石官方 SDK/播放器组件。")

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
