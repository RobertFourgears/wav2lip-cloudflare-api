FROM python:3.10-slim
RUN apt-get update && apt-get install -y ffmpeg git wget && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt
RUN git clone https://github.com/Rudrabha/Wav2Lip.git && \
    cd Wav2Lip && \
    wget -q https://www.adrianbulat.com/downloads/python-fan/s3fd-619a316812.pth -O face_detection/detection/sfd/s3fd.pth && \
    wget -q https://huggingface.co/Non-playing-Character/Wave2lip/resolve/main/wav2lip_gan.pth -O checkpoints/wav2lip_gan.pth
COPY app.py .
EXPOSE 5000
ENV PORT=5000
CMD ["python", "app.py"]