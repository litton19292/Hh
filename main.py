from flask import Flask, jsonify, request
import threading
import os
import subprocess
import time

app = Flask(__name__)

# Global variable to track streaming process
streaming_process = None

def stream_to_youtube():
    global streaming_process
    try:
        if not os.path.exists('n.jpg'):
            print("Error: n.jpg not found!")
            return

        stop_streaming()

        cmd = [
            'ffmpeg',
            '-re',
            '-loop', '1',
            '-framerate', '1',
            '-i', 'n.jpg',
            '-f', 'lavfi',
            '-i', 'anullsrc=channel_layout=stereo:sample_rate=44100',
            '-c:v', 'libx264',
            '-preset', 'veryfast',
            '-b:v', '2500k',
            '-maxrate', '3000k',
            '-bufsize', '5000k',
            '-r', '30',
            '-vf', 'scale=720x1280:flags=lanczos,format=yuv420p,setsar=1',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-ar', '44100',
            '-tune', 'stillimage',
            '-g', '60',
            '-keyint_min', '60',
            '-f', 'flv',
            'rtmp://a.rtmp.youtube.com/live2/hcgy-uvvz-em0b-62c9-b6we'
        ]

        streaming_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("YouTube streaming started successfully!")

    except Exception as e:
        print(f"Error starting FFmpeg: {e}")

def stop_streaming():
    global streaming_process
    if streaming_process:
        try:
            streaming_process.terminate()
            for _ in range(10):
                if streaming_process.poll() is not None:
                    break
                time.sleep(0.1)
            if streaming_process.poll() is None:
                streaming_process.kill()
                streaming_process.wait()
            print("Streaming stopped successfully")
        except Exception as e:
            print(f"Error stopping FFmpeg: {e}")
        finally:
            streaming_process = None

@app.route("/")
def home():
    global streaming_process
    status = "Running" if streaming_process and streaming_process.poll() is None else "Stopped"
    return f"""
    <h1>YouTube Live Stream Controller</h1>
    <p><strong>Status:</strong> {status}</p>
    <div class="controls">
        <a href="/restart" class="btn restart">Restart Stream</a>
        <a href="/stop" class="btn stop">Stop Stream</a>
        <a href="/status" class="btn status">Check Status</a>
    </div>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        .controls {{ margin: 20px 0; }}
        .btn {{ 
            display: inline-block; 
            padding: 10px 15px; 
            margin-right: 10px; 
            text-decoration: none; 
            border-radius: 4px;
            font-weight: bold;
        }}
        .restart {{ background: #4CAF50; color: white; }}
        .stop {{ background: #f44336; color: white; }}
        .status {{ background: #2196F3; color: white; }}
    </style>
    """

@app.route("/restart")
def restart():
    try:
        threading.Thread(target=stream_to_youtube, daemon=True).start()
        time.sleep(1)
        return jsonify({
            "status": "success",
            "message": "Stream restarted successfully!",
            "stream_key": "hcgy-uvvz-em0b-62c9-b6we",
            "bitrate": "2500k video, 128k audio",
            "resolution": "720x1280",
            "fps": 30
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/stop")
def stop():
    try:
        stop_streaming()
        return jsonify({"status": "success", "message": "Stream stopped successfully!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/status")
def status():
    global streaming_process
    is_running = streaming_process and streaming_process.poll() is None
    return jsonify({
        "streaming": is_running,
        "status": "running" if is_running else "stopped",
        "stream_key": "hcgy-uvvz-em0b-62c9-b6we",
        "settings": {
            "video_bitrate": "2500k",
            "audio_bitrate": "128k",
            "resolution": "720x1280",
            "fps": 30
        }
    })

if __name__ == "__main__":
    threading.Thread(target=stream_to_youtube, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting YouTube stream controller on port {port}")
    print(f"Stream key: hcgy-uvvz-em0b-62c9-b6we")
    print(f"Access the controller at: http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)