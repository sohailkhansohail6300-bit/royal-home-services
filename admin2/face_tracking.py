
import cv2
import sys

def main():

    # Load face detection model
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades +
        'haarcascade_frontalface_default.xml'
    )

    if face_cascade.empty():
        print("Error: Face detection model could not load.")
        return

    # Open laptop webcam
    camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not camera.isOpened():
        print("Error: Could not access laptop camera.")
        return

    # Camera settings
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    print("Face Tracking System Started")
    print("Press Q or ESC in the camera window to exit.")
    print("Press Ctrl+C in terminal to stop.")

    try:
        while True:

            ret, frame = camera.read()

            if not ret:
                print("Error: Cannot read camera frame.")
                break

            # Mirror webcam
            frame = cv2.flip(frame, 1)

            # Convert to grayscale
            gray = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2GRAY
            )

            # Detect faces
            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(60, 60)
            )

            # Draw face tracking boxes
            for (x, y, w, h) in faces:

                cv2.rectangle(
                    frame,
                    (x, y),
                    (x + w, y + h),
                    (0, 255, 0),
                    2
                )

                cv2.putText(
                    frame,
                    "FACE DETECTED",
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )

                # Face center
                center_x = x + w // 2
                center_y = y + h // 2

                cv2.circle(
                    frame,
                    (center_x, center_y),
                    4,
                    (0, 0, 255),
                    -1
                )

            # Display face count
            cv2.putText(
                frame,
                f"Faces Detected: {len(faces)}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 255),
                2
            )

            # Display status
            status = "FACE FOUND" if len(faces) > 0 else "SEARCHING..."

            cv2.putText(
                frame,
                status,
                (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0) if len(faces) > 0 else (0, 0, 255),
                2
            )

            # Show webcam
            cv2.imshow(
                "Python Face Tracking System",
                frame
            )

            # Exit using Q or ESC
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q') or key == 27:
                print("Face tracking stopped normally.")
                break

            # Exit if camera window is closed
            if cv2.getWindowProperty(
                "Python Face Tracking System",
                cv2.WND_PROP_VISIBLE
            ) < 1:
                break

    except KeyboardInterrupt:
        print("\nFace tracking interrupted by user.")

    except Exception as error:
        print(f"Error: {error}")

    finally:
        # Always release camera
        camera.release()

        # Close all OpenCV windows
        cv2.destroyAllWindows()

        print("Camera released successfully.")
        print("Program closed.")

if __name__ == "__main__":
    main()
