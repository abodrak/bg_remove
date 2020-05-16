from flask import Flask

import io
import os
from flask import Flask, request, jsonify, send_file
from PIL import Image
import time
from datetime import datetime
import requests
import logging

app = Flask(__name__)


host = 'http://95.217.218.75:3000/'

@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/cut', methods=['POST'])
def save():
    start = time.time()
    logging.info(' CUT')

    # Convert string of image data to uint8.
    if 'data' not in request.files:
        return jsonify({
            'status': 'error',
            'error': 'missing file param `data`'
        }), 400
    data = request.files['data'].read()
    if len(data) == 0:
        return jsonify({'status:': 'error', 'error': 'empty image'}), 400

    # Save debug locally.
    with open('cut_received.jpg', 'wb') as f:
        f.write(data)

    # Send to BASNet service.
    logging.info(' > sending to BASNet...')
    headers = {}
    headers['Host'] = host

    files = {'data': open('cut_received.jpg', 'rb')}
    res = requests.post(host, headers=headers, files=files)

    logging.info(res.status_code)

    # Save mask locally.
    logging.info(' > saving results...')
    with open('cut_mask.png', 'wb') as f:
        f.write(res.content)
        # shutil.copyfileobj(res.raw, f)

    logging.info(' > opening mask...')
    mask = Image.open('cut_mask.png').convert("L")
    mask = mask.resize((256, 256), Image.ANTIALIAS)

    print(mask.size)

    # Convert string data to PIL Image.
    logging.info(' > compositing final image...')
    ref = Image.open(io.BytesIO(data))
    ref = ref.resize((256, 256), Image.ANTIALIAS)

    print(ref.size)
    empty = Image.new("RGBA", ref.size, 0)
    img = Image.composite(ref, empty, mask)

    # TODO: currently hack to manually scale up the images. Ideally this would
    # be done respective to the view distance from the screen.
    img_scaled = img.resize((img.size[0] * 3, img.size[1] * 3))

    # Save locally.
    logging.info(' > saving final image...')
    img_scaled.save('cut_current.png')

    # Save to buffer
    buff = io.BytesIO()
    img.save(buff, 'PNG')
    buff.seek(0)

    # Print stats

    # Return data
    return send_file(buff, mimetype='image/png')






if __name__ == '__main__':
    app.run()
