OpenedAI Images
---------------

An OpenAI API compatible images server to generate or manipulate images.

This server depends on an existing installation of [AUTOMATIC1111/stable-diffusion-webui](https://github.com/AUTOMATIC1111/stable-diffusion-webui).

This is not affiliated with OpenAI in any way, and no OpenAI API key is required.

Compatibility:
- [x] generations
- - [x] prompt
- - [x] model
- - [x] size
- - [ ] quality ("hd or standard")
- - [x] response_format *(partial support for url, uses data: urls not real urls)
- - [x] n
- - [ ] style ("vivid or natural")
- - [ ] user
- [ ] edits
- [ ] variations

This is in active development and currently works for basic use-cases. It selects generation configuration based on model.

Currently hard coded as:
- dall-e-1: sd 1.5
- dall-e-2: sdxl_lightning
- dall-e-3: sdxl

Quickstart
----------

Docker (**recommended**):
```shell
echo SD_BASE_URL=http://<your stable diffusion webui server>:<port> > .env
docker compose up
```
or:
```shell
pip install -r requirements.txt
python images.py --host 127.0.0.1 --port 5005
```

You can use the OpenAI client to interact with the API.
```python
import base64
import io
import openai
from PIL import Image
client = openai.Client(base_url='http://localhost:5005/v1')
response = client.images.generate(prompt="A cute baby sea otter", response_format='b64_json')
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