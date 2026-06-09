## =============================================================================
#  AgriCactus - App del APUNTADOR  (main.py)
#  v1.0 - Recibe listas de cuadrilleros + exporta Excel
# =============================================================================

import datetime
import json
import os
import socket
import threading

from kivy.lang import Builder
from kivy.clock import Clock
from kivy.properties import StringProperty, ListProperty
from kivy.uix.screenmanager import Screen, FadeTransition
from kivy.utils import platform
from kivymd.app import MDApp
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.list import TwoLineIconListItem, IconLeftWidget, OneLineListItem

# =============================================================================
#  CONSTANTES
# =============================================================================
ARCHIVO_LISTAS     = "apuntador_listas.json"
PUERTO_ANUNCIO_CU  = 45682   # Escucha anuncios de cuadrilleros
PUERTO_CUADRILLERO = 45680   # Pide lista al cuadrillero
PUERTO_RECEPCION   = 45681   # Recibe lista del cuadrillero


def guardar_listas(listas: list):
    try:
        with open(ARCHIVO_LISTAS, 'w', encoding='utf-8') as f:
            json.dump(listas, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[STORAGE] Error: {e}")


def cargar_listas() -> list:
    if os.path.exists(ARCHIVO_LISTAS):
        try:
            with open(ARCHIVO_LISTAS, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return []


def exportar_excel(listas: list) -> str:
    """
    Genera un archivo CSV compatible con Excel.
    Retorna la ruta del archivo generado.
    """
    try:
        fecha_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_archivo = f"asistencia_{fecha_str}.csv"

        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                files_dir = PythonActivity.mActivity.getExternalFilesDir(None).getAbsolutePath()
            except Exception:
                files_dir = os.path.expanduser("~")
        else:
            files_dir = os.path.expanduser("~")

        ruta = os.path.join(files_dir, nombre_archivo)

        with open(ruta, 'w', encoding='utf-8-sig') as f:
            # Encabezado
            f.write("FECHA,CUADRILLA,CUADRILLERO,CUADRO,ACTIVIDAD,"
                    "CREDENCIAL,NOMBRE,HORA_DETECCION,HORA_VALIDACION,"
                    "ESTATUS,GPS\n")

            for lista in listas:
                fecha      = lista.get("fecha", "")
                cuadrilla  = lista.get("cuadrilla", "")
                cuadrillero = lista.get("cuadrillero", "").replace('\n', ' ')
                cuadro     = lista.get("cuadro", "")
                actividad  = lista.get("actividad", "")
                trabajadores = lista.get("trabajadores", {})

                for cred, info in trabajadores.items():
                    nombre   = info.get("nombre", "").replace('\n', ' ')
                    hora_det = info.get("hora_deteccion", "")
                    hora_val = info.get("hora_validacion", "")
                    estatus  = "PRESENTE" if info.get("validado") else "AUSENTE"
                    gps      = info.get("gps", "")
                    f.write(
                        f"{fecha},{cuadrilla},{cuadrillero},{cuadro},"
                        f"{actividad},{cred},{nombre},{hora_det},"
                        f"{hora_val},{estatus},{gps}\n"
                    )

        return ruta
    except Exception as e:
        print(f"[EXCEL] Error: {e}")
        return ""


KV = '''
#:import FadeTransition kivy.uix.screenmanager.FadeTransition

ScreenManager:
    transition: FadeTransition()
    PantallaInicio:
    PantallaDetalle:


<PantallaInicio>:
    name: 'inicio'

    MDFloatLayout:
        md_bg_color: 0.96, 0.96, 0.94, 1

        MDFloatLayout:
            size_hint_y: 0.13
            pos_hint: {'x': 0, 'top': 1}
            md_bg_color: 0.18, 0.29, 0.12, 1

            Image:
                source: "logo_agricactus.png"
                size_hint: (0.28, 0.80)
                allow_stretch: True
                keep_ratio: True
                pos_hint: {'center_x': 0.16, 'center_y': 0.5}

            MDLabel:
                text: "APUNTADOR"
                font_style: "H6"
                bold: True
                halign: "center"
                theme_text_color: "Custom"
                text_color: 0.96, 0.65, 0.14, 1
                pos_hint: {'center_x': 0.62, 'center_y': 0.60}
                size_hint: (0.66, 0.4)

            MDLabel:
                text: root.fecha_hoy
                font_style: "Caption"
                halign: "center"
                theme_text_color: "Custom"
                text_color: 0.8, 0.9, 0.8, 1
                pos_hint: {'center_x': 0.62, 'center_y': 0.28}
                size_hint: (0.66, 0.3)

        MDBoxLayout:
            size_hint_y: 0.005
            pos_hint: {'x': 0, 'top': 0.87}
            md_bg_color: 0.96, 0.65, 0.14, 1

        MDCard:
            size_hint: (0.96, 0.10)
            pos_hint: {'center_x': 0.5, 'top': 0.86}
            elevation: 2
            radius: [8, 8, 8, 8]
            md_bg_color: 1, 1, 1, 1

            MDBoxLayout:
                orientation: 'horizontal'
                padding: '8dp'
                spacing: '4dp'

                MDBoxLayout:
                    orientation: 'vertical'
                    MDLabel:
                        text: root.total_cuadrilleros
                        font_style: "H5"
                        bold: True
                        halign: "center"
                        theme_text_color: "Custom"
                        text_color: 0.18, 0.29, 0.12, 1
                    MDLabel:
                        text: "Cuadrilleros"
                        font_style: "Caption"
                        halign: "center"
                        theme_text_color: "Secondary"

                MDBoxLayout:
                    orientation: 'vertical'
                    MDLabel:
                        text: root.total_trabajadores
                        font_style: "H5"
                        bold: True
                        halign: "center"
                        theme_text_color: "Custom"
                        text_color: 0.96, 0.65, 0.14, 1
                    MDLabel:
                        text: "Trabajadores"
                        font_style: "Caption"
                        halign: "center"
                        theme_text_color: "Secondary"

                MDBoxLayout:
                    orientation: 'vertical'
                    MDLabel:
                        text: root.estado_escucha
                        font_style: "Caption"
                        bold: True
                        halign: "center"
                        theme_text_color: "Custom"
                        text_color: root.color_estado
                    MDLabel:
                        text: "Estado"
                        font_style: "Caption"
                        halign: "center"
                        theme_text_color: "Secondary"

        MDCard:
            size_hint: (0.96, 0.52)
            pos_hint: {'center_x': 0.5, 'top': 0.75}
            elevation: 2
            radius: [8, 8, 8, 8]
            md_bg_color: 1, 1, 1, 1

            MDBoxLayout:
                orientation: 'vertical'
                padding: '4dp'

                MDLabel:
                    text: "Cuadrilleros detectados"
                    font_style: "Caption"
                    bold: True
                    halign: "center"
                    theme_text_color: "Custom"
                    text_color: 0.18, 0.29, 0.12, 1
                    size_hint_y: None
                    height: '28dp'

                ScrollView:
                    MDList:
                        id: lista_cuadrilleros

        MDBoxLayout:
            orientation: 'horizontal'
            size_hint: (0.96, 0.08)
            pos_hint: {'center_x': 0.5, 'y': 0.10}
            spacing: '8dp'

            MDRaisedButton:
                text: "PEDIR TODAS LAS LISTAS"
                md_bg_color: 0.18, 0.29, 0.12, 1
                size_hint_x: 1.0
                elevation: 3
                on_release: root.pedir_todas_listas()

        MDBoxLayout:
            orientation: 'horizontal'
            size_hint: (0.96, 0.08)
            pos_hint: {'center_x': 0.5, 'y': 0.01}
            spacing: '8dp'

            MDRaisedButton:
                text: "EXPORTAR EXCEL"
                md_bg_color: 0.29, 0.40, 0.25, 1
                size_hint_x: 0.5
                elevation: 3
                on_release: root.exportar()

            MDRaisedButton:
                text: "LIMPIAR DIA"
                md_bg_color: 0.96, 0.65, 0.14, 1
                text_color: 0.18, 0.29, 0.12, 1
                size_hint_x: 0.5
                elevation: 3
                on_release: root.limpiar_dia()


<PantallaDetalle>:
    name: 'detalle'

    MDFloatLayout:
        md_bg_color: 0.96, 0.96, 0.94, 1

        MDFloatLayout:
            size_hint_y: 0.13
            pos_hint: {'x': 0, 'top': 1}
            md_bg_color: 0.18, 0.29, 0.12, 1

            MDLabel:
                text: root.titulo_detalle
                font_style: "H6"
                bold: True
                halign: "center"
                theme_text_color: "Custom"
                text_color: 0.96, 0.65, 0.14, 1
                pos_hint: {'center_x': 0.5, 'center_y': 0.60}
                size_hint: (1, 0.5)

            MDLabel:
                text: root.subtitulo_detalle
                font_style: "Caption"
                halign: "center"
                theme_text_color: "Custom"
                text_color: 0.8, 0.9, 0.8, 1
                pos_hint: {'center_x': 0.5, 'center_y': 0.25}
                size_hint: (1, 0.3)

        MDBoxLayout:
            size_hint_y: 0.005
            pos_hint: {'x': 0, 'top': 0.87}
            md_bg_color: 0.96, 0.65, 0.14, 1

        MDCard:
            size_hint: (0.96, 0.75)
            pos_hint: {'center_x': 0.5, 'top': 0.85}
            elevation: 2
            radius: [8, 8, 8, 8]
            md_bg_color: 1, 1, 1, 1

            MDBoxLayout:
                orientation: 'vertical'
                padding: '4dp'

                MDLabel:
                    text: root.info_lista
                    font_style: "Caption"
                    halign: "center"
                    theme_text_color: "Custom"
                    text_color: 0.18, 0.29, 0.12, 1
                    size_hint_y: None
                    height: '52dp'

                ScrollView:
                    MDList:
                        id: lista_detalle

        MDRectangleFlatButton:
            text: "REGRESAR"
            theme_text_color: "Custom"
            text_color: 0.18, 0.29, 0.12, 1
            line_color: 0.18, 0.29, 0.12, 1
            size_hint: (0.96, 0.07)
            pos_hint: {'center_x': 0.5, 'y': 0.01}
            on_release: app.root.current = 'inicio'
'''


class PantallaInicio(Screen):
    fecha_hoy          = StringProperty("")
    total_cuadrilleros = StringProperty("0")
    total_trabajadores = StringProperty("0")
    estado_escucha     = StringProperty("Iniciando...")
    color_estado       = ListProperty([0.96, 0.65, 0.14, 1])

    def on_enter(self):
        self.fecha_hoy = datetime.datetime.now().strftime("%d/%m/%Y  %H:%M")

    def actualizar_ui(self, cuadrilleros: dict, listas: list):
        self.ids.lista_cuadrilleros.clear_widgets()
        total_t = 0

        for cuadrilla, info in cuadrilleros.items():
            nombre  = info.get('nombre', f"Cuadrilla {cuadrilla}")
            hora    = info.get('hora_deteccion', '--:--')
            n_trab  = info.get('num_trabajadores', 0)
            total_t += n_trab

            item = TwoLineIconListItem(
                text=f"[b]Cuadrilla {cuadrilla}[/b]  —  {nombre.replace(chr(10), ' ')}",
                secondary_text=f"Detectado: {hora}  |  {n_trab} trabajadores",
                on_release=lambda x, c=cuadrilla: self._ver_detalle(c)
            )
            icono = IconLeftWidget(
                icon="account-group",
                theme_text_color="Custom",
                icon_color=(0.18, 0.29, 0.12, 1)
            )
            item.add_widget(icono)
            self.ids.lista_cuadrilleros.add_widget(item)

        self.total_cuadrilleros = str(len(cuadrilleros))
        self.total_trabajadores = str(total_t)

    def _ver_detalle(self, cuadrilla):
        app = MDApp.get_running_app()
        lista = app.listas_recibidas.get(cuadrilla)
        if not lista:
            Snackbar(text="Lista no recibida aun. Presiona PEDIR TODAS LAS LISTAS").open()
            return
        pd = app.root.get_screen('detalle')
        pd.cargar_detalle(cuadrilla, lista)
        app.root.current = 'detalle'

    def pedir_todas_listas(self):
        app = MDApp.get_running_app()
        count = 0
        for cuadrilla, info in app.cuadrilleros_detectados.items():
            ip = info.get('ip')
            if ip:
                app.pedir_lista_cuadrillero(ip, cuadrilla)
                count += 1
        if count == 0:
            Snackbar(text="No hay cuadrilleros detectados aun").open()
        else:
            Snackbar(text=f"Pidiendo lista a {count} cuadrillero(s)...").open()

    def exportar(self):
        app = MDApp.get_running_app()
        if not app.listas_recibidas:
            Snackbar(text="No hay listas para exportar").open()
            return
        listas = list(app.listas_recibidas.values())
        ruta   = exportar_excel(listas)
        if ruta:
            guardar_listas(listas)
            Snackbar(text=f"Exportado: {os.path.basename(ruta)}").open()
        else:
            Snackbar(text="Error al exportar").open()

    def limpiar_dia(self):
        app = MDApp.get_running_app()
        app.cuadrilleros_detectados = {}
        app.listas_recibidas        = {}
        self.ids.lista_cuadrilleros.clear_widgets()
        self.total_cuadrilleros = "0"
        self.total_trabajadores = "0"
        Snackbar(text="Datos del dia limpiados").open()


class PantallaDetalle(Screen):
    titulo_detalle    = StringProperty("")
    subtitulo_detalle = StringProperty("")
    info_lista        = StringProperty("")

    def cargar_detalle(self, cuadrilla, lista):
        self.titulo_detalle    = f"Cuadrilla {cuadrilla}"
        nombre_cuad = lista.get('cuadrillero', '').replace('\n', ' ')
        self.subtitulo_detalle = nombre_cuad
        cuadro    = lista.get('cuadro', '')
        actividad = lista.get('actividad', '')
        fecha     = lista.get('fecha', '')
        trabajadores = lista.get('trabajadores', {})
        presentes = sum(1 for v in trabajadores.values() if v.get('validado'))
        total     = len(trabajadores)
        self.info_lista = (
            f"Cuadro: {cuadro}  |  {fecha}\n"
            f"Actividad: {actividad}\n"
            f"Presentes: {presentes} / {total}"
        )
        self.ids.lista_detalle.clear_widgets()
        for cred, info in trabajadores.items():
            validado = info.get('validado', False)
            nombre   = info.get('nombre', '').replace('\n', ' ')
            hora     = info.get('hora_deteccion', '--')
            gps      = info.get('gps', '')
            icono = IconLeftWidget(
                icon="check" if validado else "close",
                theme_text_color="Custom",
                icon_color=(0.18, 0.29, 0.12, 1) if validado else (0.72, 0.10, 0.10, 1)
            )
            item = TwoLineIconListItem(
                text=f"Cred. {cred}  —  {nombre}",
                secondary_text=(
                    f"{hora}  |  {'PRESENTE' if validado else 'AUSENTE'}"
                    + (f"  |  {gps}" if gps else "")
                ),
            )
            item.add_widget(icono)
            self.ids.lista_detalle.add_widget(item)


class ApuntadorAgriCactusApp(MDApp):
    cuadrilleros_detectados = {}
    listas_recibidas        = {}
    _escucha_activa         = False
    _recepcion_activa       = False

    def build(self):
        self.theme_cls.theme_style     = "Light"
        self.theme_cls.primary_palette = "Green"
        controlador = Builder.load_string(KV)
        Clock.schedule_once(self._iniciar_servicios, 1.0)
        return controlador

    def _iniciar_servicios(self, dt):
        self.iniciar_escucha_cuadrilleros()
        self.iniciar_recepcion_listas()
        listas_guardadas = cargar_listas()
        for lista in listas_guardadas:
            cuadrilla = lista.get('cuadrilla', '')
            if cuadrilla:
                self.listas_recibidas[cuadrilla] = lista
        pi = self.root.get_screen('inicio')
        pi.estado_escucha = "Activo"
        pi.color_estado   = [0.18, 0.29, 0.12, 1]

    # ── Escuchar anuncios de cuadrilleros ─────────────────────────────────────
    def iniciar_escucha_cuadrilleros(self):
        if self._escucha_activa:
            return
        self._escucha_activa = True

        def _escuchar():
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                    sock.bind(('', PUERTO_ANUNCIO_CU))
                    sock.settimeout(2.0)
                    print(f"[WIFI] Escuchando cuadrilleros en puerto {PUERTO_ANUNCIO_CU}")

                    while self._escucha_activa:
                        try:
                            datos_raw, addr = sock.recvfrom(1024)
                            mensaje = datos_raw.decode('utf-8').strip()
                            partes  = mensaje.split(':')

                            # Formato: CUADRILLERO:<cuadrilla>:<nombre>
                            if len(partes) >= 3 and partes[0] == 'CUADRILLERO':
                                cuadrilla = partes[1]
                                nombre    = ':'.join(partes[2:])
                                ahora     = datetime.datetime.now().strftime("%H:%M:%S")
                                ip        = addr[0]

                                ya_existe = cuadrilla in self.cuadrilleros_detectados
                                self.cuadrilleros_detectados[cuadrilla] = {
                                    "nombre":          nombre,
                                    "hora_deteccion":  ahora,
                                    "ip":              ip,
                                    "num_trabajadores": self.listas_recibidas.get(
                                        cuadrilla, {}
                                    ).get('trabajadores', {}).__len__()
                                }
                                if not ya_existe:
                                    Clock.schedule_once(lambda dt: self._actualizar_ui(), 0)

                        except socket.timeout:
                            continue
                        except Exception as e:
                            print(f"[WIFI] Error escucha cuadrillero: {e}")

            except Exception as e:
                print(f"[WIFI] Error servidor cuadrilleros: {e}")
            finally:
                self._escucha_activa = False

        threading.Thread(target=_escuchar, daemon=True).start()

    # ── Recibir listas de cuadrilleros ────────────────────────────────────────
    def iniciar_recepcion_listas(self):
        if self._recepcion_activa:
            return
        self._recepcion_activa = True

        def _escuchar():
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    sock.bind(('', PUERTO_RECEPCION))
                    sock.settimeout(2.0)
                    print(f"[WIFI] Recibiendo listas en puerto {PUERTO_RECEPCION}")

                    while self._recepcion_activa:
                        try:
                            datos_raw, addr = sock.recvfrom(65535)
                            mensaje = datos_raw.decode('utf-8').strip()
                            payload = json.loads(mensaje)

                            if payload.get('tipo') == 'LISTA_CUADRILLA':
                                cuadrilla = payload.get('cuadrilla', '')
                                self.listas_recibidas[cuadrilla] = payload
                                n_trab = len(payload.get('trabajadores', {}))
                                if cuadrilla in self.cuadrilleros_detectados:
                                    self.cuadrilleros_detectados[cuadrilla]['num_trabajadores'] = n_trab
                                Clock.schedule_once(lambda dt: self._actualizar_ui(), 0)
                                print(f"[WIFI] Lista recibida cuadrilla {cuadrilla}: {n_trab} trabajadores")

                        except socket.timeout:
                            continue
                        except json.JSONDecodeError:
                            continue
                        except Exception as e:
                            print(f"[WIFI] Error recepcion lista: {e}")

            except Exception as e:
                print(f"[WIFI] Error servidor listas: {e}")
            finally:
                self._recepcion_activa = False

        threading.Thread(target=_escuchar, daemon=True).start()

    def pedir_lista_cuadrillero(self, ip: str, cuadrilla: str):
        mensaje = f"PEDIR_LISTA:{cuadrilla}"

        def _pedir():
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                    sock.settimeout(5.0)
                    sock.sendto(mensaje.encode('utf-8'), (ip, PUERTO_CUADRILLERO))
                    print(f"[WIFI] Lista pedida a cuadrilla {cuadrilla} ({ip})")
            except Exception as e:
                print(f"[WIFI] Error pidiendo lista: {e}")

        threading.Thread(target=_pedir, daemon=True).start()

    def _actualizar_ui(self):
        pi = self.root.get_screen('inicio')
        if self.root.current in ('inicio',):
            pi.actualizar_ui(self.cuadrilleros_detectados, list(self.listas_recibidas.values()))

    def on_stop(self):
        self._escucha_activa   = False
        self._recepcion_activa = False


if __name__ == '__main__':
    ApuntadorAgriCactusApp().run()
