# Use a base image with CUDA support
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

# Install the necessary tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends wget git ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Install Miniconda
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh && \
    bash miniconda.sh -b -p /opt/conda && \
    rm miniconda.sh && \
    /opt/conda/bin/conda init

# Add the path to conda to the environment
ENV PATH=/opt/conda/bin:$PATH

# Create and activate the conda environment
RUN /opt/conda/bin/conda create -n sonitr python=3.10 -y && \
    /opt/conda/bin/conda run -n sonitr pip install pip==23.1.2

# Install the necessary compilers and tools
RUN apt-get update && apt-get install -y build-essential cmake nano

# Install onnxruntime-gpu
RUN /opt/conda/bin/conda run -n sonitr pip install onnxruntime-gpu

# Install TTS 0.21.1 without dependencies
RUN /opt/conda/bin/conda run -n sonitr pip install -q TTS==0.21.1 --no-deps

# Remove old versions of numpy, pandas and librosa
RUN /opt/conda/bin/conda run -n sonitr pip uninstall -y numpy pandas librosa

# Install the required versions of numpy, pandas and librosa
RUN /opt/conda/bin/conda run -n sonitr pip install numpy==1.23.1 pandas==1.4.3 librosa==0.10.0

# Install the required versions of tts and torchcrepe
RUN /opt/conda/bin/conda run -n sonitr pip install "tts<0.21.0" "torchcrepe<0.0.20"

# Specify the working directory
WORKDIR /app

# Install the requirements_base.txt dependencies
COPY ./requirements_base.txt /app/requirements_base.txt
RUN (/opt/conda/bin/conda run -n sonitr pip install --default-timeout=1000 -r requirements_base.txt -v || true)
RUN /opt/conda/bin/conda run -n sonitr pip install --default-timeout=1000 -r requirements_base.txt -v

# Install the dependencies requirements_extra.txt
COPY ./requirements_extra.txt /app/requirements_extra.txt
RUN /opt/conda/bin/conda run -n sonitr pip install -r requirements_extra.txt -v

# Install dependencies requirements_xtts.txt
COPY ./requirements_xtts.txt /app/requirements_xtts.txt
RUN /opt/conda/bin/conda run -n sonitr pip install -q -r requirements_xtts.txt

RUN /opt/conda/bin/conda run -n sonitr pip uninstall -y torch torchvision torchaudio
RUN /opt/conda/bin/conda run -n sonitr pip install torch==2.1.0+cu118 torchvision==0.16.0+cu118 torchaudio==2.1.0+cu118 -f https://download.pytorch.org/whl/cu118/torch_stable.html
RUN /opt/conda/bin/conda run -n sonitr pip install googletrans pillow easyocr deep_translator
RUN /opt/conda/bin/conda run -n sonitr pip install pytube
RUN /opt/conda/bin/conda run -n sonitr pip install piper
RUN /opt/conda/bin/conda run -n sonitr pip install piper-tts

# RUN mkdir -p /app/mdx_models && \
#     wget -O /app/mdx_models/UVR-MDX-NET-Voc_FT.onnx "https://github.com/TRvlvr/model_repo/releases/download/all_public_uvr_models/UVR-MDX-NET-Voc_FT.onnx" && \
#     wget -O /app/mdx_models/UVR_MDXNET_KARA_2.onnx "https://github.com/TRvlvr/model_repo/releases/download/all_public_uvr_models/UVR_MDXNET_KARA_2.onnx" && \
#     wget -O /app/mdx_models/Reverb_HQ_By_FoxJoy.onnx "https://github.com/TRvlvr/model_repo/releases/download/all_public_uvr_models/Reverb_HQ_By_FoxJoy.onnx" && \
#     wget -O /app/mdx_models/UVR-MDX-NET-Inst_HQ_4.onnx "https://github.com/TRvlvr/model_repo/releases/download/all_public_uvr_models/UVR-MDX-NET-Inst_HQ_4.onnx"

# Open port 7860 in container
EXPOSE 7860

# Copy entrypoint.sh to container
# COPY entrypoint.sh /app/entrypoint.sh

# Set environment variables for Conda from cat /opt/conda/etc/profile.d/conda.sh
ENV CONDA_EXE="/opt/conda/bin/conda"
ENV _CE_M=""
ENV _CE_CONDA=""
ENV CONDA_PYTHON_EXE="/opt/conda/bin/python"
RUN conda init bash

# Activate Conda environment (optional)
SHELL ["/bin/bash", "-c"]
RUN conda create -n myenv python=3.9 -y
RUN echo "conda activate sonitr" >> ~/.bashrc

# RUN apt-get install -y unzip
# RUN wget -O /tmp/master.zip https://github.com/tokland/youtube-upload/archive/master.zip && \
#     unzip /tmp/master.zip && \
#     mv youtube-upload-master /youtube-upload && \
#     ls -al /youtube-upload && \
#     /opt/conda/bin/conda run -n sonitr python /youtube-upload/setup.py install

# RUN sed -i '/app\.launch(/,/debug=/s/max_threads=1,/max_threads=1, server_name="0.0.0.0",/' /app/app_rvc.py
