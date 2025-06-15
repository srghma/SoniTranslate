build:
	docker build -t soni_translate_image .
	(docker stop sonitranslate || true)

translate_images:
	docker compose run -it --rm --name translate_images sonitranslate python /app/image_translate.py --from ru --to km /home/srghma/Downloads/nevzorov/thumbnail.jpg

web:
	docker compose run -it --rm --service-ports sonitranslate python /app/app_rvc.py --cpu_mode

run:
	docker compose run -it --rm --service-ports sonitranslate python /app/app_cli.py

bash:
	docker compose run -it --rm --service-ports sonitranslate bash

translate:
	# conda activate sonitr
	# python3 ./translate-srt/translate.py

upload:
	youtubeuploader \
		-secrets /home/srghma/Downloads/client_secret_386672333928-a4vm0at31m21c65h9s507rt8lkr36ta8.apps.googleusercontent.com.json \
		-secrets /home/srghma/.config/srghma2gmail-request.token \
		-caption "/home/srghma/projects/SoniTranslate/outputs/Congress is about to make a huge mistake for astronomy _SaveChandra _sE-RUu9ClsU___km.srt"
		-filename "/home/srghma/projects/SoniTranslate/outputs/Congress is about to make a huge mistake for astronomy _SaveChandra _sE-RUu9ClsU___km.mp4"
		-categoryId
		-description
		-language km
		-playlistID
		-privacy public
		-tags
		-thumbnail
		-title
