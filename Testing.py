# Run the Following code in terminal to start the main code :
# python yolov7/detect.py --weights model/yolov7-tiny.pt --conf 0.25 --img-size 640 --source http://192.168.29.188:8080/video?type=some.mjpeg --class 0


# TODO : 1. Once you removed all the unnecessary stuff you can bring all the code from yolov7 outside or you can keep it inside and change the folder name to may be  core and run the above command from root folder.


# from notebook_utils import download_file
# from .openvino_notebooks.notebooks.utils.notebook_utils import download_file
# import openvino_notebooks.notebooks.utils.notebook_utils as note
from notebook_utils import download_file
import sys
from pathlib import Path
sys.path.append("../utils")


# Download pre-trained model weights
MODEL_LINK = "https://github.com/WongKinYiu/yolov7/releases/download/v0.1/yolov7-tiny.pt"
DATA_DIR = Path("data/")
MODEL_DIR = Path("model/")
MODEL_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

# download_file(MODEL_LINK, directory=MODEL_DIR, show_progress=True)


# !python - W ignore yolov7/detect.py - -weights model/yolov7-tiny.pt - -conf 0.25 - -img-size 640 - -source yolov7/inference/images/horses.jpg


# To test if the device is connected to your pc or not :

#from openvino.runtime import Core

#core = Core()

#devices = core.available_devices

# for device in devices:
#    device_name = core.get_property(device, "FULL_DEVICE_NAME")
#    print(f"{device}: {device_name}")


# you should able to see the MyriadX in the list.
