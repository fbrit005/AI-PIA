# Fernando Brito & Bryan Dalmasso
import cv2
import torch
import sqlite3
import numpy as np
from PIL import Image
from facenet_pytorch import InceptionResnetV1, MTCNN
import torchvision.transforms as transforms
from ultralytics import YOLO
from ultralytics.utils.ops import non_max_suppression
import os
import threading
import onnxruntime as ort  # with TensorRT support
import sys
import multiprocessing
import builtins
from builtins import any as safe_any
#any = builtins.any
import signal
import re #Used to split strings from multiple tokens

#Used to cache the results from onnx/tensor for quicker load times
os.environ["ORT_TENSORRT_ENGINE_CACHE_ENABLE"] = "1"
os.environ["ORT_TENSORRT_CACHE_PATH"] = "./trt_cache"


#Database functions

def queryCheckIfCameraNameExists(name):
    conn = sqlite3.connect("AIPIA.db")
    try:
        rows = conn.execute("SELECT Username FROM users WHERE Username = ?",(name,)).fetchall()
        #conn.commit()
        conn.close()
        return rows[0][0]
    except Exception as e:
        print(f"queryCameraName Error: {e}")
        return False

def updatePassword(IDNumber, pword):
    conn = sqlite3.connect("AIPIA.db")
    try:
        conn.execute("UPDATE users SET Password = ? WHERE ID = ?",(pword, IDNumber,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"updatePassword Error: {e}")
        return False

def queryCheckIfSameCamera(ID, name):
    conn = sqlite3.connect("AIPIA.db")
    try:
        rows = conn.execute("SELECT Username FROM users WHERE Username = ? AND ID = ?",(name, ID,)).fetchall()
        #conn.commit()
        conn.close()
        return rows[0][0]
    except Exception as e:
        print(f"queryCheckIfSameCamera Error: {e}")
        return False


def removeCamera(IDNumber):
    conn = sqlite3.connect("AIPIA.db")
    try:
        conn.execute("DELETE FROM users_settings WHERE ID = ?", (IDNumber,))
        conn.execute("DELETE FROM users WHERE ID = ?", (IDNumber,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"removeCamera Error: {e}")
        return False



def queryRTSPUrl(IDNumber):
	connection = sqlite3.connect("AIPIA.db")
	queryRows = connection.execute("SELECT RTSPStream FROM users_settings WHERE ID = ?", (IDNumber,)).fetchall()
	
	connection.close()
	
	
	return queryRows[0][0]


def queryCameraName(ID):
    conn = sqlite3.connect("AIPIA.db")
    try:
        rows = conn.execute("SELECT Username FROM users WHERE ID = ?",(ID,)).fetchall()
        #conn.commit()
        conn.close()
        return rows[0][0]
    except Exception as e:
        print(f"queryCameraName Error: {e}")
        return False

def updateCameraName(ID, name):
    conn = sqlite3.connect("AIPIA.db")
    try:
        conn.execute("UPDATE users SET Username=? WHERE ID = ?",(name, ID))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"updateCameraName Error: {e}")
        return False

def updateRTSPURL(ID, url):
    conn = sqlite3.connect("AIPIA.db")
    try:
        conn.execute("UPDATE users_settings SET RTSPStream=? WHERE ID = ?",(url, ID))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"updateRTSPURL Error: {e}")
        return False

def updatePassword(ID, pword):
    conn = sqlite3.connect("AIPIA.db")
    try:
        conn.execute("UPDATE users SET Password=? WHERE ID = ?",(pword, ID))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"updateCameraName Error: {e}")
        return False




def updateName(ID, Name):
    conn = sqlite3.connect("AIPIA.db")
    try:
        conn.execute("UPDATE main SET Name=? WHERE ID = ?",(Name, ID))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"updateName Error: {e}")
        return False

def updateTags(ID, tags):
    conn = sqlite3.connect("AIPIA.db")
    try:
        conn.execute("DELETE FROM tags WHERE ID = ?",(ID,))
        conn.commit()

        for singleTag in tags:
            rows = conn.execute("INSERT INTO tags (ID, Tag) VALUES (?,?)", (ID, singleTag))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"updateTags Error: {e}")
        return False



def queryIDsAndNames():
    conn = sqlite3.connect("AIPIA.db")
    try:
        rows = conn.execute("SELECT ID, Name FROM main order by Name asc").fetchall()
        conn.close()
        return rows
    except Exception as e:
        print(f"queryIDAndNames Error: {e}")
        return False


def queryFaceImages():
    conn = sqlite3.connect("AIPIA.db")
    #Get the images of faces in Name-alphabetical order
    rowsFaces = conn.execute("SELECT faces.ID, faces.URL FROM faces INNER JOIN main ON faces.ID = main.ID order by main.Name asc").fetchall()

    conn.close()
    return rowsFaces

def queryTags(IDNumber):
    conn = sqlite3.connect("AIPIA.db")
    rowsTags = conn.execute("SELECT Tag FROM tags where ID = ? order by ID asc", (IDNumber,)).fetchall()

    conn.close()
    return rowsTags

def queryName(IDNumber):
    conn = sqlite3.connect("AIPIA.db")
    rowsName = conn.execute("SELECT Name FROM main where ID = ? order by ID asc", (IDNumber,)).fetchall()

    conn.close()
    return rowsName

def queryIDByNameAndTags(name, tags):
    conn = sqlite3.connect("AIPIA.db")
    try:
        rows = conn.execute("SELECT ID FROM main WHERE Name = ?", (name,)).fetchall()
        rowsIDResults = conn.execute("SELECT faces.ID, faces.URL FROM faces INNER JOIN main ON faces.ID = main.ID order by main.Name asc")

        conn.close()
        return rowsIDResults
    except Exception as e:
        print(f"queryIDByNameAndTags Error: {e}")
        return False

def insertMainNew(ID, name):
    conn = sqlite3.connect("AIPIA.db")
    try:
        #print(f"ID: {ID}  name: {name}")
        conn.execute("INSERT INTO main (ID, Name) VALUES (?, ?)", (ID, name))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"insertMainNew Error: {e}")
        return False

def removeMain(ID):
    conn = sqlite3.connect("AIPIA.db")
    try:
        conn.execute("DELETE FROM main WHERE ID = ?", (ID,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"insertFacePath Error: {e}")
        return False


def queryFacePath(ID):
    conn = sqlite3.connect("AIPIA.db")
    try:
        rows = conn.execute("SELECT URL FROM faces WHERE ID = ?", (ID,)).fetchall()

        conn.close()
        return rows
    except Exception as e:
        print(f"queryFacePath Error: {e}")
        return False




def insertFacePath(ID, path):
    conn = sqlite3.connect("AIPIA.db")
    try:
        conn.execute("INSERT INTO faces (ID, URL) VALUES (?, ?)", (ID, path))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"insertFacePath Error: {e}")
        return False

def removeFacePath(ID, path):
    conn = sqlite3.connect("AIPIA.db")
    try:
        conn.execute("DELETE FROM faces WHERE ID = ? AND URL = ?", (ID, path))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"removeFacePath Error: {e}")
        return False


def insertTag(ID, tag):
    conn = sqlite3.connect("AIPIA.db")
    try:
        conn.execute("INSERT INTO tags (ID, Tag) VALUES (?, ?)", (ID, tag))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"insertTag Error: {e}")
        return False

def removeAllTag(ID):
    conn = sqlite3.connect("AIPIA.db")
    try:
        conn.execute("DELETE FROM tags WHERE ID = ?", (ID,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"RemoveAllTag Error: {e}")
        return False



def removeTag(ID, tag):
    conn = sqlite3.connect("AIPIA.db")
    try:
        conn.execute("DELETE FROM tags WHERE ID = ? AND tag = ?", (ID, tag))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"RemoveTag Error: {e}")
        return False

def queryNextID():
    conn = sqlite3.connect("AIPIA.db")

    #Now we need to check which next ID number is available (in order) in the db
    rows = conn.execute("SELECT ID FROM main order by ID asc").fetchall();

    #Variable to store the ID to use
    currentIDToUse = 0;
    #print(rows)
    #Iterate through all of the ids until we find a gap. If there is no gap, use the last number
    for i, ids in enumerate(rows):
        i = i + 1
        #print(f"i: {i} id: {ids[0]}")
        #print(f"i != id: {i != ids[0]}")
        #print(f"current {currentIDToUse}")
        if i != ids[0]:
            currentIDToUse = i;
            break
    #print(f"Cur ID: {currentIDToUse}")
    if currentIDToUse == 0:
        currentIDToUse = len(rows)+1

    conn.close()
    #print("Next ID: "+ str(currentIDToUse))
    return currentIDToUse




def queryCheckIfPersonExists(name, tags):
    conn = sqlite3.connect("AIPIA.db")
    rowsIDResults = conn.execute("SELECT ID FROM main WHERE Name = ?", (name.capitalize(),)).fetchall()

    #print(f"All IDS {rowsIDResults}")

    try:
        rowsIDResults[0][0]
    except:
        conn.close()
        return False

    if str(rowsIDResults[0][0]).casefold() == str(name).casefold():
        conn.close()
        return True
    else:

        counter = 0

        for idIndex, ID in enumerate(rowsIDResults):
            rowsTagResults = conn.execute("SELECT Tag FROM tags WHERE ID = ?", (rowsIDResults[idIndex][0],)).fetchall()

        
        #Add a , to the end of the tag list
        #tags = tags + ","
        #Tokenize the string into a list of tags
            listOfRowsToCompareOriginal = re.split(', |,',tags)
        #print(f"Split Before Cleaning: {listOfRowsToCompareOriginal}")
        #Clean the list of blank spaces
        #listOfRowsToCompare = [tag for tag in listOfRowsToCompareOriginal if item != ""]
            listOfRowsToCompare = list(filter(None, listOfRowsToCompareOriginal))
        #print(f"List of Rows::{rowsTagResults[1][0]}")
        #print(f"List of Rows:{listOfRowsToCompare[1]}")
        #print(f"Split After Cleaning: {listOfRowsToCompare}")

        #First check is to see if the number of tags entered matches the one in the db
        #if len(listOfRowsToCompare) != len(rowsTagResults):
            #return True
        #If there were no tags entered, return false
        #print(f"Length of Rows to Compare: {len(listOfRowsToCompare)}")
        #print(f"Length of Rows in DB: {len(rowsTagResults)}")
            if len(listOfRowsToCompare) == 0:
                return False

        #Check to see if the tags match the ones in the db
            #counter = 0
            #print(f"DB Tags: {rowsTagResults}")

        #for idIndex, ID in enumerate(rowsIDResults):
            for i, storedTags in enumerate(rowsTagResults):
                for j, newTags in enumerate(listOfRowsToCompare):
                    #print(f"ID : {rowsIDResults[idIndex][0]}   I: {i}  J: {j}")
                    #print(f"NewTag: {listOfRowsToCompare[j]}   DBTag: {rowsTagResults[i][0]}")
                    try:
                        if str(listOfRowsToCompare[j]).casefold() == str(rowsTagResults[i][0]).casefold():
                            counter = counter + 1
                            #print(f"Counter: {counter}")
                        #if counter == len(rowsTagResults):
                            #return True
                            #counter = 0
                    except:
                        pass
                        #return False
        if counter == len(rowsTagResults):
            return True
        return False
        #conn.close()
        #return rowsTagResults
    

#Main Model Functions
def queryFaceData(known_embeddings, known_names, known_tags, known_paths, known_IDs, ID, resnet, device, img, emb):
    # Here we load registered individuals
    conn = sqlite3.connect("AIPIA.db")
    rowsMain = conn.execute("SELECT ID, Name FROM main order by ID asc").fetchall()

    #print(f"Rows: {rowsMain}")

    #Transform for stuff
    transform = transforms.Compose([
        transforms.Resize((160, 160)),
        transforms.ToTensor()
    ])    

    for indexMain, (ids, names) in enumerate(rowsMain):
        #known_faces.append(names) #Add the name to the list
        known_IDs.append(ids)

        #print(f"known Ids: {type(known_IDs[indexMain])}")
        #query for tags
        #print(f"Known IDS {ids}")
        tempRowTags = conn.execute("SELECT Tag from tags WHERE ID = ? order by ID asc", str(known_IDs[indexMain]),).fetchall() #Get every tag for said person
        
        #Now to append all of the tags into 1 string to append
        tempTagString = ""
        for index, tag in enumerate(tempRowTags):
            tempTagString = tempTagString + str(tag[0]) + " | "

        #With the tags and name, we need to apply it to each image of said person
        tempRowFaces = conn.execute("SELECT URL FROM faces WHERE ID = ?", str(known_IDs[indexMain]),).fetchall()
        #Now to create append face url, tags, and names per picture
        for index, urls in enumerate(tempRowFaces):
            try:
                #print(f"URLS: {urls}")
                img = Image.open(urls[0]).convert('RGB')
                emb = resnet(transform(img).unsqueeze(0).to(device)).detach()
                known_embeddings.append(emb)
                known_names.append(names)
                known_tags.append(tempTagString)
            except Exception as e:
                print(f"❗ Error loading {urls[0]}: {e}")
                sys.exit(1)





    #Get ID number to get RTSPStream from (Given from login program as argv)
    loginID = 0
    #Make sure there was an argument passed
    if len(sys.argv) > 1:
        loginID = sys.argv[1]
    else:
        print("Error! Argument needs to be ID from account logging in!")
        sys.exit("Exiting")

    #Now that we have the user ID to get the stream from, we can get the rtsp stream
    rtsp_streams = conn.execute("SELECT RTSPStream from users_settings WHERE ID = ?", loginID).fetchall()
    
    # Iterate through the list containing RTSP streams and pass into openCV
    for stream_url in rtsp_streams:
        RTSPurl = stream_url[0]
        RTSPurl = str(RTSPurl)
    return RTSPurl

COCO_NAMES = [
    'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus',
    'train', 'truck', 'boat', 'traffic light', 'fire hydrant', 'stop sign',
    'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep',
    'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella',
    'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
    'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
    'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana',
    'apple', 'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza',
    'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed', 'dining table',
    'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone',
    'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock',
    'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush'
]



def mainModel(externalQueue, rtspQueue, alertOutputQueue):
    #print("Starting Main Processes")
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;udp"
    # Loads processing into GPU
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # Initializing models
    #print("Initializing Models")

    #object_model = YOLO("yolov8n.pt").to(device)
    #yolo_session = ort.InferenceSession("yolov8m.onnx", providers=["TensorrtExecutionProvider", "CUDAExecutionProvider", "CPUExecutionProvider"])

    yolo_session = ort.InferenceSession(
        "yolov8m.onnx",
        providers=["TensorrtExecutionProvider", "CUDAExecutionProvider", "CPUExecutionProvider"]
    )


    #print("Yolo Initialized")
    #yolo_session = ort.InferenceSession("yolov8n.onnx", providers=["TensorrtExecutionProvider", "CUDAExecutionProvider", "CPUExecutionProvider"])
    input_name = yolo_session.get_inputs()[0].name
    mtcnn = MTCNN(keep_all=True, device=device)
    #print("MTCNN Initialized")
    resnet = InceptionResnetV1(pretrained='vggface2').eval().to(device)
    #print("Models initialized!")


    #Global lists to store data
    known_embeddings, known_names, known_tags, known_paths, known_IDs = [], [], [], [], []

    loginID = 0
    img = None
    emb = None

    #Transform for stuff (again)
    transform = transforms.Compose([
        transforms.Resize((160, 160)),
        transforms.ToTensor()
    ])    




    #Get the data from the DB
    RTSPurl = queryFaceData(known_embeddings, known_names, known_tags, known_paths, known_IDs, loginID, resnet, device, img, emb)

    #Tensor stuff
    if not known_embeddings:
        img = Image.open("./faces/none/none.jpg").convert('RGB')
        emb = resnet(transform(img).unsqueeze(0).to(device)).detach()
        known_embeddings.append(emb)
        known_names.append("Unknown")
        known_tags.append("")

        #known_embeddings.append(torch.empty((0, 512), dtype=torch.float32))
        #pass
        #raise SystemExit("No known face embeddings!")

    known_embeddings = torch.cat(known_embeddings).to(device)

    cap = None
    cap = cv2.VideoCapture(RTSPurl)
    #print(RTSPurl)

    if not cap.isOpened():
        pass
        #print(f"❌ Could not open stream: {RTSPurl}")
        #sys.exit(1)


    while True:
        #ret, frame = cap.read()
        ret, frame = rtspQueue.get()
        #p = multiprocessing.Process(target = readStream, name ='readRTSPProcess', args=(q,url))
        #p.start()
        #ret, frame = q.get()
        #p.join()
        if not ret: break
        




        h_orig, w_orig = frame.shape[:2]
        img_resized = cv2.resize(frame, (640, 640))
        scale_x = w_orig / 640
        scale_y = h_orig / 640







        # Preprocessing
        #rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  
        #results = object_model.predict(rgb, imgsz=640, device=0, verbose=False)[0] # YOLOv8 model
        # Proper preprocessing
        
        # Copy frame for MTCNN
        rgb_for_mtcnn = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Preprocess for YOLOv8 ONNX
        img = cv2.resize(frame, (640, 640))
        yolo_input = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        yolo_input = yolo_input.astype(np.float32) / 255.0
        yolo_input = np.transpose(yolo_input, (2, 0, 1))  # HWC to CHW
        yolo_input = np.expand_dims(yolo_input, axis=0)   # Add batch dim
        yolo_input = np.ascontiguousarray(yolo_input)

        #img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        #img = img.astype(np.float32) / 255.0
        #img = np.transpose(img, (2, 0, 1))  # HWC → CHW
        #img = np.expand_dims(img, axis=0)   # Add batch dimension
        #img = np.ascontiguousarray(img)

        # Inference with ONNX Runtime
        outputs = yolo_session.run(None, {input_name: yolo_input})[0]
  
        # Added some post-processing
        preds = torch.tensor(outputs)
        results = non_max_suppression(preds, conf_thres=0.3, iou_thres=0.45)[0]
        alertOriginal = [COCO_NAMES[int(c)] for c in results[:, 5]] if results is not None and len(results) > 0 else " "
        alert = ",".join(alertOriginal)
        alert = alert + " | PERSON DETECTED: "
        #print(f"Main Model PID: {os.getpid()}")
        #if alertOutputQueue.empty():
            #alertOutputQueue.put(alert)
        

        #any = __builtins__.any
        #any = builtins.any
        #person_ids = results[:, 5].int().cpu().numpy() if results is not None and len(results) > 0 else []
        #person_detected = builtins.any(COCO_NAMES[i] == 'person' for i in person_ids)


        #person_ids = results[:,5].int().cpu().numpy if results is not None and len(results) > 0 else []
        #person_ids = results.boxes.cls.cpu().numpy().astype(int)
        person_ids = results[:,5].int().cpu().numpy() if results is not None and len(results) > 0 else []
        #person_detected = builtins.any(COCO_NAMES[i] == 'person' for i in person_ids)
        #person_detected = any(object_model.names[i] == 'person' for i in person_ids)
        person_detected = safe_any(COCO_NAMES[i] == 'person' for i in person_ids)

        if results is not None and len(results) > 0:
            for det in results:
                x1, y1, x2, y2, conf, cls = det.tolist()
                #x1, y1, x2, y2 = map(int, (x1, y1, x2, y2))
                x1 = int(x1 * scale_x)
                y1 = int(y1 * scale_y)
                x2 = int(x2 * scale_x)
                y2 = int(y2 * scale_y)
                label = COCO_NAMES[int(cls)] # This is to draw a frame around object
            #x1, y1, x2, y2 = map(int, xyxy)
            #lbl = object_model.names[int(cls)]
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255,140,0), 2)
                cv2.putText(frame, f"{label} {conf:.2f}", (x1, y1-5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,140,0), 2)


        if person_detected:
            boxes, _ = mtcnn.detect(rgb_for_mtcnn) # Face recognition model
            if boxes is not None:
                for box in boxes:
                    x1, y1, x2, y2 = map(int, box)
                    fc = frame[y1:y2, x1:x2]
                    try:
                        img = Image.fromarray(cv2.cvtColor(fc, cv2.COLOR_BGR2RGB)).resize((160,160))
                        emb = resnet(transform(img).unsqueeze(0).to(device)).detach()  # Here we finally perform face recognition
                        dists = (known_embeddings - emb).norm(dim=1)
                        md, idx = torch.min(dists, dim=0)
                        name, tag = (known_names[idx], known_tags[idx]) if md < 0.8 else ("Unknown", "")
                        label = f"{name} | {tag}"
                        alert = str(alert) + "•"+str(label)
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0,0,255), 2)
                        cv2.putText(frame, label, (x1, y2+15),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255), 2)
                        #encoded_frame = cv2.imencode('.jpg', frame)[1].tobytes()
                        #footage_socket.send(encoded_frame)
                    except Exception as e:
                        print("Face recognition error:", e)
        #print(str(externalQueue.empty()))
        if externalQueue.empty():
            #print("Placing Frame!")
            externalQueue.put(frame)
        if alertOutputQueue.empty():
            alertOutputQueue.put(alert)
        #Show the frame
        #cv2.imshow("YOLOv8 + MTCNN + FaceNet", frame) # Run outputs into the camera capture frame
        #print("Showing image")
        #p.terminate()
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    #while not q.empty():
        #q.get_nowait()

    #p.kill()
    #p.join()
    #p.close()
    #print("Closing")
    #p.join()
    #p.terminate()
    cap.release()
    cv2.destroyAllWindows()



#Reading video from opencv
def getStreamWorker(queue, url):
    capture = cv2.VideoCapture(url)
    #print(f"RTSP Fetcher PID: {os.getpid()}")
    #print(f"URL: {url}")
    #print(queue.get())
    while True:
        #print("Here!!")
        ret, frame = capture.read()
        if not ret:
            capture = cv2.VideoCapture(url)
        elif queue.empty():
            #print("RTSP Worker sending to queue")
            queue.put(capture.read())
            #queue.task_done()

#signal.signal(signal.SIGINT, exitSignalHandler)
#signal.signal(signal.SIGTERM, exitSignalHandler)


#mainModel()
