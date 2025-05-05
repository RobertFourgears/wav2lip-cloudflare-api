from flask import Flask, request, jsonify
import boto3, os, subprocess, shutil

R2_BUCKET = os.environ.get('R2_BUCKET', 'fourgears-voice-responses')
R2_ENDPOINT = os.environ.get('R2_ENDPOINT', 'https://7ed5a57b6314805291b01d698ded64f1.r2.cloudflarestorage.com')
R2_KEY = os.environ.get('R2_ACCESS_KEY')
R2_SECRET = os.environ.get('R2_SECRET_KEY')

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
        s3.download_file(R2_BUCKET, avatar_file, avatar_file)
        s3.download_file(R2_BUCKET, audio_file, audio_file)
    except Exception as e:
        return jsonify({"error": f"Failed to download input files: {e}"}), 500

    try:
        cmd = [
            'python', 'inference.py',
            '--checkpoint_path', 'checkpoints/wav2lip_gan.pth',
            '--face', os.path.abspath(avatar_file),
            '--audio', os.path.abspath(audio_file),
            '--outfile', os.path.abspath(output_file)
        ]
        subprocess.run(cmd, cwd='Wav2Lip', check=True)
    except Exception as e:
        return jsonify({"error": f"Wav2Lip processing failed: {e}"}), 500

    try:
        s3.upload_file(output_file, R2_BUCKET, output_file)
    except Exception as e:
        return jsonify({"error": f"Failed to upload result: {e}"}), 500
    finally:
        for f in (avatar_file, audio_file, output_file):
            if os.path.exists(f): os.remove(f)
        shutil.rmtree(os.path.join('Wav2Lip', 'temp'), ignore_errors=True)

    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)