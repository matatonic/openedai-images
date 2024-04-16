#!/usr/bin/env python
import base64
import time
import argparse
import sys
import os
import io
from PIL import Image
import openai

client = openai.Client(base_url='http://localhost:5005/v1', api_key='sk-ip')

TEST_DIR = 'test'
not_enhanced = "I NEED to test how the tool works with extremely simple prompts. DO NOT add any detail, just use it AS-IS:"

def generate_image(prompt, model, res, f, n = 1, suffix=''):
    start = time.time()
    response = client.images.generate(prompt=prompt, model=model, size=res, response_format='b64_json', n=n)
    #image = Image.open(io.BytesIO(base64.b64decode(response.data[0].b64_json)))
    #image.show()
    end = time.time()
    print(f"## {model} {res} took {end-start:.1f} seconds", file=f)

    for i, img in enumerate(response.data, 1):
        fname = f"test_image_{model}_{res}{suffix}-{i:02d}_{n:02d}.png"
        with open(f'{TEST_DIR}/{fname}', 'wb') as png:
            png.write(base64.b64decode(img.b64_json))
        # markdown record the details of the test, including any extra revised_prompt
        print(f"![{prompt}]({fname})", file=f)
        if img.revised_prompt:
            print("revised_prompt: " + img.revised_prompt, file=f)
        print("\n", file=f, flush=True)

    print("-"*50, file=f)
    print("\n", file=f, flush=True)

def full_test(prompt, n=1):
    for model in ['dall-e-1', 'dall-e-2']:
        with open(f"{TEST_DIR}/test_images-{model}.md", "w") as f:
            print(f"# {prompt}", file=f)
            for res in ['256x256', '512x512', '1024x1024']:
                generate_image(prompt, model, res, f, n=n)

    model = 'dall-e-3'
    with open(f"{TEST_DIR}/test_images-{model}.md", "w") as f:
        print(f"# {prompt}", file=f)
        for res in ['1024x1024', '1024x1796', '1796x1024']:
            generate_image(prompt, model, res, f, n=n)
            generate_image(not_enhanced + prompt, model, res, f, n=n, suffix='-not-enhanced')

def quick_test(prompt, n=1):
    with open(f"{TEST_DIR}/test_images_quick.md", "w") as f:
        print(f"# {prompt}", file=f)
        generate_image(prompt, "dall-e-1", "512x512", f, n=n)
        generate_image(prompt, "dall-e-1", "1024x1024", f, n=n)
        generate_image(prompt, "dall-e-2", "1024x1024", f, n=n)
        generate_image(not_enhanced + prompt, "dall-e-3", "1024x1024", f, n=n, suffix='-not-enhanced')
        generate_image(prompt, "dall-e-3", "1024x1024", f, n=n)

def parse_args(argv=None):
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-p', '--prompt', action='store', type=str, default="A cute baby sea otter")
    parser.add_argument('-q', '--quick', action='store_true')
    parser.add_argument('-f', '--full', action='store_true')
    parser.add_argument('-n', '--batch', action='store', type=int, default=1)
    parser.add_argument('-t', '--test-dir', action='store', type=str, default='test')

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args(sys.argv[1:])

    TEST_DIR = args.test_dir
    os.makedirs(TEST_DIR, exist_ok=True)

    if args.quick:
        quick_test(args.prompt, n=args.batch)
    elif args.full:
        full_test(args.prompt, n=args.batch)



