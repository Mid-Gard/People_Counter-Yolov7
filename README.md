# People Counter Using ML

## Features
- Added Label for Every Track
- Code can run on Both (CPU & GPU)
- Video/WebCam/External Camera/IP Stream Supported
- Can store the footage for future reference in compressed format to save storage space and time.
- Also stores the data in text format.

## Steps to run Code
- Clone the repository.

- Goto the cloned folder.
```
cd UsingYolov7
```
- Create a  envirnoment (Recommended, If you dont want to disturb python packages)

- Install all the packages :
```
### For Linux Users
python3 -m pip install -r requirements.txt

### For Window Users
cd yolov7objtracking
python3 -m pip install -r requirements.txt
```

- Give the IP address of the Camera in the cofig.py file, just replace the value of the varialbe `IP_Url` with IP address of the webcam.

- Run the project:
```
python detect.py
```
