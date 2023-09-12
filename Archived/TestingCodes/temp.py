from flask import Flask, render_template, jsonify, request
import cv2
import requests
import io
import config
import threading
import time

app = Flask(__name__)
num_people = 0
img = None

def update_image():
    global num_people, img
    while True:
        IPcamURL = "http://192.168.0.104:8080/video?type=some.mjpeg"
        cap = cv2.VideoCapture(IPcamURL)
        ret, frame = cap.read()
        if ret:
            img_data = cv2.imencode('.jpg', frame)[1].tobytes()
            # num_people += 1  # Example: Increment num_people for testing purposes
            img = img_data
            data = {'num_people': num_people, 'image_data': img.decode('latin1')}
            requests.post("http://localhost:5000/final_data", json=data)
        else:
            print("No frame captured")
        cap.release()
        time.sleep(1)

# def send_final_data():
#     global num_people, img
#     while True:
#         data = {'num_people': num_people, 'image_data': img.decode('latin1')}
#         requests.post("http://localhost:5000/final_data", json=data)
#         time.sleep(1)

@app.route('/')
def index():
    global num_people, img
    data = {'num_people': num_people, 'image_data': img.decode('latin1')}  # Convert bytes to string
    return render_template('index.html')

@app.route('/get_data', methods=['GET'])
def get_data():
    global num_people, img
    data = {'num_people': num_people}
    return jsonify(data)

@app.route('/final_data', methods=['POST'])
def final_data():
    global num_people, img
    # data = request.get_json()
    # Process the received data
    # num_people = data['num_people']
    # img = data['image_data'].encode('latin1')
    # Perform desired operations with the received data
    # ...
    return jsonify({'success': True})

@app.route('/update_data', methods=['POST'])
def update_data():
    # Get the image from the request
    image_file = request.files['num_people']
    image_data = image_file.read()
    # nparr = np.fromstring(image_data, np.uint8)
    # im = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # Process the image and return a response
    # num_ppl = detect_people(im)
    response_data = {'num_ppl': image_file}
    return jsonify(response_data)


if __name__ == '__main__':
    # update_thread = threading.Thread(target=update_image)
    # update_thread.start()
    #
    # send_final_data_thread = threading.Thread(target=send_final_data)
    # send_final_data_thread.start()
    update_image()
    # time.sleep(1)
    # send_final_data()

    app.run()













# from flask import Flask, render_template, request, jsonify
# import cv2
# import io
# import requests
# import config
# import time
#
# app = Flask(__name__)
#
# def SendData(frame, num_people):
#     try:
#         Serverurl = "http://localhost:5000/update_data"
#         data = {'num_people': num_people, 'image_data': frame}
#         response = requests.post(Serverurl, json=data)
#         print(data)
#     except:
#         print('Error: The WebApp is Down')
#
# @app.route('/update_data', methods=['POST'])
# def update_data():
#     data = request.get_json()
#     # Process the received data
#     num_people = data['num_people']
#     frame = data['image_data']
#     # Perform desired operations with the received data
#     # ...
#     return jsonify({'success': True})
#
# @app.route('/get_data', methods=['GET'])
# def get_data():
#     # Perform desired operations to retrieve data
#     # ...
#     return jsonify({'data': 'sample data'})
#
# @app.route('/', methods=['GET'])
# def index():
#     # Perform operations to get the data from /get_data
#     # ...
#     # Pass the data to the template
#     return render_template('index.html', data=data)
#
# def updateImage(num_people):
#     global current_frame, img_label, count_label, img_path
#     num_people = num_people
#     while True:
#         IPcamURL = config.ip_addr
#         cap = cv2.VideoCapture(IPcamURL)
#         ret, frame = cap.read()
#         if ret:
#             img_data = io.BytesIO()
#             cv2.imwrite(img_data, frame)
#             img_data.seek(0)
#             SendData(img_data.read(), num_people)
#             time.sleep(20)
#         else:
#             print("No frame captured")
#         cap.release()
#
# if __name__ == '__main__':
#     app.run()
