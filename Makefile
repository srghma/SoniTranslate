build:
	docker build -t soni_translate_image .
	(docker stop sonitranslate || true)

translate_images:
	docker compose run -it --rm --name translate_images sonitranslate python /app/image_translate.py --from ru --to km /home/srghma/Downloads/nevzorov/thumbnail.jpg

run:
	# docker compose run -it --rm sonitranslate python /app/app_rvc.py --cpu_mode
	# docker compose run -it --rm sonitranslate python /app/app_cli.py

bash:
	docker compose run -it --rm sonitranslate bash

translate:
	# conda activate sonitr
	# python3 ./translate-srt/translate.py
