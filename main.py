# =============================================================================
#  AgriCactus - App del APUNTADOR  (main.py)
#  v2.0 - Soporte periodos completos + reportes de avance
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
from kivymd.uix.list import TwoLineIconListItem, IconLeftWidget, ThreeLineIconListItem

# =============================================================================
#  CONSTANTES
# =============================================================================
ARCHIVO_LISTAS     = "apuntador_listas.json"
PUERTO_ANUNCIO_CU  = 45682
PUERTO_CUADRILLERO = 45680
PUERTO_RECEPCION   = 45681


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


def exportar_csv(listas: list, tipo: str = "avance") -> str:
    try:
        fecha_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre    = f"agricactus_{tipo}_{fecha_str}.csv"

        if platform == 'android':
            try:
                from jnius import autoclass
                PA        = autoclass('org.kivy.android.PythonActivity')
                files_dir = PA.mActivity.getExternalFilesDir(None).getAbsolutePath()
            except Exception:
                files_dir = os.path.expanduser("~")
        else:
            files_dir = os.path.expanduser("~")

        ruta = os.path.join(files_dir, nombre)

        with open(ruta, 'w', encoding='utf-8-sig') as f:
            # Encabezado
            f.write(
                "FECHA,CUADRILLA,CUADRILLERO,TIPO_REPORTE,"
                "CREDENCIAL,NOMBRE,GPS,"
                "HORA_ENTRADA,CUADRO_ENTRADA,ACTIVIDAD_ENTRADA,"
                "HORA_SALIDA_COMIDA,"
                "HORA_REGRESO_COMIDA,"
                "CAMBIOS_CUADRO,"
                "HORA_SALIDA_FINAL,"
                "TOTAL_PERIODOS,PRESENTE\n"
            )

            for lista in listas:
                fecha       = lista.get("fecha", "")
                cuadrilla   = lista.get("cuadrilla", "")
                cuadrillero = lista.get("cuadrillero", "").replace('\n', ' ')
                tipo_rep    = lista.get("tipo_reporte", "AVANCE")
                trabajadores = lista.get("trabajadores", {})

                for cred, info in trabajadores.items():
                    nombre_t  = info.get("nombre", "").replace('\n', ' ')
                    gps       = info.get("gps", "")
                    presente  = "SI" if info.get("validado") else "NO"
                    periodos  = info.get("periodos", [])

                    # Extraer periodos por tipo
                    def get_periodo(tipo_p):
                        for p in periodos:
                            if p.get("tipo") == tipo_p:
                                return p
                        return {}

                    entrada      = get_periodo("entrada")
                    sal_comida   = get_periodo("salida_comida")
                    reg_comida   = get_periodo("regreso_comida")
                    sal_final    = get_periodo("salida_final")

                    # Cambios de cuadro
                    cambios = [p for p in periodos if p.get("tipo") == "cambio_cuadro"]
                    cambios_txt = "|".join([
                        f"{c.get('hora','')} {c.get('cuadro','')} {c.get('actividad','')[:10]}"
                        for c in cambios
                    ]) or ""

                    f.write(
                        f"{fecha},{cuadrilla},{cuadrillero},{tipo_rep},"
                        f"{cred},{nombre_t},{gps},"
                        f"{entrada.get('hora','')},"
                        f"{entrada.get('cuadro','')},"
                        f"{entrada.get('actividad','')[:20]},"
                        f"{sal_comida.get('hora','')},"
                        f"{reg_comida.get('hora','')},"
                        f"{cambios_txt},"
                        f"{sal_final.get('hora','')},"
                        f"{len(periodos)},{presente}\n"
                    )

        return ruta
    except Exception as e:
        print(f"[CSV] Error: {e}")
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
        md_bg_color: 0.94, 0.96, 0.94, 1

        # Encabezado
        MDFloatLayout:
            size_hint_y: 0.13
            pos_hint: {'x': 0, 'top': 1}
            md_bg_color: 0.18, 0.29, 0.12, 1

            Image:
                source: "logo_agricactus.png"
                size_hint: (0.26, 0.76)
                allow_stretch: True
                keep_ratio: True
                pos_hint: {'center_x': 0.14, 'center_y': 0.5}

            MDLabel:
                text: "APUNTADOR"
                font_style: "H6"
                bold: True
                halign: "center"
                theme_text_color: "Custom"
                text_color: 0.96, 0.65, 0.14, 1
                pos_hint: {'center_x': 0.60, 'center_y': 0.62}
                size_hint: (0.68, 0.38)

            MDLabel:
                text: root.fecha_hoy
                font_style: "Caption"
                halign: "center"
                theme_text_color: "Custom"
                text_color: 0.78, 0.92, 0.78, 1
                pos_hint: {'center_x': 0.60, 'center_y': 0.26}
                size_hint: (0.68, 0.28)

        MDBoxLayout:
            size_hint_y: 0.004
            pos_hint: {'x': 0, 'top': 0.87}
            md_bg_color: 0.96, 0.65, 0.14, 1

        # Estadisticas
        MDCard:
            size_hint: (0.96, 0.10)
            pos_hint: {'center_x': 0.5, 'top': 0.865}
            elevation: 2
            radius: [10, 10, 10, 10]
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
                        text_color: 0.18, 0.42, 0.18, 1
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

        # Lista cuadrilleros
        MDCard:
            size_hint: (0.96, 0.53)
            pos_hint: {'center_x': 0.5, 'top': 0.76}
            elevation: 2
            radius: [10, 10, 10, 10]
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
                    height: '26dp'

                ScrollView:
                    MDList:
                        id: lista_cuadrilleros

        # Botones principales
        MDBoxLayout:
            orientation: 'horizontal'
            size_hint: (0.96, 0.08)
            pos_hint: {'center_x': 0.5, 'y': 0.11}
            spacing: '6dp'

            MDRaisedButton:
                text: "PEDIR AVANCE"
                md_bg_color: 0.18, 0.29, 0.12, 1
                size_hint_x: 0.5
                elevation: 3
                on_release: root.pedir_todas_listas()

            MDRaisedButton:
                text: "EXPORTAR CSV"
                md_bg_color: 0.18, 0.29, 0.55, 1
                size_hint_x: 0.5
                elevation: 3
                on_release: root.exportar()

        MDBoxLayout:
            orientation: 'horizontal'
            size_hint: (0.96, 0.08)
            pos_hint: {'center_x': 0.5, 'y': 0.02}
            spacing: '6dp'

            MDRaisedButton:
                text: "EXPORTAR FINAL"
                md_bg_color: 0.29, 0.40, 0.25, 1
                size_hint_x: 0.5
                elevation: 3
                on_release: root.exportar_final()

            MDRaisedButton:
                text: "LIMPIAR DIA"
                md_bg_color: 0.96, 0.65, 0.14, 1
                text_color: 0.12, 0.22, 0.08, 1
                size_hint_x: 0.5
                elevation: 3
                on_release: root.limpiar_dia()


<PantallaDetalle>:
    name: 'detalle'

    MDFloatLayout:
        md_bg_color: 0.94, 0.96, 0.94, 1

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
                pos_hint: {'center_x': 0.5, 'center_y': 0.62}
                size_hint: (1, 0.5)

            MDLabel:
                text: root.subtitulo_detalle
                font_style: "Caption"
                halign: "center"
                theme_text_color: "Custom"
                text_color: 0.78, 0.92, 0.78, 1
                pos_hint: {'center_x': 0.5, 'center_y': 0.26}
                size_hint: (1, 0.3)

        MDBoxLayout:
            size_hint_y: 0.004
            pos_hint: {'x': 0, 'top': 0.87}
            md_bg_color: 0.96, 0.65, 0.14, 1

        MDCard:
            size_hint: (0.96, 0.76)
            pos_hint: {'center_x': 0.5, 'top': 0.865}
            elevation: 2
            radius: [10, 10, 10, 10]
            md_bg_color: 1, 1, 1, 1

            MDBoxLayout:
                orientation: 'vertical'
                padding: '4dp'

                MDLabel:
                    text: root.info_lista
                    font_style: "Caption"
                    halign: "center"
                    theme_text_color: "Custom"
                    text_color: 0.12, 0.22, 0.08, 1
                    size_hint_y: None
                    height: '60dp'

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

    def actualizar_ui(self, cuadrilleros: dict):
        self.ids.lista_cuadrilleros.clear_widgets()
        total_t = 0

        for cuadrilla, info in cuadrilleros.items():
            nombre     = info.get('nombre', f"Cuadrilla {cuadrilla}").replace('\n', ' ')
            hora       = info.get('hora_deteccion', '--:--')
            n_trab     = info.get('num_trabajadores', 0)
            n_presentes = info.get('num_presentes', 0)
            cerrada    = info.get('cerrada', False)
            tipo_rep   = info.get('tipo_reporte', 'AVANCE')
            total_t   += n_trab

            estado_icon = "lock" if cerrada else "clock-outline"
            estado_color = (0.65, 0.08, 0.08, 1) if cerrada else (0.18, 0.42, 0.18, 1)

            icono = IconLeftWidget(
                icon=estado_icon,
                theme_text_color="Custom",
                icon_color=estado_color
            )
            item = TwoLineIconListItem(
                text=f"[b]Cuadrilla {cuadrilla}[/b]  —  {nombre}",
                secondary_text=(
                    f"Detectado: {hora}  |  "
                    f"{n_presentes}/{n_trab} presentes  |  {tipo_rep}"
                ),
                on_release=lambda x, c=cuadrilla: self._ver_detalle(c)
            )
            item.add_widget(icono)
            self.ids.lista_cuadrilleros.add_widget(item)

        self.total_cuadrilleros = str(len(cuadrilleros))
        self.total_trabajadores = str(total_t)

    def _ver_detalle(self, cuadrilla):
        app   = MDApp.get_running_app()
        lista = app.listas_recibidas.get(cuadrilla)
        if not lista:
            Snackbar(text="Presiona PEDIR AVANCE primero").open()
            return
        pd = app.root.get_screen('detalle')
        pd.cargar_detalle(cuadrilla, lista)
        app.root.current = 'detalle'

    def pedir_todas_listas(self):
        app   = MDApp.get_running_app()
        count = 0
        for cuadrilla, info in app.cuadrilleros_detectados.items():
            ip = info.get('ip')
            if ip:
                app.pedir_lista_cuadrillero(ip, cuadrilla)
                count += 1
        if count == 0:
            Snackbar(text="Sin cuadrilleros detectados").open()
        else:
            Snackbar(text=f"Pidiendo avance a {count} cuadrillero(s)...").open()

    def exportar(self):
        app = MDApp.get_running_app()
        if not app.listas_recibidas:
            Snackbar(text="Sin listas para exportar").open()
            return
        listas = list(app.listas_recibidas.values())
        ruta   = exportar_csv(listas, "avance")
        if ruta:
            guardar_listas(listas)
            Snackbar(text=f"CSV guardado: {os.path.basename(ruta)}").open()
        else:
            Snackbar(text="Error al exportar").open()

    def exportar_final(self):
        app = MDApp.get_running_app()
        if not app.listas_recibidas:
            Snackbar(text="Sin listas para exportar").open()
            return
        # Solo listas cerradas
        finales = {
            k: v for k, v in app.listas_recibidas.items()
            if v.get('jornada_cerrada', False)
        }
        if not finales:
            # Si no hay cerradas, exportar todas como avance
            finales = app.listas_recibidas
        listas = list(finales.values())
        ruta   = exportar_csv(listas, "final")
        if ruta:
            guardar_listas(listas)
            Snackbar(text=f"Reporte final: {os.path.basename(ruta)}").open()
        else:
            Snackbar(text="Error al exportar").open()

    def limpiar_dia(self):
        app = MDApp.get_running_app()
        app.cuadrilleros_detectados = {}
        app.listas_recibidas        = {}
        self.ids.lista_cuadrilleros.clear_widgets()
        self.total_cuadrilleros = "0"
        self.total_trabajadores = "0"
        Snackbar(text="Datos limpiados").open()


class PantallaDetalle(Screen):
    titulo_detalle    = StringProperty("")
    subtitulo_detalle = StringProperty("")
    info_lista        = StringProperty("")

    def cargar_detalle(self, cuadrilla, lista):
        self.titulo_detalle    = f"Cuadrilla {cuadrilla}"
        nombre_cuad = lista.get('cuadrillero', '').replace('\n', ' ')
        cerrada     = lista.get('jornada_cerrada', False)
        tipo_rep    = lista.get('tipo_reporte', 'AVANCE')
        self.subtitulo_detalle = f"{nombre_cuad}  |  {tipo_rep}"

        cuadro       = lista.get('cuadro', '')
        actividad    = lista.get('actividad', '')
        fecha        = lista.get('fecha', '')
        hora_rep     = lista.get('hora_reporte', '')
        trabajadores = lista.get('trabajadores', {})
        presentes    = sum(1 for v in trabajadores.values() if v.get('validado'))
        total        = len(trabajadores)

        estado = "CERRADA" if cerrada else "EN CURSO"
        self.info_lista = (
            f"Cuadro: {cuadro}  |  {fecha} {hora_rep}  [{estado}]\n"
            f"Actividad: {actividad[:40]}\n"
            f"Presentes: {presentes} / {total}"
        )

        self.ids.lista_detalle.clear_widgets()
        for cred, info in trabajadores.items():
            validado = info.get('validado', False)
            nombre   = info.get('nombre', '').replace('\n', ' ')
            periodos = info.get('periodos', [])
            gps      = info.get('gps', '')

            # Construir texto de periodos
            per_txt = "  ".join([
                f"{p.get('tipo','').replace('_',' ')[:4].upper()} {p.get('hora','')}"
                for p in periodos
            ]) or ("PRESENTE" if validado else "AUSENTE")

            icono = IconLeftWidget(
                icon="check-circle" if validado else "close-circle",
                theme_text_color="Custom",
                icon_color=(0.18, 0.42, 0.18, 1) if validado else (0.72, 0.10, 0.10, 1)
            )
            item = TwoLineIconListItem(
                text=f"Cred. {cred}  —  {nombre}",
                secondary_text=per_txt + (f"  GPS:{gps}" if gps else ""),
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
        # Cargar listas guardadas
        listas_guardadas = cargar_listas()
        for lista in listas_guardadas:
            cuadrilla = lista.get('cuadrilla', '')
            if cuadrilla:
                self.listas_recibidas[cuadrilla] = lista
        pi = self.root.get_screen('inicio')
        pi.estado_escucha = "Activo"
        pi.color_estado   = [0.18, 0.42, 0.18, 1]
        pi.fecha_hoy      = datetime.datetime.now().strftime("%d/%m/%Y  %H:%M")

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

                    while self._escucha_activa:
                        try:
                            datos_raw, addr = sock.recvfrom(1024)
                            msg    = datos_raw.decode('utf-8').strip()
                            partes = msg.split(':')

                            if len(partes) >= 3 and partes[0] == 'CUADRILLERO':
                                cuadrilla = partes[1]
                                nombre    = ':'.join(partes[2:])
                                ahora     = datetime.datetime.now().strftime("%H:%M:%S")
                                ip        = addr[0]

                                lista_cuad = self.listas_recibidas.get(cuadrilla, {})
                                n_trab = len(lista_cuad.get('trabajadores', {}))
                                n_pres = sum(
                                    1 for v in lista_cuad.get('trabajadores', {}).values()
                                    if v.get('validado')
                                )

                                ya_existe = cuadrilla in self.cuadrilleros_detectados
                                self.cuadrilleros_detectados[cuadrilla] = {
                                    "nombre":          nombre,
                                    "hora_deteccion":  ahora,
                                    "ip":              ip,
                                    "num_trabajadores": n_trab,
                                    "num_presentes":   n_pres,
                                    "cerrada":         lista_cuad.get('jornada_cerrada', False),
                                    "tipo_reporte":    lista_cuad.get('tipo_reporte', 'AVANCE')
                                }
                                if not ya_existe:
                                    Clock.schedule_once(lambda dt: self._actualizar_ui(), 0)

                        except socket.timeout:
                            continue
                        except Exception as e:
                            print(f"[WIFI] Error: {e}")

            except Exception as e:
                print(f"[WIFI] Error cuadrilleros: {e}")
            finally:
                self._escucha_activa = False

        threading.Thread(target=_escuchar, daemon=True).start()

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

                    while self._recepcion_activa:
                        try:
                            datos_raw, addr = sock.recvfrom(65535)
                            msg     = datos_raw.decode('utf-8').strip()
                            payload = json.loads(msg)

                            if payload.get('tipo') == 'LISTA_CUADRILLA':
                                cuadrilla = payload.get('cuadrilla', '')
                                self.listas_recibidas[cuadrilla] = payload

                                # Actualizar info del cuadrillero
                                trabajadores = payload.get('trabajadores', {})
                                n_trab = len(trabajadores)
                                n_pres = sum(
                                    1 for v in trabajadores.values()
                                    if v.get('validado')
                                )
                                if cuadrilla in self.cuadrilleros_detectados:
                                    self.cuadrilleros_detectados[cuadrilla].update({
                                        "num_trabajadores": n_trab,
                                        "num_presentes":    n_pres,
                                        "cerrada":  payload.get('jornada_cerrada', False),
                                        "tipo_reporte": payload.get('tipo_reporte', 'AVANCE')
                                    })

                                Clock.schedule_once(lambda dt: self._actualizar_ui(), 0)
                                tipo = payload.get('tipo_reporte', 'AVANCE')
                                Snackbar(
                                    text=f"Lista {tipo} C{cuadrilla}: {n_pres}/{n_trab}"
                                ).open()

                        except socket.timeout:
                            continue
                        except json.JSONDecodeError:
                            continue
                        except Exception as e:
                            print(f"[WIFI] Error lista: {e}")

            except Exception as e:
                print(f"[WIFI] Error recepcion: {e}")
            finally:
                self._recepcion_activa = False

        threading.Thread(target=_escuchar, daemon=True).start()

    def pedir_lista_cuadrillero(self, ip: str, cuadrilla: str):
        def _pedir():
            try:
                msg = f"PEDIR_LISTA:{cuadrilla}"
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                    sock.settimeout(5.0)
                    sock.sendto(msg.encode('utf-8'), (ip, PUERTO_CUADRILLERO))
            except Exception as e:
                print(f"[WIFI] Error pidiendo lista: {e}")

        threading.Thread(target=_pedir, daemon=True).start()

    def _actualizar_ui(self):
        pi = self.root.get_screen('inicio')
        if self.root.current == 'inicio':
            pi.actualizar_ui(self.cuadrilleros_detectados)

    def on_stop(self):
        self._escucha_activa   = False
        self._recepcion_activa = False


if __name__ == '__main__':
    ApuntadorAgriCactusApp().run()
