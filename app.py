from flask import Flask, render_template, Response, jsonify, request
import cv2
import numpy as np
import math
import time
import threading
import json

app = Flask(__name__)

# Shared state
state = {
    "expression": "",
    "result": "",
    "finger_count": 0,
    "last_gesture": "",
    "last_input_time": 0,
    "history": []
}
state_lock = threading.Lock()

cap = cv2.VideoCapture(0)

GESTURE_MAP = {
    1: "= SOLVE",
    2: "2",
    3: "3",
    4: "+",
    5: "−"
}

def process_frame(frame):
    frame = cv2.flip(frame, 1)
    roi = frame[100:400, 100:400]

    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    lower_skin = np.array([0, 20, 70], dtype=np.uint8)
    upper_skin = np.array([20, 255, 255], dtype=np.uint8)
    mask = cv2.inRange(hsv, lower_skin, upper_skin)
    mask = cv2.GaussianBlur(mask, (5, 5), 100)

    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    count_defects = 0
    finger_count = 0

    try:
        cnt = max(contours, key=lambda x: cv2.contourArea(x))
        hull = cv2.convexHull(cnt, returnPoints=False)
        defects = cv2.convexityDefects(cnt, hull)

        if defects is not None:
            for i in range(defects.shape[0]):
                s, e, f, d = defects[i, 0]
                start = tuple(cnt[s][0])
                end = tuple(cnt[e][0])
                far = tuple(cnt[f][0])

                a = math.dist(start, end)
                b = math.dist(start, far)
                c = math.dist(end, far)
                denom = 2 * b * c
                if denom == 0:
                    continue
                cos_angle = (b**2 + c**2 - a**2) / denom
                cos_angle = max(-1, min(1, cos_angle))
                angle = math.acos(cos_angle)

                if angle <= math.pi / 2:
                    count_defects += 1
                    cv2.circle(roi, far, 8, [0, 255, 255], -1)

            # Draw contour and hull on ROI
            cv2.drawContours(roi, [cnt], -1, (0, 255, 100), 2)
            hull_pts = cv2.convexHull(cnt)
            cv2.drawContours(roi, [hull_pts], -1, (0, 150, 255), 2)

        finger_count = count_defects + 1
    except:
        finger_count = 0

    # Draw styled rectangle
    cv2.rectangle(frame, (100, 100), (400, 400), (0, 255, 150), 2)
    cv2.rectangle(frame, (98, 98), (402, 402), (0, 100, 80), 1)

    # Overlay finger count
    label = GESTURE_MAP.get(finger_count, "...")
    cv2.putText(frame, f"Gesture: {label}", (10, 450),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 150), 2)
    cv2.putText(frame, f"Fingers: {finger_count}", (10, 480),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 200, 255), 2)

    # Update state
    current_time = time.time()
    with state_lock:
        state["finger_count"] = finger_count
        if finger_count > 0 and (current_time - state["last_input_time"]) > 1.5:
            if finger_count == 1:
                expr = state["expression"]
                if expr:
                    try:
                        # Replace − with -
                        safe_expr = expr.replace("−", "-")
                        res = str(eval(safe_expr))
                        state["history"].append({"expr": expr, "result": res})
                        if len(state["history"]) > 10:
                            state["history"].pop(0)
                        state["result"] = res
                        state["last_gesture"] = "SOLVED"
                    except:
                        state["result"] = "Error"
                        state["last_gesture"] = "ERROR"
                    state["expression"] = ""
                    state["last_input_time"] = current_time
            elif finger_count == 2:
                state["expression"] += "2"
                state["last_gesture"] = "2"
                state["last_input_time"] = current_time
            elif finger_count == 3:
                state["expression"] += "3"
                state["last_gesture"] = "3"
                state["last_input_time"] = current_time
            elif finger_count == 4:
                state["expression"] += "+"
                state["last_gesture"] = "+"
                state["last_input_time"] = current_time
            elif finger_count == 5:
                state["expression"] += "−"
                state["last_gesture"] = "−"
                state["last_input_time"] = current_time

    return frame

def gen_frames():
    while True:
        success, frame = cap.read()
        if not success:
            break
        frame = process_frame(frame)
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/state')
def get_state():
    with state_lock:
        return jsonify({
            "expression": state["expression"],
            "result": state["result"],
            "finger_count": state["finger_count"],
            "last_gesture": state["last_gesture"],
            "history": state["history"]
        })

@app.route('/clear', methods=['POST'])
def clear():
    with state_lock:
        state["expression"] = ""
        state["result"] = ""
        state["last_gesture"] = ""
    return jsonify({"status": "cleared"})

if __name__ == '__main__':
    app.run(debug=True, threaded=True)
