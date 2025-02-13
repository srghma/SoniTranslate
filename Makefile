run:
	docker build -t soni_translate_image .
	(docker stop sonitranslate || true)
	# Downloading model to /root/.local/share/tts/voice_conversion_models--multilingual--vctk--freevc24
	docker run --env-file .env -it --rm -p 7860:7860 -v .:/app -v ./.root-local-share-tts:/root/.local/share/tts -v /home/srghma/Downloads/:/home/srghma/Downloads/ --name sonitranslate soni_translate_image python /app/app_rvc.py --cpu_mode

translate:
	# conda activate sonitr
	# python3 ./translate-srt/translate.py
	docker run -it --rm -p 7860:7860 -v .:/app -v /home/srghma/Downloads/:/home/srghma/Downloads/ --name sonitranslate soni_translate_image bash
