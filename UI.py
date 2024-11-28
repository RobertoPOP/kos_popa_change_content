import RPi.GPIO as GPIO
import time
import cv2
import numpy as np
import mysql.connector  # Biblioteca para conexión con la base de datos
import requests  # Biblioteca para descargar el video
import os  # Para gestionar rutas y archivos

# Configuración de los pines GPIO
RED_PIN = 24
GREEN_PIN = 5
BLUE_PIN = 6

GPIO.setmode(GPIO.BCM)
GPIO.setup(RED_PIN, GPIO.OUT)
GPIO.setup(GREEN_PIN, GPIO.OUT)
GPIO.setup(BLUE_PIN, GPIO.OUT)

# Crear PWM para cada canal de color con frecuencia de 100 Hz
red_pwm = GPIO.PWM(RED_PIN, 100)  
green_pwm = GPIO.PWM(GREEN_PIN, 100)
blue_pwm = GPIO.PWM(BLUE_PIN, 100)

# Iniciar PWM en 0% de duty cycle
red_pwm.start(0)
green_pwm.start(0)
blue_pwm.start(0)

# Función para escalar valores RGB de 0-255 a 0-100 para PWM
def scale_rgb(value):
    return (value / 255) * 100

# Función para configurar el color del LED usando PWM
def set_color(rgb):
    red_pwm.ChangeDutyCycle(scale_rgb(rgb[0]))
    green_pwm.ChangeDutyCycle(scale_rgb(rgb[1]))
    blue_pwm.ChangeDutyCycle(scale_rgb(rgb[2]))

# Función para reproducir video en bucle
def play_video(video_path, window_name="Reproduciendo video"):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error al abrir el video: {video_path}")
        return False

    cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    while True:
        ret, frame = cap.read()
        if not ret:  # Si el video termina, reinicia la reproducción
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        cv2.imshow(window_name, frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            return "stop"

# Conexión a la base de datos y descarga de datos
def fetch_data_and_download_video():
    try:
        # Configura las credenciales de la base de datos
        db_config = {
            'host': '82.180.172.63',
            'port': 3306,  # Puerto de MySQL
            'user': 'u958030263_Desarrollo_POP',
            'password': 'Beex2024%',
            'database': 'u958030263_KOS_POPA'
        }
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # Consulta SQL para obtener datos relevantes
        cursor.execute("SELECT nombreVideo, colorRGB FROM Media WHERE id = 1")  # Cambiar tabla y condiciones si es necesario
        result = cursor.fetchone()

        if result:
            video_url = result[0]
            color_rgb = list(map(int, result[1].split(',')))

            # Descargar el video
            response = requests.get(video_url)
            video_path = os.path.expanduser("~/Desktop/lidar-videos-leds/video.mp4")
            with open(video_path, 'wb') as file:
                file.write(response.content)

            print(f"Video descargado: {video_path}")
            print(f"Color RGB configurado: {color_rgb}")
            return video_path, color_rgb
        else:
            print("No se encontraron datos en la base de datos.")
            return None, None
    except Exception as e:
        print(f"Error al conectar con la base de datos o descargar el video: {e}")
        return None, None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Programa principal
try:
    # Obtener datos de la base de datos y configurar sistema
    video_path, color_rgb = fetch_data_and_download_video()
    if video_path and color_rgb:
        set_color(color_rgb)  # Configurar el color del LED

        # Reproducir el video en bucle infinito
        if play_video(video_path) == "stop":
            print("Programa detenido manualmente.")
    else:
        print("Error al inicializar el sistema. Verifique la base de datos o los datos descargados.")

finally:
    # Apagar LEDs y limpiar los pines GPIO al finalizar
    red_pwm.ChangeDutyCycle(0)
    green_pwm.ChangeDutyCycle(0)
    blue_pwm.ChangeDutyCycle(0)
    
    # Detener PWM
    red_pwm.stop()
    green_pwm.stop()
    blue_pwm.stop()
    
