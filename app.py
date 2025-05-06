from flask import Flask, request, jsonify
import boto3, os, subprocess, shutil

R2_BUCKET = os.environ.get('R2_BUCKET')
R2_ENDPOINT = os.environ.get('R2_ENDPOINT')
R2_KEY = os.environ.get('R2_ACCESS_KEY')
R2_SECRET = os.environ.get('R2_SECRET_KEY')

print(f"[BOOT] R2_BUCKET: {R2_BUCKET}")
print(f"[BOOT] R2_ENDPOINT: {R2_ENDPOINT}")

s3 = boto3.client('s3',
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_KEY,
    aws_secret_access_key=R2_SECRET,
    region_name='auto'
)

app = Flask(__name__)

@app.route('/process', methods=['POST'])
def process_avatar():
    avatar_file = 'avatar.jpg'
    audio_file = 'voice.mp3'
    output_file = 'result.mp4'

    try:
        print("[INFO] Downloading avatar.jpg from R2...")
        s3.download_file(R2_BUCKET, avatar_file, avatar_file)
        print("[INFO] Downloading voice.mp3 from R2...")
        s3.download_file(R2_BUCKET, audio_file, audio_file)
    except Exception as e:
        print(f"[ERROR] Failed to download from R2: {e}")
        return jsonify({"error": f"Download failed: {e}"}), 500

    try:
        print("[INFO] Running inference.py...")
        cmd = [
            'python', 'inference.py',
            '--checkpoint_path', 'checkpoints/wav2lip_gan.pth',
            '--face', os.path.abspath(avatar_file),
            '--audio', os.path.abspath(audio_file),
            '--outfile', os.path.abspath(output_file)
        ]
        subprocess.run(cmd, cwd='Wav2Lip', check=True)
        print("[SUCCESS] Inference completed.")
    except Exception as e:
        print(f"[ERROR] Wav2Lip processing failed: {e}")
        return jsonify({"error": f"Wav2Lip processing failed: {e}"}), 500

    try:
        print("[INFO] Uploading result.mp4 back to R2...")
        s3.upload_file(output_file, R2_BUCKET, output_file)
        print("[SUCCESS] result.mp4 uploaded.")
    except Exception as e:
        print(f"[ERROR] Failed to upload result: {e}")
        return jsonify({"error": f"Upload failed: {e}"}), 500
    finally:
        for f in (avatar_file, audio_file, output_file):
            if os.path.exists(f): os.remove(f)
        shutil.rmtree(os.path.join('Wav2Lip', 'temp'), ignore_errors=True)

    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)