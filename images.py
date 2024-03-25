#!/usr/bin/env python3
import os
import sys
import time
import json
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

#class ImageResponse:
#    b64_json: str
#    url: str
#    revised_prompt: str

async def sdxl_lightning_generate(prompt, width, height, n):
    base_model_size = 1024

    conf_file = f'{CONF_PATH}/default_sdxl_lightning_conf.json'
    default_conf = {
        'sampler_name': 'DPM++ SDE',
        'refiner_checkpoint': None,
        'refiner_switch_at': 0.0,
        'VAE': None,
        'steps': 4,
        'cfg_scale': 1.0,
    }

    if os.path.exists(conf_file):
        with open(conf_file, 'r') as f:
            default_conf = json.load(f)

    payload = {
        'prompt': prompt,  # ignore prompt limit of 1000 characters
        'width': width,
        'height': height,
        'batch_size': n,
    }
    payload.update(default_conf)

    scale = min(width, height) / base_model_size
    if scale >= 1.2:
        # for better performance with the default size (1024), and larger res, add an upscaler
        scaler = {
            'width': width // scale,
            'height': height // scale,
            'hr_scale': scale,
            'enable_hr': True,
            'hr_upscaler': 'Latent',
            'denoising_strength': 0.68,
        }
        payload.update(scaler)

    resp = {
        'created': int(time.time()),
        'data': []
    }

    response = requests.post(url=f"{SD_BASE_URL}/sdapi/v1/txt2img", json=payload)
    r = response.json()
    if response.status_code != 200 or 'images' not in r:
        #raise ServiceUnavailableError(r.get('error', 'Unknown error calling Stable Diffusion'), code=response.status_code, internal_message=r.get('errors', None))
        print(r)
        return []
    
    return r['images']

async def sd15_generate(prompt, width, height, n):
    base_model_size = 512

    conf_file = f'{CONF_PATH}/default_sd15_conf.json'
    default_conf = {
        'sampler_name': 'DPM++ 2M Karras',
        'steps': 30,
    }

    if os.path.exists(conf_file):
        with open(conf_file, 'r') as f:
            default_conf = json.load(f)

    payload = {
        'prompt': prompt,  # ignore prompt limit of 1000 characters
        'width': width,
        'height': height,
        'batch_size': n,
    }
    payload.update(default_conf)

    scale = min(width, height) / base_model_size
    if scale >= 1.2:
        # for better performance with the default size (1024), and larger res, add an upscaler
        scaler = {
            'width': width // scale,
            'height': height // scale,
            'hr_scale': scale,
            'enable_hr': True,
            'hr_upscaler': 'Latent',
            'denoising_strength': 0.68,
        }
        payload.update(scaler)

    resp = {
        'created': int(time.time()),
        'data': []
    }

    response = requests.post(url=f"{SD_BASE_URL}/sdapi/v1/txt2img", json=payload)
    r = response.json()
    if response.status_code != 200 or 'images' not in r:
        #raise ServiceUnavailableError(r.get('error', 'Unknown error calling Stable Diffusion'), code=response.status_code, internal_message=r.get('errors', None))
        print(r)
        return []
    
    return r['images']

async def sdxl_generate(prompt, width, height, n):
    base_model_size = 1024

    conf_file = f'{CONF_PATH}/default_sdxl_conf.json'
    default_conf = {
        'sampler_name': 'DPM++ 2S a Karras',
        'refiner_checkpoint': 'sd_xl_refiner_1.0.safetensors',
        'refiner_switch_at': 0.8,
        'VAE': 'fixFP16ErrorsSDXLLowerMemoryUse_v10.safetensors',
        'steps': 40,
    }

    if os.path.exists(conf_file):
        with open(conf_file, 'r') as f:
            default_conf = json.load(f)

    payload = {
        'prompt': prompt,  # ignore prompt limit of 1000 characters
        'width': width,
        'height': height,
        'batch_size': n,
    }
    payload.update(default_conf)

    scale = min(width, height) / base_model_size
    if scale >= 1.2:
        # for better performance with the default size (1024), and larger res, add an upscaler
        scaler = {
            'width': width // scale,
            'height': height // scale,
            'hr_scale': scale,
            'enable_hr': True,
            'hr_upscaler': 'Latent',
            'denoising_strength': 0.68,
        }
        payload.update(scaler)

    resp = {
        'created': int(time.time()),
        'data': []
    }

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
    n: Optional[int] = 1 # 1-10, 1 only for dalle-3
    style: Optional[str] = "vivid" # natural
    user: Optional[str] = None


@app.post("/v1/images/generations")
async def generations(request: GenerationsRequest):

    resp = {
        'created': int(time.time()),
        'data': []
    }

    width, height = request.size.split('x')

    # TODO: select backend model by config
    if request.model == 'dall-e-1':
        imgs = await sd15_generate(request.prompt, int(width), int(height), request.n)
    elif request.model == 'dall-e-2':
        imgs = await sdxl_lightning_generate(request.prompt, int(width), int(height), request.n)
    else:
        imgs = await sdxl_generate(request.prompt, int(width), int(height), request.n)

    if imgs:
        for b64_json in imgs:
            if request.response_format == 'b64_json':
                resp['data'].extend([{'b64_json': b64_json}])
            else:
                resp['data'].extend([{'url': f'data:image/png;base64,{b64_json}'}])  # yeah it's lazy. requests.get() will not work with this

    return resp

@app.post("/v1/images/edits")
async def edits(
        image: UploadFile,
        prompt: str = Form(...),
        mask: Optional[UploadFile] = None,
        model: str = Form("dall-e-2"), # only dall-e-2
        size: Optional[str] = Form("1024x1024"), #256x256, 512x512, or 1024x1024 for dall-e-2.
        response_format: Optional[str] = Form("url"), # or b64_json
        n: Optional[int] = Form(1), # 1-10, 1 only for dalle-3
        user: Optional[str] = None,
    ):
    pass


@app.post("/v1/images/variations")
async def variations(
        image: UploadFile,
        model: str = Form("dall-e-2"), # only dall-e-2
        size: Optional[str] = Form("1024x1024"), #256x256, 512x512, or 1024x1024 for dall-e-2.
        response_format: Optional[str] = Form("url"), # or b64_json
        n: Optional[int] = Form(1), # 1-10
        user: Optional[str] = None,
    ):
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

    app.register_model('dall-e-1')
    app.register_model('dall-e-2')
    app.register_model('dall-e-3')

    uvicorn.run(app, host=args.host, port=args.port) # , root_path=cwd, access_log=False, log_level="info", ssl_keyfile="cert.pem", ssl_certfile="cert.pem")
