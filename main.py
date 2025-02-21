import os
import sys
import datetime
from PyQt5 import QtWidgets
from PyQt5 import QtCore,QtGui,QtWidgets
from PyQt5.QtGui import QMovie
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QUrl
from PyQt5 import uic
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtCore import QDateTime, Qt, QDate
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QTimer 
from twilio.rest import Client
from email.mime.text import MIMEText
# Importar las interfaces convertidas desde los archivos .py
from recursos.qt.principal import Ui_MainWindow
from recursos.qt.actualizar_prod import Ui_actualizar_prod as Ui_ActualizarProd
from recursos.qt.agregar_prod import Ui_VentanaAnadirProducto as Ui_AgregarProd
from recursos.qt.edit_user import Ui_Dialog as Ui_EditarUsuario
from recursos.qt.registro import Ui_Dialog as Ui_Registro
from recursos.qt.login import Ui_ingresar as Ui_Login
import re
import csv
import math
import smtplib
import requests

def get_resource_path(relative_path):
    """ Retorna la ruta correcta del recurso, ya sea en el script normal o en un .exe compilado. """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)  # Para ejecutable .exe
    return os.path.join(os.path.abspath("."), relative_path)  # Para ejecución normal

# Definir rutas para los archivos CSV
csv_path = get_resource_path("recursos/bd/productos.csv")
csv_user = get_resource_path("recursos/bd/usuarios.csv")

# Función para enviar un email de bienvenida
def enviar_email(destinatario, nombre):
    remitente = "osmelalvarez009@gmail.com"
    contraseña = "mortadela192211"
    mensaje = MIMEText(f"¡Hola {nombre}!\n\nBienvenido a nuestra aplicacion. Estamos felices de tenerte con nosotros.")
    mensaje["Subject"] = "Bienvenido a nuestra aplicacion"
    mensaje["From"] = remitente
    mensaje["To"] = destinatario

    try:
        servidor = smtplib.SMTP("smtp.gmail.com", 587)
        servidor.starttls()  # Iniciar comunicación segura
        servidor.login(remitente, contraseña)
        servidor.sendmail(remitente, destinatario, mensaje.as_string())
        servidor.quit()
        print(f"✅ Email enviado a {destinatario}")
    except Exception as e:
        print(f"❌ Error al enviar email: {e}")

# Función para enviar un mensaje de WhatsApp
def enviar_mensaje_whatsapp(telefono, nombre):
    # Reemplaza con tus credenciales de Twilio
    ACCOUNT_SID = "AC755ce00e54b4cb090d793dd3af721e28"
    AUTH_TOKEN = "f9f366992812f8ff481efdcbcbda609d"
    TWILIO_PHONE_NUMBER = "whatsapp:+14155238886"  # Número de WhatsApp de Twilio

    client = Client(ACCOUNT_SID, AUTH_TOKEN)

    try:
        mensaje = client.messages.create(
            body=f"¡Hola {nombre}! Bienvenido a nuestra tienda. ¡Esperamos que disfrutes tu experiencia!",
            from_=TWILIO_PHONE_NUMBER,
            to=f"whatsapp:{telefono}"
        )
        print(f"✅ Mensaje de WhatsApp enviado a {telefono}")
    except Exception as e:
        print(f"❌ Error al enviar mensaje de WhatsApp: {e}")


class DataManager:
    def __init__(self, productos_file="productos.csv", usuarios_file="usuarios.csv"):
        self.productos_file = productos_file
        self.usuarios_file = usuarios_file

    def guardar_producto(self, nombre, precio, cantidad, categoria):
        with open(self.productos_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([nombre, precio, cantidad, categoria, QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")])

    def cargar_productos(self):
        productos = []
        with open(self.productos_file, mode='r', newline='') as file:
            reader = csv.reader(file)
            for row in reader:
                productos.append(row)
        return productos


class Login(QDialog, Ui_Login):
    usuario_registrado = pyqtSignal()
    autenticacion_exitosa = pyqtSignal()

    def __init__(self, csv_user):
        super(Login, self).__init__()
        self.setupUi(self)
        self.csv_user = csv_user
        self.setWindowTitle("Login")
        
        # 📌 Buscar widgets
        self.name_line = self.findChild(QtWidgets.QLineEdit, 'name_line')
        self.pass_line = self.findChild(QtWidgets.QLineEdit, 'pass_line')
        self.login_btn = self.findChild(QtWidgets.QPushButton, 'login_btn')
        self.close_btn = self.findChild(QtWidgets.QPushButton, 'close_btn')
        self.register_btn = self.findChild(QtWidgets.QPushButton, 'register_btn')
        self.img_label = self.findChild(QtWidgets.QLabel, 'img_label')

        # 📌 Conectar botones
        if self.login_btn:
            self.login_btn.clicked.connect(self.verificar_credenciales)
        else:
            print("⚠️ Error: No se encontró 'login_btn' en la UI.")

        if self.close_btn:
            self.close_btn.clicked.connect(self.close)
        else:
            print("⚠️ Error: No se encontró 'close_btn' en la UI.")

        if self.register_btn:
            self.register_btn.clicked.connect(self.abrir_registro)
        else:
            print("⚠️ Error: No se encontró 'register_btn' en la UI.")

        # 📌 Agregar GIF animado
        if self.img_label:
            self.movie = QMovie(r"recursos/img/maxwell2.gif")
            self.img_label.setMovie(self.movie)
            self.movie.start()

    def verificar_credenciales(self):
        """Verifica si el usuario ingresó su nombre o correo y valida la contraseña en el CSV."""
        usuario_input = self.name_line.text().strip()
        password = self.pass_line.text().strip()

        if not usuario_input or not password:
            QMessageBox.critical(self, "Error", "Todos los campos son obligatorios.")
            return

        try:
            with open(self.csv_user, mode="r", newline='', encoding="utf-8") as file:
                reader = csv.reader(file)
                for row in reader:
                    if len(row) >= 6:  # Asegurar que hay suficientes columnas
                        nombre = row[0]  # Nombre de usuario
                        correo = row[1]  # Correo electrónico
                        contraseña = row[4]  # Contraseña
                        tipo_usuario = row[5].lower()  # Tipo de usuario (admin o normal)

                        # Comprobamos si el input coincide con el nombre o el correo y si la contraseña es correcta
                        if (usuario_input == nombre or usuario_input == correo) and password == contraseña:
                            QMessageBox.information(self, "Bienvenido", f"¡Hola, {nombre}!")

                            # 📌 Pasamos el tipo de usuario a la ventana principal
                            self.cerrar_y_abrir_principal(tipo_usuario)
                            return
        except FileNotFoundError:
            QMessageBox.critical(self, "Error", "No se encontró la base de datos de usuarios.")
            return

        QMessageBox.critical(self, "Error", "Usuario o contraseña incorrectos.")

    def cerrar_y_abrir_principal(self, tipo_usuario):
        """Cierra el login y abre la ventana principal en pantalla completa con los permisos adecuados."""
        self.close()
        
        # 📌 Asegurar que pasamos correctamente ambos archivos CSV
        csv_path = "recursos/bd/productos.csv"  # Ruta del CSV de productos
        csv_user = self.csv_user  # CSV de usuarios

        self.ventana_principal = VentanaPrincipal(csv_path, csv_user) 
        self.ventana_principal.set_tipo_usuario(tipo_usuario)  
        self.ventana_principal.showMaximized()

    def abrir_registro(self):
        """Cierra el login y abre la ventana de registro."""
        self.close()
        self.ventana_registro = Registro(self.csv_user, origen="login")  
        self.ventana_registro.show()




class Registro(QDialog, Ui_Registro):
    def __init__(self, csv_user, origen):
        super(Registro, self).__init__()
        self.setupUi(self)
        self.csv_user = csv_user
        self.origen = origen  
        

        # Widgets
        self.name_user_line = self.findChild(QtWidgets.QLineEdit, 'name_user_line')
        self.mail_line = self.findChild(QtWidgets.QLineEdit, 'mail_line')
        self.tel_line = self.findChild(QtWidgets.QLineEdit, 'tel_line')
        self.dir_line = self.findChild(QtWidgets.QLineEdit, 'dir_line')
        self.pass_user_line = self.findChild(QtWidgets.QLineEdit, 'pass_user_line')
        self.rep_pass_user_line = self.findChild(QtWidgets.QLineEdit, 'rep_pass_user_line')
        self.aceptar_btn = self.findChild(QtWidgets.QPushButton, 'aceptar_btn')
        self.salir_btn = self.findChild(QtWidgets.QPushButton, 'salir_btn')

        # Conectar botones
        self.aceptar_btn.clicked.connect(self.registrar_usuario)
        self.salir_btn.clicked.connect(self.volver)

    def volver(self):
        """Cierra el registro y abre la ventana que corresponde (login o principal)."""
        self.close()
        if self.origen == "login":
            self.ventana_login = Login(self.csv_user)
            self.ventana_login.show()
        else:
            self.ventana_principal = VentanaPrincipal(self.csv_user)
            self.ventana_principal.showMaximized()

    def validar_datos(self, nombre, email, telefono, direccion, password, rep_password):
        """Valida los datos con expresiones regulares"""
        patron_email = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        patron_telefono = r"^\+?\d{7,15}$"  # Admite formato internacional (+123456789)

        if not re.match(patron_email, email):
            QMessageBox.critical(self, "Error", "Email inválido.")
            return False
        if not re.match(patron_telefono, telefono):
            QMessageBox.critical(self, "Error", "Número de teléfono inválido.")
            return False
        if password != rep_password:
            QMessageBox.critical(self, "Error", "Las contraseñas no coinciden.")
            return False
        return True

    def email_existe(self, email):
        """Verifica si el email ya está registrado en el CSV"""
        try:
            with open(self.csv_user, mode="r", newline='', encoding="utf-8") as file:
                reader = csv.reader(file)
                for row in reader:
                    if row and row[1] == email:
                        return True
        except FileNotFoundError:
            return False
        return False

    def registrar_usuario(self):
        """Guarda el usuario en el CSV si es válido"""
        nombre = self.name_user_line.text().strip()
        email = self.mail_line.text().strip()
        telefono = self.tel_line.text().strip()
        direccion = self.dir_line.text().strip()
        password = self.pass_user_line.text().strip()
        rep_password = self.rep_pass_user_line.text().strip()
        tipo_usuario = "Usuario"  

        if not self.validar_datos(nombre, email, telefono, direccion, password, rep_password):
            return
        if self.email_existe(email):
            QMessageBox.critical(self, "Error", "El email ya está registrado.")
            return

        # Guardar usuario en CSV
        try:
            with open(self.csv_user, mode="a", newline='', encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow([nombre, email, telefono, direccion, password, tipo_usuario])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo registrar el usuario: {e}")
            return

        QMessageBox.information(self, "Éxito", "Usuario registrado correctamente.")

        # Enviar email y WhatsApp
        enviar_email(email, nombre)
        enviar_mensaje_whatsapp(telefono, nombre)

        self.close()

class VentanaEditarUsuario(QDialog, Ui_EditarUsuario):
    def __init__(self, csv_user, usuario_actual):
        super(VentanaEditarUsuario, self).__init__()
        self.setupUi(self)
        self.csv_user = csv_user
        self.usuario_actual = usuario_actual  # Diccionario con los datos del usuario seleccionado
        # 📌 Buscar widgets
        self.name_user_line = self.findChild(QtWidgets.QLineEdit, 'name_user_line')
        self.mail_line = self.findChild(QtWidgets.QLineEdit, 'mail_line')
        self.tel_line = self.findChild(QtWidgets.QLineEdit, 'tel_line')
        self.dir_line = self.findChild(QtWidgets.QLineEdit, 'dir_line')
        self.pass_user_line = self.findChild(QtWidgets.QLineEdit, 'pass_user_line')
        self.rep_pass_user_line = self.findChild(QtWidgets.QLineEdit, 'rep_pass_user_line')
        self.guardar_btn = self.findChild(QtWidgets.QPushButton, 'guardar_btn')
        self.cancel_btn = self.findChild(QtWidgets.QPushButton, 'cancel_btn')

        # Llenar los campos con los datos del usuario
        self.cargar_datos_usuario()

        # Conectar botones
        self.guardar_btn.clicked.connect(self.guardar_cambios)
        self.cancel_btn.clicked.connect(self.close)

    def cargar_datos_usuario(self):
        """Carga los datos actuales del usuario en los campos"""
        self.name_user_line.setText(self.usuario_actual["nombre"])
        self.mail_line.setText(self.usuario_actual["email"])
        self.mail_line.setDisabled(True)  # No se puede modificar el email
        self.tel_line.setText(self.usuario_actual["telefono"])
        self.dir_line.setText(self.usuario_actual["direccion"])
        self.pass_user_line.setText(self.usuario_actual["password"])
        self.rep_pass_user_line.setText(self.usuario_actual["password"])  # Repetir contraseña

    def guardar_cambios(self):
        """Guarda los cambios del usuario en el CSV"""
        nombre = self.name_user_line.text().strip()
        telefono = self.tel_line.text().strip()
        direccion = self.dir_line.text().strip()
        password = self.pass_user_line.text().strip()
        rep_password = self.rep_pass_user_line.text().strip()

        # Validar los datos
        if not nombre or not telefono or not direccion or not password or not rep_password:
            QMessageBox.critical(self, "Error", "Todos los campos son obligatorios.")
            return
        
        if password != rep_password:
            QMessageBox.critical(self, "Error", "Las contraseñas no coinciden.")
            return

        # Actualizar el usuario en el CSV
        if self.actualizar_usuario_csv(nombre, telefono, direccion, password):
            QMessageBox.information(self, "Éxito", "Usuario actualizado correctamente.")
            self.close()
        else:
            QMessageBox.critical(self, "Error", "No se pudo actualizar el usuario.")

    def actualizar_usuario_csv(self, nombre, telefono, direccion, password):
        """Modifica los datos del usuario en el CSV"""
        try:
            usuarios = []
            with open(self.csv_user, mode="r", newline='', encoding="utf-8") as file:
                reader = csv.reader(file)
                for row in reader:
                    if row and row[1] == self.usuario_actual["email"]:  # Comparar con el email (único)
                        usuarios.append([nombre, row[1], telefono, direccion, password, "Usuario"])
                    else:
                        usuarios.append(row)

            with open(self.csv_user, mode="w", newline='', encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerows(usuarios)

            return True
        except Exception as e:
            print(f"Error al actualizar el usuario: {e}")
            return False

class VentanaAnadirProducto(QtWidgets.QDialog, Ui_AgregarProd):
    def __init__(self, csv_path, actualizar_func):
        super(VentanaAnadirProducto, self).__init__()
        self.setupUi(self)
        self.csv_path = csv_path
        self.actualizar_func = actualizar_func

        # Widgets según los objectName definidos en Qt Designer
        self.nombre_line = self.findChild(QtWidgets.QLineEdit, 'nombre_line')
        self.cat_line = self.findChild(QtWidgets.QLineEdit, 'cat_line')
        self.fecha_edit = self.findChild(QtWidgets.QDateEdit, 'fecha_edit')
        self.hoy_btn = self.findChild(QtWidgets.QPushButton, 'hoy_btn')
        self.cant_spin = self.findChild(QtWidgets.QSpinBox, 'cant_spin')
        self.precio_line = self.findChild(QtWidgets.QLineEdit, 'precio_line')
        self.cancel_btn = self.findChild(QtWidgets.QPushButton, 'cancel_btn')
        self.done_btn = self.findChild(QtWidgets.QPushButton, 'done_btn')

        # Configuración del QDateEdit
        self.fecha_edit.setCalendarPopup(True)
        self.fecha_edit.setDate(QDate.currentDate())  # Fecha predeterminada: hoy
        self.hoy_btn.clicked.connect(self.set_fecha_hoy)

        # Conectar los botones
        self.done_btn.clicked.connect(self.agregar_producto)
        self.cancel_btn.clicked.connect(self.close)

    def set_fecha_hoy(self):
        """Establece la fecha de hoy en el QDateEdit."""
        self.fecha_edit.setDate(QDate.currentDate())

    def agregar_producto(self):
        """
        Recoge la información de los widgets y guarda un nuevo producto en el CSV.
        """
        nombre = self.nombre_line.text().strip()
        categoria = self.cat_line.text().strip()
        cantidad = self.cant_spin.value()
        precio_text = self.precio_line.text().strip()
        fecha_creacion = self.fecha_edit.date().toString("yyyy-MM-dd")

        # Validación de campos obligatorios
        if not nombre or not categoria:
            self.mostrar_error("El nombre y la categoría son obligatorios.")
            return

        if not precio_text:
            self.mostrar_error("El campo Precio es obligatorio.")
            return

        try:
            precio = float(precio_text)
            if precio <= 0:
                raise ValueError
        except ValueError:
            self.mostrar_error("Ingrese un precio válido (mayor a 0).")
            return

        # Verificar si el producto ya existe (usando el nombre como identificador)
        if self.producto_existe(nombre):
            self.mostrar_advertencia("El producto ya existe en el inventario.")
            return

        # Preparar la fila del producto
        producto = [nombre, str(cantidad), f"{precio:.2f}", categoria, fecha_creacion]
        try:
            with open(self.csv_path, mode="a", newline='', encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(producto)
        except Exception as e:
            self.mostrar_error(f"No se pudo agregar el producto: {e}")
            return

        self.mostrar_informacion("Producto agregado correctamente.")

        # Actualizar la tabla en la ventana principal y cerrar
        if self.actualizar_func:
            self.actualizar_func()
        self.close()

    def producto_existe(self, nombre):
        """Verifica si un producto ya existe en el CSV, comparando el nombre (sin distinguir mayúsculas)."""
        try:
            with open(self.csv_path, mode="r", newline='', encoding="utf-8") as file:
                reader = csv.reader(file)
                for row in reader:
                    if row and row[0].strip().lower() == nombre.lower():
                        return True
        except FileNotFoundError:
            return False
        return False

    def mostrar_error(self, mensaje):
        QtWidgets.QMessageBox.critical(self, "Error", mensaje)

    def mostrar_advertencia(self, mensaje):
        QtWidgets.QMessageBox.warning(self, "Advertencia", mensaje)

    def mostrar_informacion(self, mensaje):
        QtWidgets.QMessageBox.information(self, "Información", mensaje)
                
class VentanaEditarProducto(QtWidgets.QDialog, Ui_ActualizarProd):
    def __init__(self, csv_path, producto_actual, actualizar_func):
        super(VentanaEditarProducto, self).__init__()
        self.setupUi(self)
        self.csv_path = csv_path
        self.producto_actual = producto_actual
        self.actualizar_func = actualizar_func

        # Widgets según los objectName definidos en Qt Designer
        self.nombre_line = self.findChild(QtWidgets.QLineEdit, 'nombre_line')
        self.cat_line = self.findChild(QtWidgets.QLineEdit, 'cat_line')
        self.fecha_edit = self.findChild(QtWidgets.QDateEdit, 'fecha_edit')
        self.hoy_btn = self.findChild(QtWidgets.QPushButton, 'hoy_btn')
        self.cant_spin = self.findChild(QtWidgets.QSpinBox, 'cant_spin')
        self.precio_line = self.findChild(QtWidgets.QLineEdit, 'precio_line')
        self.close_btn = self.findChild(QtWidgets.QPushButton, 'close_btn')
        self.done_btn = self.findChild(QtWidgets.QPushButton, 'done_btn')

        # Configuración del QDateEdit
        self.fecha_edit.setCalendarPopup(True)
        self.hoy_btn.clicked.connect(self.set_fecha_hoy)

        # Conectar los botones
        self.done_btn.clicked.connect(self.editar_producto)
        self.close_btn.clicked.connect(self.close)

        # Cargar los datos del producto en los campos
        self.cargar_datos_producto()

    def set_fecha_hoy(self):
        """Establece la fecha de hoy en el QDateEdit."""
        self.fecha_edit.setDate(QDate.currentDate())

    def cargar_datos_producto(self):
        """Carga los datos del producto seleccionado en los campos de edición."""
        print("Producto recibido:", self.producto_actual)
        print("Tipo de producto:", type(self.producto_actual))

        if not self.producto_actual:
            self.mostrar_error("No se encontró el producto.")
            return

        # Acceder a los valores del diccionario con .get() para evitar KeyError
        self.nombre_line.setText(self.producto_actual.get("nombre", ""))
        self.cant_spin.setValue(int(self.producto_actual.get("cantidad", 0)))
        self.precio_line.setText(self.producto_actual.get("precio", ""))
        self.cat_line.setText(self.producto_actual.get("categoria", ""))

        fecha_str = self.producto_actual.get("fecha", "")
        fecha = QDate.fromString(fecha_str, "dd/MM/yyyy")  # Ajustar formato de fecha según lo recibido
        self.fecha_edit.setDate(fecha if fecha.isValid() else QDate.currentDate())

    def editar_producto(self):
        """
        Guarda los cambios en el producto y actualiza el CSV.
        """
        nombre = self.nombre_line.text().strip()
        categoria = self.cat_line.text().strip()
        cantidad = self.cant_spin.value()
        precio_text = self.precio_line.text().strip()
        fecha_creacion = self.fecha_edit.date().toString("dd/MM/yyyy")

        # Validación de campos obligatorios
        if not nombre or not categoria:
            self.mostrar_error("El nombre y la categoría son obligatorios.")
            return

        if not precio_text:
            self.mostrar_error("El campo Precio es obligatorio.")
            return

        try:
            precio = float(precio_text)
            if precio <= 0:
                raise ValueError
        except ValueError:
            self.mostrar_error("Ingrese un precio válido (mayor a 0).")
            return

        # Actualizar el producto en el CSV
        if self.actualizar_producto_csv(nombre, cantidad, precio, categoria, fecha_creacion):
            self.mostrar_informacion("Producto actualizado correctamente.")
            if self.actualizar_func:
                self.actualizar_func()
            self.close()
        else:
            self.mostrar_error("No se pudo actualizar el producto.")

    def actualizar_producto_csv(self, nombre, cantidad, precio, categoria, fecha):
        """Actualiza el producto en el archivo CSV."""
        try:
            productos = []
            with open(self.csv_path, mode="r", newline='', encoding="utf-8") as file:
                reader = csv.reader(file)
                productos = [row for row in reader]
            file.close()  # Asegura que el archivo se cierre antes de escribir en él.

            with open(self.csv_path, mode="w", newline='', encoding="utf-8") as file:
                writer = csv.writer(file)
                for row in productos:
                    if row and row[0] == self.producto_actual.get("nombre"):  # Buscar por nombre
                        writer.writerow([nombre, str(cantidad), f"{precio:.2f}", categoria, fecha])
                    else:
                        writer.writerow(row)

            return True
        except Exception as e:
            print(f"Error al actualizar el producto: {e}")
            return False


    def mostrar_error(self, mensaje):
        QtWidgets.QMessageBox.critical(self, "Error", mensaje)

    def mostrar_informacion(self, mensaje):
        QtWidgets.QMessageBox.information(self, "Información", mensaje)      
        
class VentanaPrincipal(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, csv_path, csv_user):
        super(VentanaPrincipal, self).__init__()
        self.setupUi(self)
        self.csv_path = csv_path
        self.csv_user = csv_user
        self.mostrar_datos_productos()
        self.mostrar_datos_usuarios()
        self.actualizar_hora_fecha()  # Actualizar la hora y el día cada segundo        self.timer = QTimer(self)        self.timer.timeout.connect(self.actualizar_hora_fecha)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.actualizar_hora_fecha)
        self.timer.start(1000)
        self.table_prod.setEditTriggers(QTableWidget.NoEditTriggers)
        self.menu_btn.clicked.connect(self.toggle_frame_controls)
        self.inico_btn.clicked.connect(self.mostrarPaginaInicio)
        self.productos_btn.clicked.connect(self.mostrarPaginaProductos)
        self.ayuda_btn.clicked.connect(self.mostrarPaginaayuda)
        self.usuarios_btn.clicked.connect(self.mostrarPaginausuarios)
        self.salir_btn.clicked.connect(self.salir)
        self.nombre_btn.clicked.connect(self.ordenar_por_nombre)
        self.cat_btn.clicked.connect(self.ordenar_por_categoria)
        self.new_btn.clicked.connect(self.ordenar_por_nuevos)
        self.old_btn.clicked.connect(self.ordenar_por_viejos)
        self.update_btn.clicked.connect(self.actualizar_tabla_productos)
        self.edit_btn.clicked.connect(self.editar_producto)
        self.eliminar_btn.clicked.connect(self.eliminar_producto)
        self.agregar_btn.clicked.connect(self.anadir_producto)
        self.primera_btn.clicked.connect(self.primera_pag)
        self.anterior_btn.clicked.connect(self.pagina_anterior)
        self.siguiente_btn.clicked.connect(self.siguiente_pag)
        self.ultima_btn.clicked.connect(self.ultima_pag)
        self.primera_btn_2.clicked.connect(self.primera_pag)
        self.anterior_btn_2.clicked.connect(self.pagina_anterior)
        self.siguiente_btn_2.clicked.connect(self.siguiente_pag)
        self.ultima_btn_2.clicked.connect(self.ultima_pag)
        self.agregar_user_btn.clicked.connect(self.abrir_registro)
        self.edit_user_btn.clicked.connect(self.abrir_editar_usuario)
        self.delete_user_btn.clicked.connect(self.eliminar_usuario)
        self.set_visibilidad_botones_admin(False)
      
      # Crear un QMovie para el GIF
        self.movie = QMovie(r"recursos/img/maxwell2.gif")

        # Asignar el QMovie al QLabel
        self.img_label.setMovie(self.movie)

            # Iniciar la reproducción del GIF
        self.movie.start()

    def set_tipo_usuario(self, tipo_usuario):
        self.tipo_usuario = tipo_usuario
        if tipo_usuario == 'admin':
            self.set_visibilidad_botones_admin(True)
        else:
            self.set_visibilidad_botones_admin(False)
            
    def set_visibilidad_botones_admin(self, visible):
        self.usuarios_btn.setVisible(visible)
    
    def salir(self):
        QtWidgets.QApplication.quit()
    
      # Métodos para cambiar de página
    def mostrarPaginaInicio(self):
        self.stackedWidget.setCurrentWidget(self.home)

    def mostrarPaginausuarios(self):
        self.stackedWidget.setCurrentWidget(self.usuarios)
        # También actualizamos la tabla de usuarios si es necesario
        self.actualizar_tabla_usuarios()

    def mostrarPaginaayuda(self):
        self.stackedWidget.setCurrentWidget(self.ayuda)

    def mostrarPaginaProductos(self):
        self.stackedWidget.setCurrentWidget(self.productos)  
    
    def actualizar_datos_tabla(self):
        self.mostrar_datos_productos()   
        
    def actualizar_hora_fecha(self):
        # Obtener la fecha y hora actual
        ahora = QDateTime.currentDateTime()

        # Formatear la hora actual como "HH:mm:ss"
        hora_texto = ahora.toString("HH:mm:ss")

        # Formatear el día de la semana y la fecha como "Día, DD de Mes de Año"
        fecha_texto = ahora.toString("dddd, d 'de' MMMM 'de' yyyy")

        # Mostrar la hora y la fecha en los QLabel correspondientes
        self.hora.setText("Hora actual: " + hora_texto)
        self.dia.setText("Fecha actual: " + fecha_texto)
      
    def toggle_frame_controls(self):
        if self.frame_controls.isVisible():
            # Si el frame está visible, lo ocultamos hacia la izquierda
            self.frame_controls.setVisible(False)
            self.frame_controls.setGeometry(-self.frame_controls.width(), 0, self.frame_controls.width(), self.frame_controls.height())
        else:
            # Si el frame está oculto, lo mostramos deslizándolo desde la izquierda
            self.frame_controls.setGeometry(0, 0, self.frame_controls.width(), self.frame_controls.height())
            self.frame_controls.setVisible(True) 
            
    def ordenar_por_nombre(self):
        if hasattr(self, 'productos_data') and self.productos_data:
            # Ordena de forma ascendente por nombre (índice 0)
            self.productos_data.sort(key=lambda p: p[0].lower())
            # Se actualiza la visualización, reiniciando a la primera página
            self.mostrar_pagina(1)

    def ordenar_por_categoria(self):
        if hasattr(self, 'productos_data') and self.productos_data:
            # Ordena de forma ascendente por categoría (índice 1)
            self.productos_data.sort(key=lambda p: p[1].lower())
            self.mostrar_pagina(1)

    def ordenar_por_nuevos(self):
        if hasattr(self, 'productos_data') and self.productos_data:
            # Ordena de forma descendente por la fecha de creación (índice 3)
            # Se asume que la fecha está en formato ISO: "YYYY-MM-DD HH:MM:SS", lo que permite ordenarla como string
            self.productos_data.sort(key=lambda p: p[3], reverse=True)
            self.mostrar_pagina(1)

    def ordenar_por_viejos(self):
        if hasattr(self, 'productos_data') and self.productos_data:
            # Ordena de forma ascendente por la fecha de creación (índice 3)
            self.productos_data.sort(key=lambda p: p[3])
            self.mostrar_pagina(1)
     
    def anadir_producto(self):
        """
        Abre la ventana para agregar un nuevo producto.
        Se pasa la ruta del CSV y una función para actualizar la tabla de productos.
        """
        ventana_anadir = VentanaAnadirProducto(self.csv_path, self.actualizar_tabla_productos)
        if ventana_anadir.exec_() == QtWidgets.QDialog.Accepted:
            self.actualizar_tabla_productos()

    def editar_producto(self):
        """
        Abre la ventana para editar el producto seleccionado.
        Verifica que se haya seleccionado un producto en la tabla.
        """
        row = self.table_prod.currentRow()
        if row < 0:
            QtWidgets.QMessageBox.warning(self, "Editar Producto", "Por favor, selecciona un producto para editar.")
            return

        # Extraer datos del producto seleccionado.
        producto = {
            "nombre": self.table_prod.item(row, 0).text(),
            "categoria": self.table_prod.item(row, 1).text(),
            "cantidad": self.table_prod.item(row, 2).text(),
            "fecha": self.table_prod.item(row, 3).text(),
            "precio": self.table_prod.item(row, 4).text(),
        }

        # Llamar a la ventana de edición pasando csv_path y actualizar_func
        ventana_editar = VentanaEditarProducto(self.csv_path, producto, self.actualizar_tabla_productos)
        if ventana_editar.exec_() == QtWidgets.QDialog.Accepted:
            self.actualizar_tabla_productos()


    def eliminar_producto(self):
        """
        Elimina el producto seleccionado después de confirmar la acción.
        Se actualiza la tabla de productos luego de eliminar.
        """
        row = self.table_prod.currentRow()
        if row < 0:
            QtWidgets.QMessageBox.warning(self, "Eliminar Producto", "Por favor, selecciona un producto para eliminar.")
            return

        reply = QtWidgets.QMessageBox.question(self, "Eliminar Producto",
                                                "¿Estás seguro de eliminar el producto?",
                                                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                                QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            # Aquí debes implementar la lógica para eliminar el producto del CSV.
            # Por ejemplo, puedes cargar todos los productos, eliminar el seleccionado y reescribir el CSV.
            productos = self.cargar_productos()
            if row < len(productos):
                producto_a_eliminar = productos[row]
                nuevos_productos = [p for p in productos if p != producto_a_eliminar]
                try:
                    with open(self.csv_path, mode="w", newline='', encoding="utf-8") as archivo:
                        escritor = csv.writer(archivo)
                        # Escribir encabezado
                        escritor.writerow(['Nombre', 'Cantidad', 'Precio', 'Categoria', 'Fecha de Creacion'])
                        escritor.writerows([
                            [p[0], p[2], p[4], p[1], p[3]] for p in nuevos_productos
                        ])
                except Exception as e:
                    QtWidgets.QMessageBox.critical(self, "Error", f"No se pudo eliminar el producto: {e}")
                self.actualizar_tabla_productos()
            
        
    def mostrar_datos_productos(self):
        """
        Carga los datos desde el archivo CSV de productos y los muestra en la tabla.
        """
        try:
            with open(self.csv_path, newline='', encoding="utf-8") as archivo:
                lector_csv = csv.reader(archivo)
                datos = list(lector_csv)

            if not datos:
                return  # No hay datos en el CSV

            encabezados = datos[0]  # Primera fila como encabezados
            productos = datos[1:]  # Filas de productos

            # Configurar encabezados de la tabla
            

            # Insertar productos en la tabla
            self.table_prod.setRowCount(len(productos))
            for fila_idx, fila in enumerate(productos):
                for col_idx, valor in enumerate(fila):
                    self.table_prod.setItem(fila_idx, col_idx, QtWidgets.QTableWidgetItem(valor))

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"No se pudo cargar el archivo de productos: {e}")

        
    def cargar_productos(self):
        """
        Lee el archivo CSV y retorna una lista de productos.
        Cada producto es una lista con el siguiente orden:
        [Nombre, Categoria, Cantidad, Fecha de Creacion, Precio]
        """
        productos = []
        try:
            with open(self.csv_path, mode="r", newline='', encoding="utf-8") as archivo:
                lector = csv.reader(archivo)
                filas = list(lector)
                # Si existe el encabezado, lo omite.
                if filas and filas[0] == []:
                    filas = filas[1:]
                for row in filas:
                    if len(row) < 5:
                        continue  # omite filas incompletas
                    # Reordenar los datos para mostrarlos como: [Nombre, Categoria, Cantidad, Fecha, Precio]
                    productos.append([row[0], row[3], row[1], row[4], row[2]])
        except Exception as e:
            print("Error al cargar productos:", e)
        return productos

    def actualizar_tabla_productos(self):
        """
        Carga los productos del CSV, calcula la cantidad total de páginas
        y muestra la primera página en la tabla.
        """
        self.productos_data = self.cargar_productos()
        total_productos = len(self.productos_data)
        self.total_pages = math.ceil(total_productos / 12) if total_productos > 0 else 1
        self.current_page = 1
        self.mostrar_pagina(self.current_page)

    def mostrar_pagina(self, page):
        """
        Muestra en la tabla los productos correspondientes a la página 'page'.
        Actualiza también el label 'conteo' para mostrar la página actual y el total.
        """
        if page < 1 or page > self.total_pages:
            return  # Si la página es inválida, no hace nada.
        self.current_page = page
        inicio = (page - 1) * 12
        fin = inicio + 12
        datos = self.productos_data[inicio:fin]
        
        # Limpiar la tabla
        self.table_prod.setRowCount(0) 
        
        # Insertar los productos en la tabla
        for row_number, row_data in enumerate(datos):
            self.table_prod.insertRow(row_number)
            for column_number, dato in enumerate(row_data):
                self.table_prod.setItem(row_number, column_number, QtWidgets.QTableWidgetItem(str(dato)))
        
        # Actualizar el label de paginación (ej: "Página 1 de 3")
        self.conteo.setText(f"Página {self.current_page} de {self.total_pages}")

    # Métodos de paginación para los botones
    def primera_pag(self):
        self.mostrar_pagina(1)
    
    def pagina_anterior(self):
        self.mostrar_pagina(max(1, self.current_page - 1))
    
    def siguiente_pag(self):
        self.mostrar_pagina(min(self.total_pages, self.current_page + 1))
    
    def ultima_pag(self):
        self.mostrar_pagina(self.total_pages)      

    def mostrar_datos_usuarios(self):
        """
        Carga los datos desde el archivo CSV de usuarios y los muestra en la tabla.
        """
        try:
            with open(self.csv_user, newline='', encoding="utf-8") as archivo:
                lector_csv = csv.reader(archivo)
                datos = list(lector_csv)

            if not datos:
                return  # No hay datos en el CSV
            usuarios = datos[1:]  # Filas de usuarios

            self.user_table.setRowCount(len(usuarios))
            

            for fila_idx, fila in enumerate(usuarios):
                for col_idx, valor in enumerate(fila):
                    self.user_table.setItem(fila_idx, col_idx, QtWidgets.QTableWidgetItem(valor))

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"No se pudo cargar el archivo de usuarios: {e}")

    def cargar_usuarios(self):
        """
        Lee el archivo CSV de usuarios y retorna una lista de usuarios.
        Cada usuario es una lista con el orden: [Nombre, Email, Telefono, Direccion].
        """
        usuarios = []
        try:
            with open(self.csv_user, mode="r", newline='', encoding="utf-8") as archivo:
                lector = csv.reader(archivo)
                filas = list(lector)
                # Omitir encabezado si existe
                if filas and filas[0] == ['Nombre', 'Email', 'Telefono', 'Direccion']:
                    filas = filas[1:]
                for row in filas:
                    if len(row) < 4:
                        continue  # omitir filas incompletas
                    usuarios.append(row)
        except Exception as e:
            print("Error al cargar usuarios:", e)
        return usuarios

    def actualizar_tabla_usuarios(self):
        """
        Carga los usuarios del CSV, calcula la cantidad total de páginas
        y muestra la primera página en la tabla de usuarios.
        """
        self.usuarios_data = self.cargar_usuarios()
        total_usuarios = len(self.usuarios_data)
        self.total_pages_users = math.ceil(total_usuarios / 12) if total_usuarios > 0 else 1
        self.current_page_users = 1
        self.mostrar_pagina_usuarios(self.current_page_users)

    def mostrar_pagina_usuarios(self, page):
        """
        Muestra en la tabla de usuarios los datos correspondientes a la página 'page'.
        Actualiza también el label 'conteo_2' para mostrar la página actual y el total.
        """
        if page < 1 or page > self.total_pages_users:
            return
        self.current_page_users = page
        inicio = (page - 1) * 12
        fin = inicio + 12
        datos = self.usuarios_data[inicio:fin]
        
        self.user_table.setRowCount(0)
        for row_number, row_data in enumerate(datos):
            self.user_table.insertRow(row_number)
            for column_number, dato in enumerate(row_data):
                self.user_table.setItem(row_number, column_number, QtWidgets.QTableWidgetItem(str(dato)))
        
        # Actualizar el label de paginación para usuarios
        self.conteo_2.setText(f"Página {self.current_page_users} de {self.total_pages_users}")

    # Métodos de paginación específicos para usuarios

    def primera_pag_usuarios(self):
        self.mostrar_pagina_usuarios(1)

    def pagina_anterior_usuarios(self):
        self.mostrar_pagina_usuarios(max(1, self.current_page_users - 1))

    def siguiente_pag_usuarios(self):
        self.mostrar_pagina_usuarios(min(self.total_pages_users, self.current_page_users + 1))

    def ultima_pag_usuarios(self):
        self.mostrar_pagina_usuarios(self.total_pages_users)

    # Funciones para gestionar los usuarios (ejemplos)

    def abrir_registro(self):
        """
        Abre la ventana de registro para agregar un nuevo usuario.
        Al cerrar el diálogo con éxito, se actualiza la tabla de usuarios.
        """
        # Se asume que tienes una clase RegistroUsuario para el registro de usuarios.
        ventana_registro = Registro(self.csv_user)  # Implementa RegistroUsuario según necesites
        if ventana_registro.exec_() == QtWidgets.QDialog.Accepted:
            self.actualizar_tabla_usuarios()

    def abrir_editar_usuario(self):
        """Abre la ventana de edición para modificar el usuario seleccionado."""
        row = self.table_user.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Editar Usuario", "Selecciona un usuario para editar.")
            return

        # Extraer datos del usuario seleccionado
        usuario = {
            "nombre": self.table_user.item(row, 0).text(),
            "email": self.table_user.item(row, 1).text(),
            "telefono": self.table_user.item(row, 2).text(),
            "direccion": self.table_user.item(row, 3).text(),
            "password": self.table_user.item(row, 4).text(),
        }

        # Abrir ventana de edición
        ventana_editar = VentanaEditarUsuario(self.csv_user, usuario)
        if ventana_editar.exec_() == QtWidgets.QDialog.Accepted:
            self.actualizar_tabla_usuarios()


    def eliminar_usuario(self):
        """
        Elimina el usuario seleccionado tras confirmar la acción.
        """
        row = self.user_table.currentRow()
        if row < 0:
            QtWidgets.QMessageBox.warning(self, "Eliminar Usuario", "Selecciona un usuario para eliminar.")
            return

        reply = QtWidgets.QMessageBox.question(self, "Eliminar Usuario",
                                                "¿Estás seguro de eliminar este usuario?",
                                                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                                QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            # Leer todos los usuarios, eliminar el seleccionado y reescribir el CSV.
            usuarios = self.cargar_usuarios()
            if row < len(usuarios):
                usuario_a_eliminar = usuarios[row]
                nuevos_usuarios = [u for u in usuarios if u != usuario_a_eliminar]
                try:
                    with open(self.csv_user, mode="w", newline='', encoding="utf-8") as archivo:
                        escritor = csv.writer(archivo)
                        # Escribir encabezado
                        escritor.writerow(['Nombre', 'Email', 'Telefono', 'Direccion'])
                        escritor.writerows(nuevos_usuarios)
                except Exception as e:
                    QtWidgets.QMessageBox.critical(self, "Error", f"No se pudo eliminar el usuario: {e}")
                self.actualizar_tabla_usuarios()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Definir las rutas absolutas para los CSV, según la estructura del proyecto:
    base_path = os.path.dirname(__file__)
    csv_path = os.path.join(base_path, "recursos", "bd", "productos.csv")
    csv_user = os.path.join(base_path, "recursos", "bd", "usuarios.csv")
    origen = "some_value"
    # Crear la instancia de VentanaPrincipal pasando ambas rutas:
    ventana_principal = VentanaPrincipal(csv_path, csv_user)
    ventana_registro = Registro(csv_user, origen)
    ventana_ingreso = Login(csv_user)
    ventana_ingreso.show()
    
    sys.exit(app.exec_())