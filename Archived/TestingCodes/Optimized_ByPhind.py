import time
from pathlib import Path
import requests
import cv2
import torch
import torch.backends.cudnn as cudnn
from numpy import random
from threading import Thread

import config
import WebApp
from models.experimental import attempt_load
from utils.datasets import LoadStreams, LoadImages
from utils.general import check_img_size, check_imshow, non_max_suppression, apply_classifier, \
    scale_coords, xyxy2xywh, strip_optimizer, set_logging, \
    increment_path
from utils.plots import plot_one_box
from utils.torch_utils import select_device, load_classifier, time_synchronized, TracedModel

def detect(save_img=False):
    source = config.IP_Url
    weights = 'yolov7.pt'
    view_img = True
    save_txt = True
    imgsz = 640
    trace = True
    objectType = 0
    project = 'runs/detect'
    name = 'object_tracking'
    exist_ok = False
    device = ''
    save_conf = False
    nosave = True

    save_img = not save_img and not source.endswith('.txt')  # save inference images
    webcam = source.isnumeric() or source.endswith('.txt') or source.lower().startswith(
        ('rtsp://', 'rtmp://', 'http://', 'https://'))
    save_dir = Path(increment_path(Path(project) / name, exist_ok=exist_ok))  # increment run
    (save_dir / 'labels' if save_txt else save_dir).mkdir(parents=True, exist_ok=True)  # make dir
    set_logging()
    device = select_device(device)
    half = device.type != 'cpu'  # half precision only supported on CUDA
    model = attempt_load(weights, map_location=device)  # load FP32 model
    stride = int(model.stride.max())  # model stride
    imgsz = check_img_size(imgsz, s=stride)  # check img_size

    if trace:
        model = TracedModel(model, device, imgsz)

    if half:
        model.half()  # to FP16
    classify = False
    if classify:
        modelc = load_classifier(name='resnet101', n=2)  # initialize
        modelc.load_state_dict(torch.load('weights/resnet101.pt', map_location=device)['model']).to(device).eval()
    vid_path, vid_writer = None, None
    if webcam:
        view_img = check_imshow()
        cudnn.benchmark = True  # set True to speed up constant image size inference
        dataset = LoadStreams(source, img_size=imgsz, stride=stride)
    else:
        dataset = LoadImages(source, img_size=imgsz, stride=stride)
    names = model.module.names if hasattr(model, 'module') else model.names
    colors = [[random.randint(0, 255) for _ in range(3)] for _ in names]
    if device.type != 'cpu':
        model(torch.zeros(1, 3, imgsz, imgsz).to(device).type_as(next(model.parameters())))  # run once
    old_img_w = old_img_h = imgsz
    old_img_b = 1

    t0 = time.time()

    def inference(path, img, im0s, vid_cap):
        nonlocal model, device, half, names, colors, save_img, save_txt, save_dir, objectType

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
                model(img, augment=False)[0]

        t1 = time_synchronized()
        pred = model(img, augment=False)[0]
        t2 = time_synchronized()

        modelDelay = t2 - t1
        print(f'The Model Delay : {modelDelay}')

        conf_thres = 0.25
        iou_thres = 0.45
        # Apply NMS
        pred = non_max_suppression(pred, conf_thres, iou_thres, classes=objectType, agnostic=False)
        s = ''

        for i, det in enumerate(pred):  # detections per image
            if webcam:  # batch_size >= 1
                p, s, im0 = Path(path[i]), '', im0s[i].copy()
                save_path = str(save_dir / p.name)
            else:
                p, s, im0 = Path(path), '', im0s

            gn = torch.tensor(im0.shape)[[1, 0, 1, 0]]  # normalization gain whwh
            if len(det):
                # Rescale boxes from img_size to im0 size
                det[:, :4] = scale_coords(img.shape[2:], det[:, :4], im0.shape).round()

                # Print results
                for c in det[:, -1].unique():
                    n = (det[:, -1] == c).sum()  # detections per class
                    s += f"{n} {names[int(c)]}{'s' * (n > 1)},"  # add to string

                # Write results on the window
                for *xyxy, conf, cls in reversed(det):
                    if save_txt:  # Write to file
                        xywh = (xyxy2xywh(torch.tensor(xyxy).view(1, 4)) / gn).view(-1).tolist()  # normalized xywh

                    # Add bbox to image
                    if save_img or view_img:
                        label = f'{names[int(cls)]} {conf:.2f}'
                        plot_one_box(xyxy, im0, label=label, color=colors[int(cls)], line_thickness=1)
            print(s)


            if view_img:
               cv2.imshow(str(p), im0)

               # Wait for a key press
               if cv2.waitKey(1) == ord('q'):  # q to quit
                   cv2.destroyAllWindows()
                   raise StopIteration

    threads = []
    for path, img, im0s, vid_cap in dataset:
        t = Thread(target=inference, args=(path, img, im0s, vid_cap))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    print(f'Done. ({time.time() - t0:.3f}s)')


if __name__ == '__main__':
    detect(save_img=True)
