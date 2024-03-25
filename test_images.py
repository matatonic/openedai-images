import base64
import io
import openai
from PIL import Image

client = openai.Client(base_url='http://localhost:5005/v1')
response = client.images.generate(prompt="A cute baby sea otter", response_format='b64_json')
image = Image.open(io.BytesIO(base64.b64decode(response.data[0].b64_json)))
image.show()
