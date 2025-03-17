import PySimpleGUI as sg
import time
import threading
import queue
import csv
import re
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from serial_comm import SerialObj  # Asumiendo que serial_comm.py contiene la clase SerialObj

# Configuración del puerto serie
BAUD_RATE = 115200
SERIAL_QUEUE = queue.Queue()
STOP_THREAD_TRIGGER = False

IMAGEN = "C:/Users/vjere/OneDrive/Escritorio/Coheteria/Dashboard/horizontal.png"
# Variables iniciales
var1, var2, var3 = 0, 0, 0
history_var1, history_var2, history_var3 = [], [], []

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
# Función para actualizar el gráfico
# Función para actualizar los gráficos
def update_graph(fig_canvas_agg, ax, history, label, color):
    ax.cla()
    ax.plot(history, label=label, color=color)
    ax.set_title(f"{label} en tiempo real")
    ax.set_xlabel("Tiempo")
    ax.set_ylabel("Valor")
    fig_canvas_agg.draw()

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
    [sg.Image(filename=IMAGEN, ),
     sg.Text("Banco de Pruebas", font=("Helvetica", 20), justification="left", expand_x=True),
     sg.Text("", font=("Helvetica", 20), key="-TIME-", expand_x=True, justification="right")],
    [
        sg.Column([
            [sg.VPush()],
            [sg.Text("Empuje:", font=("Helvetica", 16), justification="center")],
            [sg.Text("0", font=("Helvetica", 30), key="-VAR1-", justification="center")],
            [sg.Text("Temperatura \n ambiente:", font=("Helvetica", 16), justification="center")],
            [sg.Text("0", font=("Helvetica", 30), key="-VAR2-", justification="center")],
            [sg.Text("Temperatura \n  tobera:", font=("Helvetica", 16), justification="center")],
            [sg.Text("0", font=("Helvetica", 30), key="-VAR3-", justification="center")],
            [sg.VPush()]
        ], element_justification="center", expand_x=True, expand_y=True),
        sg.Column([
            [sg.Canvas(key="-CANVAS1-", size=(50, 50))],
        ], element_justification="center", expand_x=True),
        sg.Column([
            [sg.Canvas(key="-CANVAS2-", size=(50, 50))]
        ], element_justification="center", expand_x=True),
        sg.Column([
            [sg.Canvas(key="-CANVAS3-", size=(50, 50))]
        ], element_justification="center", expand_x=True)
    ],
    [sg.Button("Salir", size=(10, 1))]
]

# Crear la ventana del dashboard
window = sg.Window("Dashboard Banco de Pruebas", layout, size=(1050, 800), element_justification="center", finalize=True)

# Configuración de gráficos
fig1, ax1 = plt.subplots(figsize=(3, 4))  # Cambia los valores según el tamaño deseado
fig_canvas_agg1 = FigureCanvasTkAgg(fig1, window["-CANVAS1-"].Widget)
fig_canvas_agg1.get_tk_widget().pack(side="top", fill="both", expand=1)

fig2, ax2 = plt.subplots(figsize=(3, 4))  # Cambia los valores según el tamaño deseado
fig_canvas_agg2 = FigureCanvasTkAgg(fig2, window["-CANVAS2-"].Widget)
fig_canvas_agg2.get_tk_widget().pack(side="top", fill="both", expand=1)

fig3, ax3 = plt.subplots(figsize=(3, 4))  # Cambia los valores según el tamaño deseado
fig_canvas_agg3 = FigureCanvasTkAgg(fig3, window["-CANVAS3-"].Widget)
fig_canvas_agg3.get_tk_widget().pack(side="top", fill="both", expand=1)


# Loop principal para actualizar datos y la hora
while True:
    event, values = window.read(timeout=500)  # Leer eventos con timeout de 1 segundo

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

    # Actualizar los datos históricos para el gráfico
    history_var1.append(var1)
    history_var2.append(var2)
    history_var3.append(var3)

    # Limitar la longitud del historial
    # Limitar la longitud del historial
    if len(history_var1) > 30:
        history_var1.pop(0)
    if len(history_var2) > 30:
        history_var2.pop(0)
    if len(history_var3) > 30:
        history_var3.pop(0)


    # Actualizar el gráfico
    update_graph(fig_canvas_agg1, ax1, history_var1, "Empuje", "red")
    update_graph(fig_canvas_agg2, ax2, history_var2, "Temp 1", "green")
    update_graph(fig_canvas_agg3, ax3, history_var3, "Temp 2", "blue")


# Cerrar la ventana
window.close()