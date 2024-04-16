OpenedAI Images
---------------

An OpenAI API compatible images server to generate or manipulate images.

This server depends on an existing installation of [AUTOMATIC1111/stable-diffusion-webui](https://github.com/AUTOMATIC1111/stable-diffusion-webui).

This is not affiliated with OpenAI in any way, and no OpenAI API key is required.

Compatibility:
- [x] generations
- - [x] prompt, including AI enhanced prompts when selecting 'dall-e-3'
- - [x] model
- - [x] size
- - [ ] quality ("hd or standard")
- - [x] response_format *(partial support for url, uses data: urls not real urls)
- - [x] n
- - [ ] style ("vivid or natural")
- - [ ] user
- [ ] edits
- [x] variations *(square input size is not required but output size is always 1M pixel)

This is in active development and currently works for basic use-cases. It selects the generation configuration based on the chosen model.

The default configuration uses:
- dall-e-1: sd 1.5
- dall-e-2: sdxl_turbo / sdxl_lightning
- dall-e-3: sdxl

Settings for each model type can be found in the config folder, and can be modified as needed without needing to restart the server.

Quickstart
----------

Configure your environment:
```shell
echo SD_BASE_URL=http://<your stable diffusion webui server>:<port> > .env
echo OPENAI_BASE_URL=http://<your openai chat server>:<port>/v1 >> .env # optional, for dall-e-3 style AI prompt enhancement
echo OPENAI_API_KEY=skip >> .env # optional, for dall-e-3 style AI prompt enhancement
```

Docker (**recommended**):
```shell
docker compose up
```
or:
```shell
pip install -r requirements.txt
python images.py --host 127.0.0.1 --port 5005
```

You can use the OpenAI python client to interact with the API.
```shell
pip install -U openai
```

```python
import base64
import io
import openai
from PIL import Image
client = openai.Client(base_url='http://localhost:5005/v1', api_key='skip')
response = client.images.generate(prompt="A cute baby sea otter", response_format='b64_json', model='dall-e-3')
image = Image.open(io.BytesIO(base64.b64decode(response.data[0].b64_json)))
image.show()

```

Links & Documentation
---------------------

- Swagger API docs are available locally via /docs, here: (http://localhost:5005/docs) if you are using the defaults.
- OpenAI Images Guide: (https://platform.openai.com/docs/guides/moderation)
- OpenAI Images API Reference: (https://platform.openai.com/docs/api-reference/moderations)
- AUTOMATIC1111 Stable Diffusion WebUI: (https://github.com/AUTOMATIC1111/stable-diffusion-webui)
- ashleykleynhans/stable-diffusion-docker (https://github.com/ashleykleynhans/stable-diffusion-docker)

