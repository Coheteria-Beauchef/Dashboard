import PySimpleGUI as sg
import time
import csv
import re
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from serial_comm import SerialObj  # Asumiendo que serial_comm.py contiene la clase SerialObj

# Configuración del puerto serie
BAUD_RATE = 115200
IMAGEN = "C:/Users/vjere/OneDrive/Escritorio/Coheteria/Dashboard/Dashboard/horizontal.png"

# Variables iniciales
var1, var2, var3 = 0, 0, 0
history_var1, history_var2, history_var3 = [], [], []

def save_data_to_csv(file_name, data):
    """Función para guardar los datos en un archivo CSV."""
    with open(file_name, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(data)

def create_port_selection_window():
    """Ventana para seleccionar el puerto serie."""
    ports = SerialObj.get_ports()
    layout = [[sg.Text("Seleccionar puerto serie:")],
              [sg.Listbox(values=[port[0] for port in ports], size=(40, 6), key="-PORTS-")],
              [sg.Button("Seleccionar"), sg.Button("Cancelar")]]
    window = sg.Window("Seleccionar Puerto Serie", layout, modal=True)
    event, values = window.read()
    selected_port = values["-PORTS-"][0] if event == "Seleccionar" and values["-PORTS-"] else None
    window.close()
    return selected_port

def create_file_save_window():
    """Ventana para elegir el archivo de guardado."""
    layout = [[sg.Text("Seleccionar archivo para guardar los datos:")],
              [sg.InputText(key="-FILE_PATH-"), sg.FileSaveAs(file_types=(('CSV Files', '*.csv'),))],
              [sg.Button("Guardar"), sg.Button("Cancelar")]]
    window = sg.Window("Guardar Datos", layout, modal=True)
    event, values = window.read()
    file_path = values["-FILE_PATH-"] if event == "Guardar" else None
    window.close()
    return file_path

def update_graph(fig_canvas_agg, ax, history, label, color):
    ax.cla()
    ax.plot(history, label=label, color=color)
    ax.set_title(f"{label} en tiempo real")
    ax.set_xlabel("Tiempo")
    ax.set_ylabel("Valor")
    fig_canvas_agg.draw()

selected_port = create_port_selection_window()
if not selected_port:
    sg.popup("No se seleccionó ningún puerto. Saliendo.", title="Error")
    exit()

file_name = create_file_save_window()
if not file_name:
    sg.popup("No se seleccionó ningún archivo. Saliendo.", title="Error")
    exit()

serial_connector = SerialObj(BAUD_RATE)
serial_connector.connect(selected_port)
if not serial_connector.is_connect():
    sg.popup("No se pudo conectar al puerto seleccionado. Saliendo.", title="Error")
    exit()

layout = [
    [sg.Image(filename=IMAGEN)],
    [sg.Text("Banco de Pruebas", font=("Helvetica", 20)), sg.Text("", font=("Helvetica", 20), key="-TIME-")],
    [
        sg.Column([
            [sg.Text("Empuje:"), sg.Text("0", font=("Helvetica", 30), key="-VAR1-")],
            [sg.Canvas(key="-CANVAS1-")]
        ], element_justification="center"),
        sg.Column([
            [sg.Text("Temperatura ambiente:"), sg.Text("0", font=("Helvetica", 30), key="-VAR2-")],
            [sg.Canvas(key="-CANVAS2-")]
        ], element_justification="center"),
        sg.Column([
            [sg.Text("Temperatura tobera:"), sg.Text("0", font=("Helvetica", 30), key="-VAR3-")],
            [sg.Canvas(key="-CANVAS3-")]
        ], element_justification="center")
    ],
    [sg.Button("Salir")]
]

window = sg.Window("Dashboard Banco de Pruebas", layout, finalize=True)

fig1, ax1 = plt.subplots(figsize=(3, 4))
fig_canvas_agg1 = FigureCanvasTkAgg(fig1, window["-CANVAS1-"].Widget)
fig_canvas_agg1.get_tk_widget().pack(side="top", fill="both", expand=1)

fig2, ax2 = plt.subplots(figsize=(3, 4))
fig_canvas_agg2 = FigureCanvasTkAgg(fig2, window["-CANVAS2-"].Widget)
fig_canvas_agg2.get_tk_widget().pack(side="top", fill="both", expand=1)

fig3, ax3 = plt.subplots(figsize=(3, 4))
fig_canvas_agg3 = FigureCanvasTkAgg(fig3, window["-CANVAS3-"].Widget)
fig_canvas_agg3.get_tk_widget().pack(side="top", fill="both", expand=1)

while True:
    event, values = window.read(timeout=500)
    if event == sg.WINDOW_CLOSED or event == "Salir":
        break

    current_time = time.strftime("%H:%M:%S")
    window["-TIME-"].update(current_time)

    try:
        data = serial_connector.get_data()
        if data:
            values = re.sub(r"\s+", "", data.decode("utf-8")).split(",")
            if len(values) == 3:
                var1, var2, var3 = map(float, values)
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                save_data_to_csv(file_name, [timestamp, var1, var2, var3])
                history_var1.append(var1)
                history_var2.append(var2)
                history_var3.append(var3)

                if len(history_var1) > 30:
                    history_var1.pop(0)
                if len(history_var2) > 30:
                    history_var2.pop(0)
                if len(history_var3) > 30:
                    history_var3.pop(0)

                window["-VAR1-"].update(f"{var1:.2f}")
                window["-VAR2-"].update(f"{var2:.2f}")
                window["-VAR3-"].update(f"{var3:.2f}")

                update_graph(fig_canvas_agg1, ax1, history_var1, "Empuje", "red")
                update_graph(fig_canvas_agg2, ax2, history_var2, "Temp 1", "green")
                update_graph(fig_canvas_agg3, ax3, history_var3, "Temp 2", "blue")
    except (OSError, UnicodeDecodeError, ValueError):
        pass

serial_connector.disconnect()
window.close()
