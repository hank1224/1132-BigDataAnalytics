import vosk
import sounddevice as sd # 或者使用 PyAudio
import json
import queue

# 選擇你的模型路徑 (解壓縮後的模型資料夾)
# https://alphacephei.com/vosk/models
MODEL_PATH = "./vosk-model-en-us-0.42-gigaspeech"
# 選擇你的麥克風裝置 (可選)
# DEVICE_INFO = sd.query_devices(kind='input')
# SAMPLERATE = int(DEVICE_INFO['default_samplerate'])
SAMPLERATE = 16000 # 常用的取樣率

q = queue.Queue()

def callback(indata, frames, time, status):
    """音訊回調函數，將音訊數據放入佇列。"""
    if status:
        print(status)
    q.put(bytes(indata))

try:
    # 載入 Vosk 模型
    model = vosk.Model(MODEL_PATH)
    recognizer = vosk.KaldiRecognizer(model, SAMPLERATE)
    recognizer.SetWords(True) # 設定為 True 可以取得詞彙資訊

    print("開始即時語音辨識 (按 Ctrl+C 停止)...")

    # 開啟麥克風串流
    with sd.RawInputStream(samplerate=SAMPLERATE, blocksize=8000, dtype='int16',
                           channels=1, callback=callback):
        while True:
            data = q.get()
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                print(f"最終結果: {result['text']}")
            else:
                partial_result = json.loads(recognizer.PartialResult())
                if partial_result['partial']:
                    print(f"部分結果: {partial_result['partial']}")

except KeyboardInterrupt:
    print("\n辨識結束")
except Exception as e:
    print(f"發生錯誤: {e}")