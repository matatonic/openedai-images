#!/usr/bin/env python3
import io
import os
import sys
import time
import yaml
import math
import argparse

import requests

from typing import Optional, List
from fastapi import UploadFile, Form
import uvicorn
from pydantic import BaseModel
import base64
from PIL import Image

import openedai

pipe = None
app = openedai.OpenAIStub()

if OPENAI_BASE_URL:
    import openai
    openai_client = openai.Client()


async def sd_request(payload, api="txt2img", config_manager=None):
    if config_manager is None:
        raise ValueError("ConfigManager instance is required")

    # Get the base URL from the configuration
    # Check if the environment variable is set and override the base URL if it is
    base_url = os.environ.get("SD_BASE_URL", base_url, config_manager.get(["default", "enhanced_prompt", "sd_base_url"]))

    # Send the request and return the response
    response = requests.post(f"{base_url}/sdapi/v1/{api}", json=payload)
    r = response.json()
    if response.status_code != 200 or 'images' not in r:
        #raise ServiceUnavailableError(r.get('error', 'Unknown error calling Stable Diffusion'), code=response.status_code, internal_message=r.get('errors', None))
        print(r)
        return []
    
    return r['images']

"""
defaults:
  enhanced_prompt:
    models:
    - dall-e-3
    openai_api_key: sk-1111
    openai_base_url: http://localhost:5005/v1
    params:
"""
class ConfigManager:
    def __init__(self, config_path):
        self.config_path = config_path
        self.parsed_config = self.load_config()

    def load_config(self):
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)

    def update_config(self):
        self.parsed_config = self.load_config()

    def get_config(self):
        return self._get_config(self.parsed_config)

    # ['defaults', 'enhanced_prompt', 'openai_api_key'], 
    def get(self, key: list[str], default=None):
        conf = self.load_config()
        if len(key) > 1:
            for k in key:
                if k in conf:
                    conf = conf[k]
                else:
                    return default
        if conf:
            return conf.get(key[-1], default)
        return default

async def DallesquePrompt(prompt, config_manager=None):
    if config_manager is None:
        raise ValueError("ConfigManager instance is required")

    # Get the base URL and API key from the configuration
    # Check if the environment variables are set and override the base URL and API key if they are
    base_url = os.environ.get("OPENAI_BASE_URL", config_manager.get_config().get("openai_base_url"))
    api_key = os.environ.get("OPENAI_API_KEY", config_manager.get_config().get("openai_api_key"))

    # Construct the request payload
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": config_manager.get_config().get("enhanced_prompts").get("messages"),
        "temperature": 0.7,
    }

    # Send the request and return the response
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.post(base_url, json=payload, headers=headers)
    return response.json()


if model in config_manager.get_config().get("openai_api_key"))
    

async def DallesquePrompt(prompt):

    
    if not OPENAI_BASE_URL:
        return prompt

    messages = [ {'role': 'user', 'content': """Rules for generating prompts based on user input:
1. **Description of the object or scene (5-7 words).** Briefly indicate what or who should be depicted, focusing on the main object or plot.
2. **Key characteristics (10-20 words).** Describe important features of the object, character, or scene elements that are key to visualization.
3. **Environment or background (10-15 words).** Provide context for the location or surroundings in which the object is situated, adding depth and atmosphere.
4. **Combination or blending of elements (10-15 words).** If applicable, explain how different aspects or characteristics combine or blend to create a unique image.
5. **Symbolic or emotional significance (10-15 words).** Express the intended symbolic meaning or emotions that the image should evoke.
6. **Lighting and time of day (3-5 words).** Specify the lighting and time of day to add to the visual mood of the scene.
7. **Additional details (5-10 words).** Include specific or important details that will complement and clarify the visualization.
8. **Overall mood or impression (3-7 words).** Conclude with a description of the overall mood or main impression that the image should convey.

Write everything in 1 sentence (not a list), separating with commas, in English, strictly following the instruction (especially the number of words). Provide descriptions that are direct and literal, avoiding metaphors and figurative language, and exclude specific features like "Velvet shadows." Focus on explicit and clear depiction of features, surroundings, element combinations, symbolic significance, lighting, additional details, and overall mood without using commonly associated expressions or imagery."""},
        {'role': 'assistant', 'content': "Understood, provide the input and I will generate a complete description of a scene."},
        {'role': 'user', 'content': "photo of an ancient castle very atmospheric, but the sky should be completely covered in clouds, yet it should be bright."},
        {'role': 'assistant', 'content': "photo of an ancient castle with a majestic, eerie ambiance, highlighting its towering spires, weathered stone, and ivy-clad walls, set against a backdrop of a dense, mystic forest under a sky completely shrouded in clouds yet illuminated by a diffused, ethereal light, where the fusion of natural decay and enduring architectural grandeur evokes a sense of timeless mystery and the eternal battle between man and nature, casting a glow that reveals subtle details and textures, creating an impression of haunting beauty and solemn tranquility. "},
        {'role': 'user', 'content': prompt }
    ]

    resp = openai_client.chat.completions.create(
        model='x',
        messages=messages,
        temperature=1.99,
        max_tokens=300,
        top_p=0.5,
        stop=['\n', '</s>'],
    )
    return resp.choices[0].message.content


class txt2img_request_generator:
    base_model_size = None
    default_conf_path: str = None
    default_conf: dict = {}

    def __init__(self):
        self.default_conf = self.load_default_conf(self.default_conf_path)
    
    def load_default_conf(self, filename):
        if filename and os.path.exists(filename):
            with open(filename, 'r') as f:
                return json.load(f)

    def maybe_scaler(self, payload, width, height):
        scale = math.sqrt(width * height) / self.base_model_size

        # If the target is more than 20% off the ideal size, scale it
        if abs(scale - 1) >= 0.2:
            # SD expects pixel sized aligned by 8
            sd_width = 8 * round(width / (scale * 8))
            sd_height = 8 * round(height / (scale * 8))
            scaler = {
                'width': sd_width,
                'height': sd_height,
                'enable_hr': True,
                'hr_resize_x': width,
                'hr_resize_y': height,
            }
            payload.update(scaler)

    def maybe_vscaler(self, payload, width, height):
        scale = math.sqrt(width * height) / self.base_model_size

        # If the target is more than 20% off the ideal size, scale it
        if abs(scale - 1) >= 0.2:
            # SD expects pixel sized aligned by 8
            sd_width = 8 * round(width / (scale * 8))
            sd_height = 8 * round(height / (scale * 8))
            scaler = {
                'width': sd_width,
                'height': sd_height,
                'resize_mode': 3,
            }
            payload.update(scaler)

    def create_request(self, prompt, width, height, n):
        payload = {
            'prompt': prompt,
            'width': width,
            'height': height,
            'batch_size': n,
        }
        self.maybe_scaler(payload, width, height)
        payload.update(self.default_conf)
        return payload

    async def create_variation(self, image, width, height, n):
        img_dat = await image.read()
        pil_image = Image.open(io.BytesIO(img_dat))
        payload = {
            'init_images': [base64.b64encode(img_dat).decode()],
            'width': pil_image.size[0],
            'height': pil_image.size[1],
            'batch_size': n,
        }

        self.maybe_vscaler(payload, pil_image.size[0], pil_image.size[1])
        payload.update(self.default_conf)
        return payload

class sd15_request_generator(txt2img_request_generator):
    base_model_size: int = 512
    default_conf_path: str = f'{CONF_PATH}/default_sd15_conf.json'

class sdxl_lightning_request_generator(txt2img_request_generator):
    base_model_size = 1024
    default_conf_path = f'{CONF_PATH}/default_sdxl_lightning_conf.json'

class sdxl_request_generator(txt2img_request_generator):
    base_model_size = 1024
    default_conf_path = f'{CONF_PATH}/default_sdxl_conf.json'

class GenerationsRequest(BaseModel):
    prompt: str
    model: Optional[str] = "dall-e-2" # dall-e-3
    size: Optional[str] = "1024x1024" #256x256, 512x512, or 1024x1024 for dall-e-2. Must be one of 1024x1024, 1792x1024, or 1024x1792 for dall-e-3
    quality: Optional[str] = "standard" # or hd
    response_format: Optional[str] = "url" # or b64_json
    n: Optional[int] = 1 # 1-10, 1 only for dall-e-3
    style: Optional[str] = "vivid" # natural
    user: Optional[str] = None

@app.post("/v1/images/generations")
async def generations(request: GenerationsRequest):
    resp = {
        'created': int(time.time()),
        'data': []
    }

    revised_prompt = None
    width, height = request.size.split('x')

    Config()
    # TODO: select backend model by config
    if request.model == 'dall-e-1':
        rg = sd15_request_generator()
    elif request.model == 'dall-e-2':
        rg = sdxl_lightning_request_generator()
    else:
        rg = sdxl_request_generator()

        # dall-e-3 reworks the prompt
        # https://platform.openai.com/docs/guides/images/prompting
        if not request.prompt.startswith("I NEED to test how the tool works with extremely simple prompts. DO NOT add any detail, just use it AS-IS:"):
            request.prompt = revised_prompt = await DallesquePrompt(request.prompt)
        else:
            request.prompt = revised_prompt = request.prompt[len("I NEED to test how the tool works with extremely simple prompts. DO NOT add any detail, just use it AS-IS:"):]

    req = rg.create_request(request.prompt, int(width), int(height), request.n)
    print(req)

    imgs = await sd_request(req, "txt2img")

    if imgs:
        for b64_json in imgs:
            if request.response_format == 'b64_json':
                img_dat = {'b64_json': b64_json}
            else:
                # TODO: use files API to post this image and return a URL - or reverse engineer the SD URL to get a direct link to the image.
                img_dat = {'url': f'data:image/png;base64,{b64_json}'}  # yeah it's lazy. requests.get() will not work with this, but web clients will

            if revised_prompt:
                img_dat['revised_prompt'] = revised_prompt

            resp['data'].extend([img_dat])

    return resp

class EditsRequest(BaseModel):
    image: UploadFile
    prompt: str
    model: Optional[str] = "dall-e-2" # dall-e-3
    size: Optional[str] = "1024x1024" #256x256, 512x512, or 1024x1024 for dall-e-2. Must be one of 1024x1024, 1792x1024, or 1024x1792 for dall-e-3
    quality: Optional[str] = "standard" # or hd
    response_format: Optional[str] = "url" # or b64_json
    n: Optional[int] = 1 # 1-10, 1 only for dall-e-3
    style: Optional[str] = "vivid" # natural
    user: Optional[str] = None

@app.post("/v1/images/edits")
async def edits(request: EditsRequest):
    resp = {
        'created': int(time.time()),
        'data': []
    }


@app.post("/v1/images/variations")
async def variations(
        image: UploadFile,
        model: str = Form("dall-e-2"), # only dall-e-2
        size: Optional[str] = Form("1024x1024"), #256x256, 512x512, or 1024x1024 for dall-e-2.
        response_format: Optional[str] = Form("url"), # or b64_json
        n: Optional[int] = Form(1), # 1-10
        user: Optional[str] = Form(None),
    ):
    # Steps:
    # 1) latent up scale input image to 1M pixel (if needed), or bicubic scale down
    # 2) call img2img with sdxl_lighting defaults, include scaling of output images(s) to output sizes if needed
    # get original image size
    resp = {
        'created': int(time.time()),
        'data': []
    }

    width, height = size.split('x')

    # TODO: select backend model by config
    rg = sdxl_lightning_request_generator()
        
    req = await rg.create_variation(image, int(width), int(height), n)
    print(req)

    imgs = await sd_request(req, "img2img")

    if imgs:
        for b64_json in imgs:
            if response_format == 'b64_json':
                img_dat = {'b64_json': b64_json}
            else:
                # TODO: use files API to post this image and return a URL - or reverse engineer the SD URL to get a direct link to the image.
                img_dat = {'url': f'data:image/png;base64,{b64_json}'}  # yeah it's lazy. requests.get() will not work with this, but web clients will

            resp['data'].extend([img_dat])

    return resp

def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description='OpenedAI Images API Server',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    #CONF_PATH = 'config/config.json'
    #SD_BASE_URL = os.environ['SD_BASE_URL'] # f"{SD_BASE_URL}/sdapi/v1/txt2img"
    #OPENAI_BASE_URL = os.environ.get('OPENAI_BASE_URL', None) # for dall-e-3 enhanced prompts
    # args or env:
    parser.add_argument('-C', '--config', action='store', default='config/config.json', help="Path to config file")
    parser.add_argument('-P', '--port', action='store', default=5005, type=int, help="Server tcp port")
    parser.add_argument('-H', '--host', action='store', default='localhost', help="Host to listen on, Ex. 0.0.0.0")

    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args(sys.argv[1:])

    # load config
    if not os.path.exists(args.config):

    with open(args.config) as f:
        #app/main.py
        config = yaml.safe_load(f)


    # TODO: monitor SD health
    app.register_model('dall-e-1')
    app.register_model('dall-e-2')
    app.register_model('dall-e-3')

    uvicorn.run(app, host=args.host, port=args.port) # , root_path=cwd, access_log=False, log_level="info", ssl_keyfile="cert.pem", ssl_certfile="cert.pem")
