#!/usr/bin/env python3
import os
import sys
import time
import json
import math
import argparse

import requests

from typing import Optional, List
from fastapi import UploadFile, Form
import uvicorn
from pydantic import BaseModel

import openedai

pipe = None
app = openedai.OpenAIStub()

CONF_PATH = 'config'
SD_BASE_URL = os.environ['SD_BASE_URL'] # f"{SD_BASE_URL}/sdapi/v1/txt2img"
OPENAI_BASE_URL = os.environ.get('OPENAI_BASE_URL', None) # for dall-e-3 enhanced prompts

if OPENAI_BASE_URL:
    import openai
    openai_client = openai.Client()

#class ImageResponse:
#    b64_json: str
#    url: str
#    revised_prompt: str

async def OpenDallePrompt(prompt):
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

Write everything in 1 sentence (not a list), separating with commas, in English, strictly following the instruction (especially the number of words)."""},
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

        if scale >= 1.2:
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

class sd15_request_generator(txt2img_request_generator):
    base_model_size: int = 512
    default_conf_path: str = f'{CONF_PATH}/default_sd15_conf.json'

class sdxl_lightning_request_generator(txt2img_request_generator):
    base_model_size = 1024
    default_conf_path = f'{CONF_PATH}/default_sdxl_lightning_conf.json'

class sdxl_request_generator(txt2img_request_generator):
    base_model_size = 1024
    default_conf_path = f'{CONF_PATH}/default_sdxl_conf.json'

async def generations_request(payload):
    response = requests.post(url=f"{SD_BASE_URL}/sdapi/v1/txt2img", json=payload)
    r = response.json()
    if response.status_code != 200 or 'images' not in r:
        #raise ServiceUnavailableError(r.get('error', 'Unknown error calling Stable Diffusion'), code=response.status_code, internal_message=r.get('errors', None))
        print(r)
        return []
    
    return r['images']

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
            request.prompt = revised_prompt = await OpenDallePrompt(request.prompt)

    req = rg.create_request(request.prompt, int(width), int(height), request.n)
    print(req)

    imgs = await generations_request(req)

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


class VariationsRequest(BaseModel):
    image: UploadFile
    model: str = Form("dall-e-2") # only dall-e-2
    size: Optional[str] = Form("1024x1024") #256x256, 512x512, or 1024x1024 for dall-e-2.
    response_format: Optional[str] = Form("url") # or b64_json
    n: Optional[int] = Form(1) # 1-10
    user: Optional[str] = None

@app.post("/v1/images/variations")
async def variations(request: VariationsRequest):
    pass


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description='OpenedAI Images API Server',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-P', '--port', action='store', default=5005, type=int, help="Server tcp port")
    parser.add_argument('-H', '--host', action='store', default='localhost', help="Host to listen on, Ex. 0.0.0.0")

    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args(sys.argv[1:])

    # TODO: monitor SD health
    app.register_model('dall-e-1')
    app.register_model('dall-e-2')
    app.register_model('dall-e-3')

    uvicorn.run(app, host=args.host, port=args.port) # , root_path=cwd, access_log=False, log_level="info", ssl_keyfile="cert.pem", ssl_certfile="cert.pem")
