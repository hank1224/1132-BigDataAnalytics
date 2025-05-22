# pip install faster-whisper sounddevice numpy scikit-learn

import sounddevice as sd
import numpy as np
from faster_whisper import WhisperModel
import collections
import time
import threading

# --- 配置參數 ---
CHANNELS = 1                    # 單聲道
RATE = 16000                    # 採樣率 (Hz) - Whisper 模型要求 16000 Hz
AUDIO_BUFFER_SECONDS = 5        # 每次 Whisper 處理的音頻緩衝區大小 (秒)
MODEL_SIZE = "small"            # Whisper 模型大小 tiny, base, small, medium, large-v1, large-v2, distil-whisper-large-v3
LANGUAGE = "en"                 # 設置為中文 ("zh") 或其他語言，例如英文 ("en")

# --- 初始化 Whisper 模型 ---
# 如果你有 GPU，可以將 device="cuda"
# compute_type="int8" 或 "float16" 可以調整計算精度，int8 速度更快但可能略微犧牲準確性
print(f"正在加載 Whisper 模型: {MODEL_SIZE}...")
model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
print("模型加載完成。")

# --- 音頻緩衝區 ---
# 緩衝音頻數據直到達到指定秒數
# 使用 deque 存儲音頻 numpy 數組
audio_queue = collections.deque()
current_audio_frames = [] # 臨時存放音頻幀，直到達到 AUDIO_BUFFER_SECONDS
total_frames_collected = 0

# --- 鎖定機制，防止數據競爭 ---
transcription_lock = threading.Lock()
transcription_queue = collections.deque() # 用於存放待處理的音頻數據塊

# --- sounddevice 回調函數 ---
# 每當有新的音頻數據時，這個函數會被調用
def audio_callback(indata, frames, time_obj, status):
    global current_audio_frames, total_frames_collected

    if status:
        print(f"警告: 音頻回調狀態 - {status}", flush=True)

    # 將 indata (numpy 數組) 直接添加到緩衝區
    # indata 已經是 float32 類型，無需轉換
    current_audio_frames.append(indata.copy()) # .copy() 很重要，因為 indata 是緩衝區的視圖

    total_frames_collected += frames

    # 當收集到足夠的音頻數據時，將其傳遞給辨識線程
    if total_frames_collected >= RATE * AUDIO_BUFFER_SECONDS:
        combined_audio = np.concatenate(current_audio_frames, axis=0)
        # 轉換為單聲道 (如果原始錄音是多聲道)
        if combined_audio.ndim > 1:
            combined_audio = combined_audio[:, 0] # 取第一個通道

        with transcription_lock:
            transcription_queue.append(combined_audio)

        # 清空已處理的緩衝區並重置幀計數
        current_audio_frames = []
        total_frames_collected = 0

# --- 語音辨識線程 ---
def transcribe_thread():
    while True:
        if transcription_queue:
            with transcription_lock:
                audio_to_transcribe = transcription_queue.popleft()

            # 執行辨識
            segments, info = model.transcribe(audio_to_transcribe, language=LANGUAGE, beam_size=5)

            # 輸出結果
            print("\n----- 辨識結果 -----")
            for segment in segments:
                print(f"[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))
            print("--------------------\n")
        else:
            time.sleep(0.1) # 等待新數據

# --- 啟動語音辨識線程 ---
transcribe_worker = threading.Thread(target=transcribe_thread, daemon=True)
transcribe_worker.start()

# --- sounddevice 設置 ---
print("正在啟動麥克風流...")
try:
    with sd.InputStream(samplerate=RATE, channels=CHANNELS, callback=audio_callback):
        print("正在聆聽語音，請說話...")
        print(f"將每 {AUDIO_BUFFER_SECONDS} 秒處理一次語音...")
        # 保持主線程運行，直到用戶中斷 (Ctrl+C)
        # 這裡我們讓主線程休眠，以便後台的錄音和辨識線程可以運行
        while True:
            time.sleep(0.1)

except KeyboardInterrupt:
    print("停止錄音。")
except Exception as e:
    print(f"發生錯誤: {e}")
finally:
    # InputStream 會自動關閉，無需手動調用 stop_stream/close
    print("資源已釋放。")