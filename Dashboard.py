import PySimpleGUI as sg
import time
import threading
import queue
import csv
import re
from serial_comm import SerialObj  # Asumiendo que serial_comm.py contiene la clase SerialObj

# Configuración del puerto serie
BAUD_RATE = 115200
SERIAL_QUEUE = queue.Queue()
STOP_THREAD_TRIGGER = False

# Variables iniciales
var1, var2, var3 = 0, 0, 0

def save_data_to_csv(file_name, data):
    """Función para guardar los datos en un archivo CSV."""
    with open(file_name, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(data)

# Función para manejar la comunicación serial
def start_serial_comm(serial_connector, serialport, gui_queue, stop_thread_trigger, file_name):
    global var1, var2, var3
    serial_connector.connect(serialport)
    if serial_connector.is_connect():
        gui_queue.put("Puerto serie conectado")

        while not stop_thread_trigger():
            try:
                data = serial_connector.get_data()
                if data is not None:
                    # Asumimos que los datos vienen en formato "var1,var2,var3"
                    values = re.sub(r"\s+", "", data.decode("utf-8")).split(",")
                    if len(values) == 3:
                        var1, var2, var3 = map(float, values)
                        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                        save_data_to_csv(file_name, [timestamp, var1, var2, var3])
            except (OSError, UnicodeDecodeError, ValueError):
                pass

        serial_connector.disconnect()
    return

def create_port_selection_window():
    """Ventana para seleccionar el puerto serie."""
    ports = SerialObj.get_ports()
    layout = [
        [sg.Text("Seleccionar puerto serie:")],
        [sg.Listbox(values=[port[0] for port in ports], size=(40, 6), key="-PORTS-")],
        [sg.Button("Seleccionar"), sg.Button("Cancelar")]
    ]
    window = sg.Window("Seleccionar Puerto Serie", layout, modal=True)
    event, values = window.read()
    selected_port = values["-PORTS-"][0] if event == "Seleccionar" and values["-PORTS-"] else None
    window.close()
    return selected_port

def create_file_save_window():
    """Ventana para elegir el archivo de guardado."""
    layout = [
        [sg.Text("Seleccionar archivo para guardar los datos:")],
        [sg.InputText(key="-FILE_PATH-"), sg.FileSaveAs(file_types=(('CSV Files', '*.csv'),))],
        [sg.Button("Guardar"), sg.Button("Cancelar")]
    ]
    window = sg.Window("Guardar Datos", layout, modal=True)
    event, values = window.read()
    file_path = values["-FILE_PATH-"] if event == "Guardar" else None
    window.close()
    return file_path

# Seleccionar puerto serie
selected_port = create_port_selection_window()
if not selected_port:
    sg.popup("No se seleccionó ningún puerto. Saliendo.", title="Error")
    exit()

# Seleccionar archivo para guardar los datos
file_name = create_file_save_window()
if not file_name:
    sg.popup("No se seleccionó ningún archivo. Saliendo.", title="Error")
    exit()

# Iniciar hilo para comunicación serial
serial_connector = SerialObj(BAUD_RATE)
thread_serial = threading.Thread(target=start_serial_comm, args=(serial_connector, selected_port, SERIAL_QUEUE, lambda: STOP_THREAD_TRIGGER, file_name), daemon=True)
thread_serial.start()

# Configuración del diseño del dashboard
layout = [
    [sg.Text("Banco de Pruebas de Cohete", font=("Helvetica", 20), justification="center", expand_x=True),sg.Text("", font=("Helvetica", 20), key="-TIME-", expand_x=True, justification="right")],
    [
        sg.Column([
            [sg.VPush()],
            [sg.Text("Variable 1:", font=("Helvetica", 16), justification="center")],
            [sg.Text("0", font=("Helvetica", 30), key="-VAR1-", justification="center")],
            [sg.Text("Variable 2:", font=("Helvetica", 16), justification="center")],
            [sg.Text("0", font=("Helvetica", 30), key="-VAR2-", justification="center")],
            [sg.Text("Variable 3:", font=("Helvetica", 16), justification="center")],
            [sg.Text("0", font=("Helvetica", 30), key="-VAR3-", justification="center")],
            [sg.VPush()]
        ], element_justification="center", expand_x=True, expand_y=True),
        sg.Column([
            [sg.VPush()],
            
            [sg.VPush()]
        ], element_justification="center", expand_x=True, expand_y=True),
        sg.Column([
            [sg.VPush()],
            
        ], element_justification="center", expand_x=True, expand_y=True),
    ],
    [sg.Button("Salir", size=(10, 1))]
]

# Crear la ventana del dashboard
window = sg.Window("Dashboard Banco de Pruebas", layout, size=(800, 600), element_justification="center", finalize=True)

# Loop principal para actualizar datos y la hora
while True:
    event, values = window.read(timeout=1000)  # Leer eventos con timeout de 1 segundo

    # Salir si el usuario cierra la ventana o presiona "Salir"
    if event == sg.WINDOW_CLOSED or event == "Salir":
        STOP_THREAD_TRIGGER = True
        thread_serial.join()
        break

    # Actualizar la hora
    current_time = time.strftime("%H:%M:%S")
    window["-TIME-"].update(current_time)

    # Actualizar las variables en el dashboard
    window["-VAR1-"].update(f"{var1:.2f}")
    window["-VAR2-"].update(f"{var2:.2f}")
    window["-VAR3-"].update(f"{var3:.2f}")

# Cerrar la ventana
window.close()