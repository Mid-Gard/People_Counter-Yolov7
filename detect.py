import argparse
import time
from pathlib import Path
import requests
import cv2
import torch
import torch.backends.cudnn as cudnn
from numpy import random
import os
import datetime

# Custom Modules
import config
from models.experimental import attempt_load
from utils.datasets import LoadStreams, LoadImages
from utils.general import check_img_size, check_imshow, non_max_suppression, apply_classifier, \
    scale_coords, xyxy2xywh, strip_optimizer, set_logging, \
    increment_path
from utils.plots import plot_one_box
from utils.torch_utils import select_device, load_classifier, time_synchronized, TracedModel


def detect(save_img=False):
    source, weights, view_img, save_txt, imgsz, trace, webApp = opt.source, opt.weights, opt.view_img, opt.save_txt, opt.img_size, not opt.no_trace, opt.webApp
    # source = config.IP_Url
    source='sources.txt'
    weights = 'yolov7.pt'
    # save_img = not opt.nosave and not source.endswith('.txt')  # save inference images, That is basically if you are storing all teh Ip webcame in the soruces.txt then since all are not of same resolution, it makes the save_img flag False so it dont save the footage.
    save_img = True # Okay so the problem is if you are using multiple cameras of defferent resolution, then it creates a video, but it doest have the higer reso camera frames.
    save_txt = True
    webcam = source.isnumeric() or source.endswith('.txt') or source.lower().startswith(
        ('rtsp://', 'rtmp://', 'http://', 'https://'))

    # Directories
    today_date = datetime.datetime.now().strftime("%Y-%m-%d")  # Get today's date in YYYY-MM-DD format
    opt.project = 'Output/'+today_date
    current_time = datetime.datetime.now().strftime("%H-%M-%S")
    opt.name = ''
    # save_dir = Path(increment_path(Path(opt.project), exist_ok=opt.exist_ok))  # increment run
    save_dir = Path(opt.project, exist_ok=opt.exist_ok)  # increment run
    (save_dir if save_txt else save_dir).mkdir(parents=True, exist_ok=True)  # make dir


    # Initialize
    set_logging()
    device = select_device(opt.device)
    half = device.type != 'cpu'  # half precision only supported on CUDA

    # Load model
    model = attempt_load(weights, map_location=device)  # load FP32 model
    stride = int(model.stride.max())  # model stride
    imgsz = check_img_size(imgsz, s=stride)  # check img_size


    if trace:
        model = TracedModel(model, device, opt.img_size)

    if half:
        model.half()  # to FP16

    # Second-stage classifier
    classify = False
    if classify:
        modelc = load_classifier(name='resnet101', n=2)  # initialize
        modelc.load_state_dict(torch.load('weights/resnet101.pt', map_location=device)['model']).to(device).eval()

    # Set Dataloader
    vid_path, vid_writer = None, None
    if webcam:
        view_img = check_imshow()
        cudnn.benchmark = True  # set True to speed up constant image size inference
        dataset = LoadStreams(source, img_size=imgsz, stride=stride)
    else:
        dataset = LoadImages(source, img_size=imgsz, stride=stride)

    # Get names and colors
    names = model.module.names if hasattr(model, 'module') else model.names
    colors = [[random.randint(0, 255) for _ in range(3)] for _ in names]

    # Run inference
    if device.type != 'cpu':
        model(torch.zeros(1, 3, imgsz, imgsz).to(device).type_as(next(model.parameters())))  # run once
    old_img_w = old_img_h = imgsz
    old_img_b = 1


    for path, img, im0s, vid_cap in dataset:
        t0 = time.time()
        img = torch.from_numpy(img).to(device)
        img = img.half() if half else img.float()  # uint8 to fp16/32
        img /= 255.0  # 0 - 255 to 0.0 - 1.0
        if img.ndimension() == 3:
            img = img.unsqueeze(0)

        # Warmup
        if device.type != 'cpu' and (
                old_img_b != img.shape[0] or old_img_h != img.shape[2] or old_img_w != img.shape[3]):
            old_img_b = img.shape[0]
            old_img_h = img.shape[2]
            old_img_w = img.shape[3]
            for i in range(3):
                model(img, augment=opt.augment)[0]

        # Inference
        t1 = time_synchronized()
        pred = model(img, augment=opt.augment)[0]
        t2 = time_synchronized()

        modelDelay = t2 - t0
        # print(f'The Model Delay : {modelDelay}')

        # Apply NMS
        pred = non_max_suppression(pred, opt.conf_thres, opt.iou_thres, classes=opt.classes, agnostic=opt.agnostic_nms)
        t3 = time_synchronized()

        NMSDelay = t3 - t2
        # print(f'The Model Delay : {NMSDelay}')

        # Apply Classifier
        if classify:
            pred = apply_classifier(pred, modelc, img, im0s)

        # Process detections
        for i, det in enumerate(pred):  # detections per image
            if webcam:  # batch_size >= 1
                p, s, im0, frame = path[i], '%g: ' % i, im0s[i].copy(), dataset.count
            else:
                p, s, im0, frame = path, '', im0s, getattr(dataset, 'frame', 0)

            p = Path(p)  # to Path
            # current_time = datetime.datetime.now().strftime("%H-%M-%S")
            save_path = str(save_dir / current_time)  # img.jpg
            txt_path = str(save_dir /  current_time)  # img.txt
            gn = torch.tensor(im0.shape)[[1, 0, 1, 0]]  # normalization gain whwh
            if len(det):
                # Rescale boxes from img_size to im0 size
                det[:, :4] = scale_coords(img.shape[2:], det[:, :4], im0.shape).round()

                # Print results
                for c in det[:, -1].unique():
                    n = (det[:, -1] == c).sum()  # detections per class
                    # s += f"{n} {names[int(c)]}{'s' * (n > 1)}, "  # This line creates for all types of objects but i need for only person, hence use below line.
                    s += f"{n} {names[int(c)]}{'s' * (n > 1)}"

                frame_time = datetime.datetime.now().strftime("%H-%M-%S")
                if save_txt and not dataset.mode == 'image':  # Write to file normalized xywh
                    with open(txt_path + '.txt', 'a') as f:
                        f.write(('\nTime : '+ frame_time+ '\nRESULT : ' + s))

                # Only do this if you are showing the cv window
                if view_img:
                    # Write results in txt file and draw box in the image
                    for *xyxy, conf, cls in reversed(det):
                        # Enable Below code if you want to save the confidence
                        if save_txt and not dataset.mode == 'image':  # Write to file
                            xywh = (xyxy2xywh(torch.tensor(xyxy).view(1, 4)) / gn).view(-1).tolist()  # normalized xywh
                            line = (cls, *xywh, conf) if opt.save_conf else (cls, *xywh)  # label format
                            with open(txt_path + '.txt', 'a') as f:
                                f.write(('\nProbability :'+ ' %g ' * len(line)).rstrip() % line + '\n')
                        # Add bbox to image
                        if save_img or view_img:
                            label = f'{names[int(cls)]} {conf:.2f}'
                            plot_one_box(xyxy, im0, label=label, color=colors[int(cls)], line_thickness=1)

            # Print time (inference + NMS)
            # print(f'{s}Done. ({(1E3 * (t2 - t1)):.1f}ms) Inference, ({(1E3 * (t3 - t2)):.1f}ms) NMS')
            print(s)

            # Create an API for the webApp
            # if webApp:
            #     try:
            #         Serverurl = "http://localhost:5000/update_data"
            #         data = {'num_people': s}
            #         response = requests.post(Serverurl, json=data)
            #     except:
            #         print("Failed to send to WebApp")

            # Stream results
            if view_img:
                # Display the image in a window
                cv2.putText(im0, 'Result : ' + s[3:], (10, im0.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)
                tit = 'People Detector / Counter'
                cv2.imshow(tit , im0)

                # Wait for a key press
                if cv2.waitKey(1) == ord('q'):  # q to quit
                    cv2.destroyAllWindows()
                    raise StopIteration

            # Save results (image with detections)
            if save_img:
                if dataset.mode == 'image':
                    cv2.imwrite(save_path, im0)
                    print(f" The image with the result is saved in: {save_path}")
                else:  # 'video' or 'stream'
                    if vid_path != save_path:  # new video
                        vid_path = save_path
                        if isinstance(vid_writer, cv2.VideoWriter):
                            vid_writer.release()  # release previous video writer
                        if vid_cap:  # video
                            fps = vid_cap.get(cv2.CAP_PROP_FPS)
                            w = int(vid_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                            h = int(vid_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        else:  # stream
                            fps, w, h = 15, im0.shape[1], im0.shape[0]
                            save_path += '.mp4'
                        vid_writer = cv2.VideoWriter(save_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))
                    vid_writer.write(im0)
                # print("Video Saved")

        # This code is just to print data
        # if save_txt or save_img:
        #     s = f"\n{len(list(save_dir.glob('labels/*.txt')))} labels saved to {save_dir / 'labels'}" if save_txt else ''
        #     print(f"Results saved to {save_dir}{s}")

        print(f'Done. ({time.time() - t0:.3f}s)')
        # time.sleep(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--weights', nargs='+', type=str, default='yolov7.pt', help='model.pt path(s)')
    parser.add_argument('--download', action='store_true', help='download model weights automatically')
    parser.add_argument('--no-download', dest='download', action='store_false')
    parser.add_argument('--source', type=str, default='inference/images', help='source')  # file/folder, 0 for webcam
    parser.add_argument('--img-size', type=int, default=640, help='inference size (pixels)')
    parser.add_argument('--conf-thres', type=float, default=0.25, help='object confidence threshold')
    parser.add_argument('--iou-thres', type=float, default=0.45, help='IOU threshold for NMS')
    parser.add_argument('--device', default='', help='cuda device, i.e. 0 or 0,1,2,3 or cpu')
    parser.add_argument('--save-txt', action='store_true', help='save results to *.txt')
    parser.add_argument('--save-conf', action='store_true', help='save confidences in --save-txt labels')
    parser.add_argument('--nosave', action='store_true', help='do not save images/videos')
    parser.add_argument('--classes', nargs='+', type=int, default=0, help='filter by class: --class 0, or --class 0 2 3')
    parser.add_argument('--agnostic-nms', action='store_true', help='class-agnostic NMS')
    parser.add_argument('--augment', action='store_true', help='augmented inference')
    parser.add_argument('--update', action='store_true', help='update all models')
    parser.add_argument('--project', default='Output', help='save results to project/name')
    parser.add_argument('--name', default='object_tracking', help='save results to project/name')
    parser.add_argument('--exist-ok', action='store_true', help='existing project/name ok, do not increment')
    parser.add_argument('--no-trace', action='store_true', help='don`t trace model')
    parser.add_argument('--view-img', action='store_true', help='display results')
    parser.add_argument('--webApp',default=0,  help='Create an API for the WebApp')
    parser.set_defaults(download=True)
    opt = parser.parse_args()
    print(opt)

    # check_requirements(exclude=('pycocotools', 'thop'))
    # if opt.download and not os.path.exists(opt.weights[0]):
    #     print('Model weights not found. Attempting to download now...')
    #     download('./')

    with torch.no_grad():
        if opt.update:  # update all models (to fix SourceChangeWarning)
            for opt.weights in ['yolov7.pt']:
                detect()
                strip_optimizer(opt.weights)
        else:
            detect()






















# Working code


# import argparse
# import time
# from pathlib import Path
# import requests
# import cv2
# import torch
# import torch.backends.cudnn as cudnn
# from numpy import random
#
# # Custom Modules
# import config
# import WebApp
# from models.experimental import attempt_load
# from utils.datasets import LoadStreams, LoadImages
# from utils.general import check_img_size, check_imshow, non_max_suppression, apply_classifier, \
#     scale_coords, xyxy2xywh, strip_optimizer, set_logging, \
#     increment_path
# from utils.plots import plot_one_box
# from utils.torch_utils import select_device, load_classifier, time_synchronized, TracedModel
#
#
# def detect(save_img=False):
#     source, weights, view_img, save_txt, imgsz, trace = opt.source, opt.weights, opt.view_img, opt.save_txt, opt.img_size, not opt.no_trace
#     source = config.IP_Url
#     weights = 'yolov7.pt'
#     save_img = not opt.nosave and not source.endswith('.txt')  # save inference images
#     webcam = source.isnumeric() or source.endswith('.txt') or source.lower().startswith(
#         ('rtsp://', 'rtmp://', 'http://', 'https://'))
#
#     # Directories
#     save_dir = Path(increment_path(Path(opt.project) / opt.name, exist_ok=opt.exist_ok))  # increment run
#     (save_dir / 'labels' if save_txt else save_dir).mkdir(parents=True, exist_ok=True)  # make dir
#
#     # Initialize
#     set_logging()
#     device = select_device(opt.device)
#     half = device.type != 'cpu'  # half precision only supported on CUDA
#
#     # Load model
#     model = attempt_load(weights, map_location=device)  # load FP32 model
#     stride = int(model.stride.max())  # model stride
#     imgsz = check_img_size(imgsz, s=stride)  # check img_size
#
#     if trace:
#         model = TracedModel(model, device, opt.img_size)
#
#     if half:
#         model.half()  # to FP16
#
#     # Second-stage classifier
#     classify = False
#     if classify:
#         modelc = load_classifier(name='resnet101', n=2)  # initialize
#         modelc.load_state_dict(torch.load('weights/resnet101.pt', map_location=device)['model']).to(device).eval()
#
#     # Set Dataloader
#     vid_path, vid_writer = None, None
#     if webcam:
#         view_img = check_imshow()
#         cudnn.benchmark = True  # set True to speed up constant image size inference
#         dataset = LoadStreams(source, img_size=imgsz, stride=stride)
#     else:
#         dataset = LoadImages(source, img_size=imgsz, stride=stride)
#
#     # Get names and colors
#     names = model.module.names if hasattr(model, 'module') else model.names
#     colors = [[random.randint(0, 255) for _ in range(3)] for _ in names]
#
#     # Run inference
#     if device.type != 'cpu':
#         model(torch.zeros(1, 3, imgsz, imgsz).to(device).type_as(next(model.parameters())))  # run once
#     old_img_w = old_img_h = imgsz
#     old_img_b = 1
#
#     t0 = time.time()
#     # print(t0)
#
#     for path, img, im0s, vid_cap in dataset:
#         img = torch.from_numpy(img).to(device)
#         img = img.half() if half else img.float()  # uint8 to fp16/32
#         img /= 255.0  # 0 - 255 to 0.0 - 1.0
#         if img.ndimension() == 3:
#             img = img.unsqueeze(0)
#
#         # Warmup
#         if device.type != 'cpu' and (
#                 old_img_b != img.shape[0] or old_img_h != img.shape[2] or old_img_w != img.shape[3]):
#             old_img_b = img.shape[0]
#             old_img_h = img.shape[2]
#             old_img_w = img.shape[3]
#             for i in range(3):
#                 model(img, augment=opt.augment)[0]
#
#         # Inference
#         t1 = time_synchronized()
#         pred = model(img, augment=opt.augment)[0]
#         t2 = time_synchronized()
#
#         # Apply NMS
#         pred = non_max_suppression(pred, opt.conf_thres, opt.iou_thres, classes=opt.classes, agnostic=opt.agnostic_nms)
#         t3 = time_synchronized()
#
#         # Apply Classifier
#         if classify:
#             pred = apply_classifier(pred, modelc, img, im0s)
#
#         # Process detections
#         for i, det in enumerate(pred):  # detections per image
#             if webcam:  # batch_size >= 1
#                 p, s, im0, frame = path[i], '%g: ' % i, im0s[i].copy(), dataset.count
#             else:
#                 p, s, im0, frame = path, '', im0s, getattr(dataset, 'frame', 0)
#
#             p = Path(p)  # to Path
#             save_path = str(save_dir / p.name)  # img.jpg
#             txt_path = str(save_dir / 'labels' / p.stem) + ('' if dataset.mode == 'image' else f'_{frame}')  # img.txt
#             gn = torch.tensor(im0.shape)[[1, 0, 1, 0]]  # normalization gain whwh
#             if len(det):
#                 # Rescale boxes from img_size to im0 size
#                 det[:, :4] = scale_coords(img.shape[2:], det[:, :4], im0.shape).round()
#
#                 # Print results
#                 for c in det[:, -1].unique():
#                     n = (det[:, -1] == c).sum()  # detections per class
#                     # s += f"{n} {names[int(c)]}{'s' * (n > 1)}, "  # This line creates for all types of objects but i need for only person, hence use below line.
#                     s += f"{n} {names[int(c)]}{'s' * (n > 1)},"
#
#                 # Write results in txt file and draw box in the image
#                 # for *xyxy, conf, cls in reversed(det):
#                 #     if save_txt:  # Write to file
#                 #         xywh = (xyxy2xywh(torch.tensor(xyxy).view(1, 4)) / gn).view(-1).tolist()  # normalized xywh
#                 #         line = (cls, *xywh, conf) if opt.save_conf else (cls, *xywh)  # label format
#                 #         with open(txt_path + '.txt', 'a') as f:
#                 #             f.write(('%g ' * len(line)).rstrip() % line + '\n')
#                 #
#                 #     if save_img or view_img:  # Add bbox to image
#                 #         label = f'{names[int(cls)]} {conf:.2f}'
#                 #         plot_one_box(xyxy, im0, label=label, color=colors[int(cls)], line_thickness=1)
#
#             # Print time (inference + NMS)
#             # print(f'{s}Done. ({(1E3 * (t2 - t1)):.1f}ms) Inference, ({(1E3 * (t3 - t2)):.1f}ms) NMS')
#             print(s)
#
#             # Stream results
#             # if view_img:
#             #     cv2.imshow(str(p), im0)
#             #     if cv2.waitKey(1) == ord('q'):  # q to quit
#             #         cv2.destroyAllWindows()
#             #         raise StopIteration
#
#             # Stream results
#             if view_img:
#                 # Convert the image to a byte string
#                 # img_bytes = cv2.imencode('.jpg', im0)[1].tostring()
#
#                 try:
#                     # Send the image to the Flask server
#                     Serverurl = "http://localhost:5000/update_data"
#                     data = {'num_people': s}
#                     response = requests.post(Serverurl, json=data)
#                     # print(response)
#                     # WebApp.updateImage(s)
#                     # Check the response status code
#                 except:
#                     print("Failed to send to WebApp")
#
#                 # Display the image in a window
#                 # cv2.imshow(str(p), im0)
#                 #
#                 # # Wait for a key press
#                 # if cv2.waitKey(1) == ord('q'):  # q to quit
#                 #     cv2.destroyAllWindows()
#                 #     raise StopIteration
#
#             # Save results (image with detections)
#             if save_img:
#                 if dataset.mode == 'image':
#                     cv2.imwrite(save_path, im0)
#                     print(f" The image with the result is saved in: {save_path}")
#                 else:  # 'video' or 'stream'
#                     if vid_path != save_path:  # new video
#                         vid_path = save_path
#                         if isinstance(vid_writer, cv2.VideoWriter):
#                             vid_writer.release()  # release previous video writer
#                         if vid_cap:  # video
#                             fps = vid_cap.get(cv2.CAP_PROP_FPS)
#                             w = int(vid_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
#                             h = int(vid_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
#                         else:  # stream
#                             fps, w, h = 30, im0.shape[1], im0.shape[0]
#                             save_path += '.mp4'
#                         vid_writer = cv2.VideoWriter(save_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))
#                     vid_writer.write(im0)
#
#     if save_txt or save_img:
#         s = f"\n{len(list(save_dir.glob('labels/*.txt')))} labels saved to {save_dir / 'labels'}" if save_txt else ''
#         print(f"Results saved to {save_dir}{s}")
#
#     print(f'Done. ({time.time() - t0:.3f}s)')
#
#
# if __name__ == '__main__':
#     parser = argparse.ArgumentParser()
#     parser.add_argument('--weights', nargs='+', type=str, default='yolov7.pt', help='model.pt path(s)')
#     parser.add_argument('--download', action='store_true', help='download model weights automatically')
#     parser.add_argument('--no-download', dest='download', action='store_false')
#     parser.add_argument('--source', type=str, default='inference/images', help='source')  # file/folder, 0 for webcam
#     parser.add_argument('--img-size', type=int, default=640, help='inference size (pixels)')
#     parser.add_argument('--conf-thres', type=float, default=0.25, help='object confidence threshold')
#     parser.add_argument('--iou-thres', type=float, default=0.45, help='IOU threshold for NMS')
#     parser.add_argument('--device', default='', help='cuda device, i.e. 0 or 0,1,2,3 or cpu')
#     parser.add_argument('--view-img', action='store_true', help='display results')
#     parser.add_argument('--save-txt', action='store_true', help='save results to *.txt')
#     parser.add_argument('--save-conf', action='store_true', help='save confidences in --save-txt labels')
#     parser.add_argument('--nosave', action='store_true', help='do not save images/videos')
#     parser.add_argument('--classes', nargs='+', type=int, default=0, help='filter by class: --class 0, or --class 0 2 3')
#     parser.add_argument('--agnostic-nms', action='store_true', help='class-agnostic NMS')
#     parser.add_argument('--augment', action='store_true', help='augmented inference')
#     parser.add_argument('--update', action='store_true', help='update all models')
#     parser.add_argument('--project', default='runs/detect', help='save results to project/name')
#     parser.add_argument('--name', default='object_tracking', help='save results to project/name')
#     parser.add_argument('--exist-ok', action='store_true', help='existing project/name ok, do not increment')
#     parser.add_argument('--no-trace', action='store_true', help='don`t trace model')
#     parser.set_defaults(download=True)
#     opt = parser.parse_args()
#     print(opt)
#
#     # check_requirements(exclude=('pycocotools', 'thop'))
#     # if opt.download and not os.path.exists(opt.weights[0]):
#     #     print('Model weights not found. Attempting to download now...')
#     #     download('./')
#
#     with torch.no_grad():
#         if opt.update:  # update all models (to fix SourceChangeWarning)
#             for opt.weights in ['yolov7.pt']:
#                 detect()
#                 strip_optimizer(opt.weights)
#         else:
#             detect()