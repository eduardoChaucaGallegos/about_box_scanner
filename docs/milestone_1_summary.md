# Hito 1: Escáner de Repo Mejorado - Completado ✅

**Fecha:** 27 de enero, 2026  
**Estado:** Implementado y funcionando

---

## Resumen

Hemos mejorado el escáner de repositorios para alinearse específicamente con los patrones de ShotGrid Toolkit documentados en `docs/about_box_process.md`. El escáner ahora aplica heurísticas específicas de Toolkit por defecto.

---

## Nuevas Características Implementadas

### 1. ✅ Modo Toolkit (Activado por defecto)

El escáner ahora reconoce patrones específicos de Toolkit:

**Rutas vendored de Toolkit detectadas:**
- `shotgun_api3/lib`
- `python/vendors/`
- `desktopclient/python/vendors`
- `desktopserver/resources/python/`
- `tests/python/third_party/`
- `adobe/` (para archivos .zip)

**Archivos .zip en raíz:**
- Detecta archivos `.zip` en la raíz del repo
- Detecta archivos `.zip` en el directorio `adobe/`

### 2. ✅ Detección de `frozen_requirements.txt`

El escáner ahora:
- Busca archivos `frozen_requirements.txt` en todo el repo
- Los lista por separado en el inventario
- Los parsea para extraer dependencias
- Documenta su ubicación para auditorías Snyk

### 3. ✅ Detección de `software_credits`

Nueva funcionalidad para verificar el archivo `software_credits`:
- Detecta si existe en la raíz del repo
- Cuenta líneas de contenido
- Identifica si es un placeholder ("no third parties")
- Reporta el estado en el inventario

### 4. ✅ Búsqueda Mejorada de `requirements.txt`

El escáner ahora busca en múltiples niveles:
- `requirements.txt` (raíz)
- `*/requirements.txt` (nivel 1)
- `*/*/requirements.txt` (nivel 2)
- `*/*/*/requirements.txt` (nivel 3)

Esto captura patrones de Toolkit como:
- `desktopserver/resources/python/bin/requirements.txt`
- `desktopserver/resources/python/source/requirements.txt`

### 5. ✅ Modelos de Datos Mejorados

**Nueva clase: `SoftwareCreditsInfo`**
```python
@dataclass
class SoftwareCreditsInfo:
    exists: bool
    path: Optional[str] = None
    is_empty: bool = False
    line_count: int = 0
```

**Clase mejorada: `VendoredCandidate`**
- Nuevo campo: `is_toolkit_pattern: bool`
- Identifica candidatos que coinciden con patrones específicos de Toolkit

**Clase mejorada: `Inventory`**
- Nuevo campo: `software_credits: Optional[SoftwareCreditsInfo]`
- Nuevo campo: `frozen_requirements_files: List[str]`

### 6. ✅ CLI Mejorado

Nueva opción de línea de comandos:
```bash
--no-toolkit-mode    # Deshabilita patrones específicos de Toolkit
```

Por defecto, el modo Toolkit está **ACTIVADO**.

---

## Uso

### Escaneo Estándar (Modo Toolkit activado)

```bash
python -m scanner --repo-path /path/to/tk-core --output tk-core-inventory.json
```

### Escaneo Genérico (Modo Toolkit desactivado)

```bash
python -m scanner --repo-path /path/to/repo --output inventory.json --no-toolkit-mode
```

### Con Verbose

```bash
python -m scanner --repo-path /path/to/tk-desktop --output output.json -v
```

---

## Ejemplo de Salida JSON

```json
{
  "repo_path": "/path/to/tk-core",
  "scanned_at": "2026-01-27T10:30:00Z",
  "software_credits": {
    "exists": true,
    "path": "software_credits",
    "is_empty": false,
    "line_count": 145
  },
  "frozen_requirements_files": [
    "python/third_party/frozen_requirements.txt"
  ],
  "dependencies": [
    {
      "source": "requirements.txt:5",
      "name": "requests",
      "version_spec": ">=2.25.0",
      "raw_line": "requests>=2.25.0"
    }
  ],
  "vendored_candidates": [
    {
      "path": "shotgun_api3/lib",
      "reason": "toolkit_vendor_pattern",
      "license_files": ["shotgun_api3/lib/LICENSE"],
      "is_toolkit_pattern": true
    },
    {
      "path": "python/vendors",
      "reason": "toolkit_vendor_pattern",
      "license_files": [],
      "is_toolkit_pattern": true
    }
  ],
  "asset_candidates": [
    {
      "path": "resources/fonts/OpenSans-Regular.ttf",
      "type": "font",
      "reason": "in_font_directory | font_file_extension"
    }
  ]
}
```

---

## Archivos Modificados/Creados

### Archivos Nuevos:
- `scanner/software_credits_detector.py` - Detector de software_credits

### Archivos Modificados:
- `scanner/utils.py` - Patrones Toolkit, función `is_toolkit_vendor_path()`
- `scanner/models.py` - Nuevas clases `SoftwareCreditsInfo`, campos mejorados
- `scanner/dependency_parser.py` - Soporte para `frozen_requirements.txt`, búsqueda anidada
- `scanner/vendored_detector.py` - Detección de patrones Toolkit, archivos .zip
- `scanner/core.py` - Integración de todas las nuevas características
- `scanner/cli.py` - Nueva opción `--no-toolkit-mode`
- `scanner/__init__.py` - Exportar `SoftwareCreditsInfo`
- `README.md` - Documentación actualizada

---

## Beneficios para el Proceso (Sección B del Wiki)

Este hito ayuda directamente con **Sección B - Paso 1** del proceso del wiki:

✅ **"Abrir cada archivo e identificar si es propiedad de Autodesk"**
- El escáner identifica automáticamente candidatos de TPCs

✅ **"Crear una página wiki y listar los TPC por orden alfabético"**
- La salida JSON sirve como base para generar tablas wiki

✅ **"Nombre, versión, ruta en el repo git"**
- Toda esta información está capturada en el inventario

✅ **"¿Está el TPC listado en el archivo software_credits?"**
- Ahora detectamos si el archivo `software_credits` existe

✅ **"Mantener archivo frozen_requirements.txt"**
- Detectamos y listamos todos los archivos `frozen_requirements.txt`

---

## Limitaciones Conocidas

1. **No extrae información de licencias/copyright** (Hito 2)
2. **No compara con contenido de `software_credits`** (Hito 3)
3. **No valida aprobaciones PAOS/LeCorpio** (requiere intervención humana)
4. **Detección heurística** - puede tener falsos positivos/negativos que requieren revisión humana

---

## Próximos Pasos

**Hito 2: Extractor de Licencias y Copyright**
- Leer archivos LICENSE en candidatos detectados
- Extraer declaraciones de copyright
- Detectar tipos de licencia (MIT, Apache, BSD, GPL, etc.)
- Obtener info de PyPI para paquetes Python
- Enriquecer el inventario con esta información

---

## Testing

Para probar el escáner mejorado:

1. Instalar dependencias:
   ```bash
   cd about_box_scanner
   pip install -r requirements.txt
   ```

2. Escanear un repo de Toolkit:
   ```bash
   python -m scanner --repo-path /path/to/tk-core --output test-output.json -v
   ```

3. Revisar el archivo JSON de salida para verificar:
   - Campo `software_credits` presente
   - Lista `frozen_requirements_files`
   - Candidatos vendored con `is_toolkit_pattern: true`
   - Patrones específicos de Toolkit detectados

---

*Hito 1 completado - Listo para proceder al Hito 2* ✅
