import cv2

camera = cv2.VideoCapture(0)

try:
    if not camera.isOpened():
        raise RuntimeError("カメラを開けません")

    ret, frame = camera.read()

    if not ret:
        raise RuntimeError("撮影に失敗しました")

    cv2.imshow("USB Camera", frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

finally:
    camera.release()
