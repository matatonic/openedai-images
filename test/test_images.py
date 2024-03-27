#!/usr/bin/env python
import base64
import io
import time
import openai
from PIL import Image

client = openai.Client(base_url='http://localhost:5005/v1')

def generate_image(prompt, model, res, f):
	start = time.time()
	response = client.images.generate(prompt=prompt, model=model, size=res, response_format='b64_json')
	#image = Image.open(io.BytesIO(base64.b64decode(response.data[0].b64_json)))
	#image.show()
	end = time.time()
	for img in response.data:
		fname = f"test_image_{model}_{res}.png"
		with open(fname, 'wb') as png:
			png.write(base64.b64decode(img.b64_json))
		# markdown record the details of the test, including any extra revised_prompt
		print(f"## {model} {res} took {end-start:.1f} seconds", file=f)
		print(f"![{prompt}]({fname})", file=f)
		if img.revised_prompt:
			print("revised_prompt: " + img.revised_prompt, file=f)
		print("\n", file=f)

	print("-"*50, file=f)
	print("\n", file=f)

if __name__ == '__main__':
	prompt = "A cute baby sea otter"
	for model in ['dall-e-1', 'dall-e-2']:
		with open(f"test_images-{model}.md", "w") as f:
			print(f"# {prompt}", file=f)
			for res in ['256x256', '512x512', '1024x1024']:
				generate_image(prompt, model, res, f)

	model = 'dall-e-3'
	with open(f"test_images-{model}.md", "w") as f:
		print(f"# {prompt}", file=f)
		for res in ['1024x1024', '1024x1796', '1796x1024']:
			generate_image(prompt, model, res, f)

