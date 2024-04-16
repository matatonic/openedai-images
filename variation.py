#!/usr/bin/env python
import base64
import argparse
import sys
import os
import io
import time
from PIL import Image
import openai

client = openai.Client(base_url='http://localhost:5005/v1', api_key="sk-ip")

def parse_args(argv=None):
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('image', action='store', type=str)
    parser.add_argument('-n', '--batch', action='store', type=int, default=1)

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args(sys.argv[1:])

    t = int(time.time())
    name, ext = os.path.splitext(os.path.basename(args.image))
    response = client.images.create_variation(
        model='dall-e-2',
        image=open(args.image, 'rb'),
        n=args.batch,
        response_format='b64_json'
    )

    for i, resp in enumerate(response.data, 1):
        vimg = Image.open(io.BytesIO(base64.b64decode(resp.b64_json)))
        fname = f"{name}-{t}-{i:02d}-of-{args.batch:02d}{ext}"
        vimg.save(fname)
        print(fname)
