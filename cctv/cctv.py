import cv2
import numpy as np
import cvui
rtsp_username = "admin"
rtsp_password = "crl@12345"
width = 800
height = 480
cam_no = 1

#recognizer = cv2.face.LBPHFaceRecognizer_create()
#recognizer.read('home/ram/Downloads/Exp33/trainner/trainner.yml')
cascadePath = "/home/ram/Downloads/Exp33/haarcascade_frontalface_default.xml"
faceCascade = cv2.CascadeClassifier(cascadePath);

def create_camera (channel):
#    rtsp = "rtsp://" + rtsp_username + ":" + rtsp_password + "@192.168.0.102:554/Streaming/channels/" + channel + "02" #change the IP to suit yours
    rtsp = "rtsp://admin:Crl@12345@192.168.0.102:554/cam/realmonitor?channel=3&subtype=0"
    cap = cv2.VideoCapture()
    cap.open(rtsp)
    cap.set(3, 640)  # ID number for width is 3
    cap.set(4, 480)  # ID number for height is 480
    cap.set(10, 100)  # ID number for brightness is 10qq
    return cap
cam = create_camera(str(cam_no))
cvui.init('screen')
while True:
    success, current_cam = cam.read()
    dim = (width, height)
    Full_frame = cv2.resize(current_cam, dim, interpolation=cv2.INTER_AREA)
    cv2.namedWindow('screen', cv2.WINDOW_NORMAL)
    cv2.setWindowProperty('screen', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    gray=cv2.cvtColor(current_cam,cv2.COLOR_BGR2GRAY)
    faces=faceCascade.detectMultiScale(gray, 1.2,5)
    for(x,y,w,h) in faces:
        cv2.rectangle(current_cam, (x,y),(x+w,y+h),(225,0,0),2)
#        Id, conf = recognizer.predict(gray[y:y+h,x:x+w])
#        print(Id)
#        print(conf)
#        if(conf>40):
#            if(Id==1):
#                Id="Ram"
#            elif(Id==2):
#                Id="elakki"
##            elif(Id==3):
##                Id="Aadharsh"
#        else:
#            Id="Unknown"
##        cv2.putText(cv2.fromarray(im),str(Id), (x,y+h),font, 255)
##        cv2.putText(im,str(Id), (x,y+h),font, 255,None)
        cv2.putText(current_cam,str(Id),(x,y+h),cv2.FONT_HERSHEY_SIMPLEX, 1,(255,255,255))
    cv2.imshow('im',current_cam) 
    if cv2.waitKey(10) & 0xFF==ord('q'):
        break
 
    if (cvui.button(Full_frame, width - 100, height - 40, "Next") and cvui.mouse(cvui.CLICK)):
        print("Next Button Pressed")
        cvui.init('screen')
        cam_no = cam_no+1
        if (cam_no>4):
            cam_no=1
        del cam
        cam = create_camera(str(cam_no))
    if (cvui.button(Full_frame, width - 200, height - 40, "Previous") and cvui.mouse(cvui.CLICK)):
        print("Previous Button Pressed")
        cvui.init('screen')
        cam_no = cam_no - 1
        if (cam_no<1):
            cam_no=4
        del cam
        cam = create_camera(str(cam_no))
#    cv2.imshow('screen', Full_frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        cv2.destroyAllWindows()
        break
cam.release()
cv2.destroyAllWindows()

