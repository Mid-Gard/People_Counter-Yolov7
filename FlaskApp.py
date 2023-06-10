
# TODO : if you can make the algorithm a little bit faster i can direclty shwo the streame in the html only the number updation will be slower.



from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

num_people = 10

@app.route('/')
def index():
    global num_people
    return render_template("index.html", num_people=num_people)

@app.route('/update_data', methods=['POST'])
def update_data():
    global num_people
    while True:
        # Receive the posted data
        requestss = request.json
        num_people = requestss['num_people']

        return 'Data updated successfully!'


@app.route('/get_data', methods=['GET'])
def get_data():
    global num_people, img
    num_people_modified = num_people[3:]  # Remove the first three characters
    data = {'num_people': num_people_modified}
    return jsonify(data)


if __name__ == '__main__':
    app.run()

# from flask import Flask, render_template, jsonify
# import cv2
# import io
# import config
# import threading
# import time
# app = Flask(__name__)
# num_people = 0
# img = None
#
# def update_image():
#     global num_people, img
#     while True:
#         IPcamURL = config.IP_Url
#         cap = cv2.VideoCapture(IPcamURL)
#         ret, frame = cap.read()
#         if ret:
#             img_data = cv2.imencode('.jpg', frame)[1].tobytes()
#             num_people += 1  # Example: Increment num_people for testing purposes
#             img = img_data
#         else:
#             print("No frame captured")
#         cap.release()
#         time.sleep(1)
#
# @app.route('/')
# def index():
#     global num_people, img
#     data = {'num_people': num_people, 'image_data': img.decode('latin1')}  # Convert bytes to string
#     return render_template('index.html', data=data)
#
# @app.route('/get_data', methods=['GET'])
# def get_data():
#     global num_people, img
#     data = {'num_people': num_people, 'image_data': img.decode('latin1')}
#     return jsonify(data)
#
# if __name__ == '__main__':
#     update_thread = threading.Thread(target=update_image)
#     update_thread.start()
#     app.run()







# from flask import Flask, jsonify, request, render_template
# import cv2
# import numpy as np
#
# app = Flask(__name__)
#
#
# @app.route('/')
# def index():
#     # Load the image from disk
#     image_path = 'path/to/image.jpg'
#     im = cv2.imread(image_path)
#
#     # Convert the image to JPEG format and encode it as base64
#     _, jpeg = cv2.imencode('.jpg', im)
#     b64 = base64.b64encode(jpeg.tobytes()).decode()
#
#     # Render the image in an HTML template
#     return render_template('index.html', image_data=b64)
# @app.route('/update_data', methods=['POST'])
# def update_data():
#     # Get the image from the request
#     image_file = request.files['image']
#     image_data = image_file.read()
#     nparr = np.fromstring(image_data, np.uint8)
#     im = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
#
#     # Process the image and return a response
#     num_ppl = detect_people(im)
#     response_data = {'num_ppl': num_ppl}
#     return jsonify(response_data)
#
#
# @app.route('/view_data', methods=['GET'])
# def view_data():
#     # Load the image from disk
#     image_path = 'path/to/image.jpg'
#     im = cv2.imread(image_path)
#
#     # Convert the image to JPEG format and encode it as base64
#     _, jpeg = cv2.imencode('.jpg', im)
#     b64 = base64.b64encode(jpeg.tobytes()).decode()
#
#     # Render the image in an HTML template
#     return render_template('view_data.html', image_data=b64)
#
#
#
#
# if __name__ == '__main__':
#     app.run(debug=True)
