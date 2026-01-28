# Hito 2: Extractor de Licencias y Copyright - Completado ✅

**Fecha:** 27 de enero, 2026  
**Estado:** Implementado y probado

---

## Resumen

Hemos implementado el extractor de licencias y copyright que enriquece el inventario detectado en el Hito 1 con información legal crítica. El sistema ahora puede:

- Leer archivos LICENSE/COPYING/NOTICE
- Detectar automáticamente tipos de licencia (MIT, Apache, BSD, GPL, etc.)
- Extraer declaraciones de copyright
- Obtener metadata de paquetes Python desde PyPI

---

## Nuevas Características Implementadas

### 1. ✅ Modelos de Datos para Licencias

**Nueva clase: `LicenseInfo`**
```python
@dataclass
class LicenseInfo:
    license_type: Optional[str]  # "MIT", "Apache-2.0", etc.
    license_file_path: Optional[str]
    license_text: Optional[str]
    copyright_statements: List[str]
    spdx_id: Optional[str]
```

**Nueva clase: `PyPIInfo`**
```python
@dataclass
class PyPIInfo:
    name: str
    version: Optional[str]
    license: Optional[str]
    home_page: Optional[str]
    project_url: Optional[str]
    author: Optional[str]
    summary: Optional[str]
```

### 2. ✅ Extractor de Licencias (`license_extractor.py`)

**Funcionalidades:**

- **Lector de archivos LICENSE**: Lee LICENSE, COPYING, NOTICE, COPYRIGHT
- **Detector de tipos de licencia**: Reconoce patrones de 10+ tipos comunes:
  - MIT
  - Apache-2.0
  - BSD-3-Clause, BSD-2-Clause
  - GPL-2.0, GPL-3.0
  - LGPL-2.1, LGPL-3.0
  - ISC
  - MPL-2.0
  - PSF (Python Software Foundation)
- **Detección de SPDX identifiers**: Lee `SPDX-License-Identifier:` tags
- **Extractor de copyright**: Detecta múltiples formatos:
  - `Copyright (c) 2024 Nombre`
  - `© 2024 Nombre`
  - `Copyrights: ...`
  - Con rangos de años: `2020-2024`

### 3. ✅ Cliente PyPI (`pypi_client.py`)

**Funcionalidades:**

- Consulta a PyPI JSON API: `https://pypi.org/pypi/{package}/json`
- Obtiene metadata por nombre de paquete
- Soporta versiones específicas
- Maneja versiones con operadores (`>=`, `==`, etc.)
- Timeout configurado (5 segundos)
- Logging detallado de requests
- Manejo robusto de errores (404, network, etc.)

**Información obtenida:**
- Nombre oficial del paquete
- Versión
- Licencia declarada
- Homepage / Project URL
- Autor
- Resumen/descripción

### 4. ✅ Integración con Core Scanner

**Nuevos parámetros en `scan_repository()`:**
```python
def scan_repository(
    repo_path: Path,
    toolkit_mode: bool = True,
    enrich_licenses: bool = True,  # ← NUEVO
    fetch_pypi: bool = True         # ← NUEVO
) -> Inventory:
```

**Proceso de enriquecimiento:**

1. Escaneo básico (Hito 1)
2. **Extracción de licencias** (si `enrich_licenses=True`):
   - Para cada `VendoredCandidate` con LICENSE files
   - Lee el archivo LICENSE
   - Detecta tipo de licencia
   - Extrae copyright statements
   - Añade `license_info` al candidato
3. **Fetch de PyPI** (si `fetch_pypi=True`):
   - Para cada `Dependency`
   - Consulta PyPI API
   - Obtiene metadata del paquete
   - Añade `pypi_info` a la dependencia

### 5. ✅ Nuevas Opciones CLI

```bash
--no-license-extraction  # Deshabilitar extracción de licencias
--no-pypi                # Deshabilitar fetch de PyPI
```

**Por defecto:**
- ✅ Licencias: HABILITADO
- ✅ PyPI: HABILITADO

---

## Ejemplo de Uso

### Escaneo Completo (con enriquecimiento)

```bash
python -m scanner --repo-path /path/to/tk-core --output inventory.json -v
```

**Salida:**
```
2026-01-27 18:00:00 - Extracting license information...
2026-01-27 18:00:00 - Enriched 2 vendored candidates with license info
2026-01-27 18:00:00 - Fetching PyPI metadata...
2026-01-27 18:00:04 - Fetched PyPI info for 6/7 dependencies
```

### Escaneo sin Enriquecimiento

```bash
python -m scanner --repo-path /path/to/repo --no-license-extraction --no-pypi
```

---

## Ejemplo de JSON Enriquecido

### Dependencia con PyPI Info

```json
{
  "source": "requirements.txt:12",
  "name": "pyyaml",
  "version_spec": "==5.4.1",
  "raw_line": "pyyaml==5.4.1",
  "pypi_info": {
    "name": "PyYAML",
    "version": "5.4.1",
    "license": "MIT",
    "home_page": "https://pyyaml.org/",
    "project_url": "https://pypi.org/project/PyYAML/",
    "author": "Kirill Simonov",
    "summary": "YAML parser and emitter for Python"
  }
}
```

### Vendored Candidate con License Info

```json
{
  "path": "python/tank_vendor/ruamel/yaml",
  "reason": "license_file_found",
  "license_files": ["python/tank_vendor/ruamel/yaml/LICENSE"],
  "is_toolkit_pattern": false,
  "license_info": {
    "license_type": "MIT",
    "license_file_path": "python/tank_vendor/ruamel/yaml/LICENSE",
    "license_text": " The MIT License (MIT)\n\n Copyright (c) 2014-2025...",
    "copyright_statements": [
      "Copyright (c) 2014-2025 Anthon van der Neut, Ruamel bvba"
    ],
    "spdx_id": null
  }
}
```

---

## Beneficios para el Proceso (Sección B del Wiki)

Este hito ayuda directamente con **Sección B - Paso 2b** del proceso del wiki:

✅ **"Identificar la licencia y titular de copyright de la versión específica"**
- Detección automática de tipos de licencia
- Extracción de copyright statements

✅ **"Helper para módulos Python: verificar LICENSE de paquetes instalados"**
- Lee archivos LICENSE automáticamente
- Extrae texto completo de licencias

✅ **"Recuperar información de entrada de https://pypi.org/"**
- Cliente PyPI integrado
- Metadata completa de paquetes

✅ **"Proporcionar enlace del repositorio github.com en el tag de la versión"**
- PyPI info incluye `home_page` y `project_url`

---

## Resultados de Pruebas

### Prueba con `tk-core`

**Comando:**
```bash
python -m scanner --repo-path ../tk-core --output tk-core-enriched.json -v
```

**Resultados:**
- ✅ 2 vendored candidates enriquecidos con license info
  - `python/tank_vendor/ruamel/yaml` → MIT detectada
  - `python/tank_vendor/yaml` → MIT detectada
- ✅ 6/7 dependencias con PyPI info
  - distro: Apache License
  - pyyaml: MIT
  - ruamel_yaml: MIT
  - six: MIT
  - coverage: Apache-2.0
  - ordereddict: (info obtenida)
- ✅ Copyright statements extraídos correctamente

### Prueba de Flags

**Comando:**
```bash
python -m scanner --repo-path ../tk-mari --no-license-extraction --no-pypi
```

**Resultados:**
- ✅ No ejecutó extracción de licencias
- ✅ No ejecutó fetch de PyPI
- ✅ Comportamiento esperado

---

## Archivos Creados/Modificados

### Archivos Nuevos:
- `scanner/license_extractor.py` - Extractor de licencias y copyright (284 líneas)
- `scanner/pypi_client.py` - Cliente API de PyPI (117 líneas)

### Archivos Modificados:
- `scanner/models.py` - Nuevas clases `LicenseInfo`, `PyPIInfo`, campos enriquecidos
- `scanner/core.py` - Integración de enriquecimiento, funciones `_enrich_with_licenses()` y `_enrich_with_pypi()`
- `scanner/cli.py` - Nuevas opciones `--no-license-extraction`, `--no-pypi`
- `scanner/__init__.py` - Exportar nuevas clases
- `README.md` - Documentación actualizada

---

## Patrones de Licencia Detectados

El detector reconoce estos patrones:

| Licencia | Patrones Clave |
|----------|----------------|
| MIT | "MIT License", "Permission is hereby granted, free of charge" |
| Apache-2.0 | "Apache License, Version 2.0", "apache.org/licenses" |
| BSD-3-Clause | "BSD 3-Clause", "Redistribution and use..." |
| GPL-2.0/3.0 | "GNU GENERAL PUBLIC LICENSE", "gnu.org/licenses/gpl" |
| LGPL-2.1/3.0 | "GNU LESSER GENERAL PUBLIC LICENSE" |
| ISC | "ISC License", "Permission to use, copy, modify" |
| MPL-2.0 | "Mozilla Public License Version 2.0" |
| PSF | "Python Software Foundation License" |

---

## Limitaciones Conocidas

### ⚠️ Detección de Licencia es Heurística

- Funciona bien para licencias estándar
- Licencias personalizadas pueden no detectarse
- **Siempre requiere revisión humana**

### ⚠️ No Determina PAOS vs. LeCorpio

- El escáner solo detecta el tipo de licencia
- La decisión PAOS/LeCorpio requiere consulta a Leap page
- **Requiere intervención Legal**

### ⚠️ PyPI puede no tener todos los paquetes

- Paquetes internos/privados no estarán en PyPI
- Algunos paquetes antiguos pueden faltar metadata
- Se maneja gracefully (log warning, continúa)

### ⚠️ Extracción de Copyright puede ser imperfecta

- Múltiples formatos de copyright statements
- Algunos pueden no capturarse
- Puede incluir líneas parciales
- **Requiere validación humana**

---

## Próximos Pasos

**Hito 3: Analizador y Generador de software_credits**
- Parsear archivo `software_credits` existente
- Comparar TPCs detectados vs. `software_credits`
- Generar reporte de diferencias
- Crear borrador actualizado de `software_credits`

---

## Performance

**Tiempo de escaneo (tk-core):**
- Escaneo básico (Hito 1): ~3 segundos
- Con extracción de licencias: +1 segundo
- Con PyPI fetch (7 paquetes): +4 segundos
- **Total: ~8 segundos**

**Optimizaciones posibles:**
- Caché de PyPI results
- Requests paralelos a PyPI
- Limite de tamaño de license_text

---

*Hito 2 completado - Listo para proceder al Hito 3* ✅
