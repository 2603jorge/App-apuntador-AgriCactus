#
# Hook de python-for-android: agrega el <provider> de FileProvider
# directamente al AndroidManifest.xml generado, justo antes de compilar
# con Gradle. Esto es necesario porque buildozer.spec no tiene forma de
# insertar un elemento <provider> completo dentro de <application> --
# solo permite agregar atributos sueltos (extra_manifest_application_arguments)
# o elementos a nivel <manifest> (extra_manifest_xml), y <provider> tiene
# que ir SI o SI dentro de <application>.
#
from pathlib import Path


def after_apk_build(toolchain):
    manifest_file = Path(toolchain._dist.dist_dir) / "src" / "main" / "AndroidManifest.xml"
    if not manifest_file.exists():
        print(f"[HOOK] No se encontro AndroidManifest.xml en {manifest_file}, se omite.")
        return

    contenido = manifest_file.read_text(encoding="utf-8")

    if "androidx.core.content.FileProvider" in contenido:
        print("[HOOK] FileProvider ya estaba en el manifest, no se duplica.")
        return

    provider_xml = '''
    <provider
        android:name="androidx.core.content.FileProvider"
        android:authorities="${applicationId}.fileprovider"
        android:exported="false"
        android:grantUriPermissions="true">
        <meta-data
            android:name="android.support.FILE_PROVIDER_PATHS"
            android:resource="@xml/file_paths" />
    </provider>
'''

    nuevo_contenido = contenido.replace(
        "</application>",
        f"{provider_xml}\n    </application>"
    )

    manifest_file.write_text(nuevo_contenido, encoding="utf-8")
    print("[HOOK] FileProvider agregado correctamente al AndroidManifest.xml")
