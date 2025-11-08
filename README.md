# FiUnamFS Manager

Gestor de sistema de archivos FiUnamFS (Facultad de Ingeniería UNAM Filesystem) con arquitectura concurrente de 2 hilos.

## Autores

- PaoGo (pao.gonzma@gmail.com)

## Descripción

Este proyecto implementa un gestor de archivos para el sistema FiUnamFS, un filesystem que simula un disquete de 1.44MB. El programa permite listar, importar, exportar y eliminar archivos de imágenes de disco FiUnamFS mediante una interfaz de línea de comandos.

### Características principales

- **4 operaciones básicas**: list, export, import, delete
- **Arquitectura de 2 hilos**: Un hilo maneja las operaciones de E/S del filesystem, otro maneja la interfaz de usuario
- **Sincronización thread-safe**: Comunicación mediante `queue.Queue` de Python
- **Validación estricta**: Cumplimiento total de la especificación FiUnamFS (firma, versión, formato binario)
- **Sin dependencias externas**: Solo usa biblioteca estándar de Python

## Requisitos

- **Python**: 3.6 o superior
- **Sistema Operativo**: Linux, macOS o Windows
- **Dependencias**: Ninguna (solo biblioteca estándar de Python)

## Instalación

No requiere instalación de paquetes externos. Simplemente clona el repositorio:

```bash
git clone git@github.com:paogmtz/Proyecto2SO.git
cd Proyecto2SO
python3 --version  # Verificar Python 3.6+
```

## Uso

### Sintaxis general

```bash
python3 src/fiunamfs_manager.py <COMANDO> <IMAGEN_FILESYSTEM> [OPCIONES]
```

### Comandos disponibles

#### 1. Listar archivos

```bash
python3 src/fiunamfs_manager.py list fiunamfs/fiunamfs.img
```

#### 2. Exportar archivo (copiar del filesystem al sistema local)

```bash
python3 src/fiunamfs_manager.py export fiunamfs/fiunamfs.img ARCHIVO.txt ./salida/ARCHIVO.txt
```

#### 3. Importar archivo (copiar del sistema local al filesystem)

```bash
python3 src/fiunamfs_manager.py import fiunamfs/fiunamfs.img ./entrada/archivo.txt
```

#### 4. Eliminar archivo

```bash
python3 src/fiunamfs_manager.py delete fiunamfs/fiunamfs.img archivo.txt
```

### Ejemplos de salida

#### Listar archivos
```
================================================================================
Contenido del filesystem FiUnamFS
================================================================================

Archivo             Tamaño  Creado               Modificado           Cluster
---------------- ----------  -------------------- -------------------- -------
README.TXT            2,048  20250107120000       20250107120000           5
DATA.BIN             10,240  20250107130000       20250107140000          12

--------------------------------------------------------------------------------
Total: 2 archivos
Espacio usado: 12,288 bytes (12.00 KB)
Espacio libre: 1,457,152 bytes (1,423.00 KB)
================================================================================
```

#### Exportar archivo
```
✓ Archivo exportado exitosamente
  Archivo: README.TXT
  Tamaño: 2,048 bytes (2.00 KB)
  Destino: ./salida/README.TXT
```

#### Importar archivo
```
✓ Archivo importado exitosamente
  Archivo: NUEVO.TXT
  Tamaño: 1,500 bytes (1.46 KB)
  Cluster inicial: 25
  Clusters usados: 2
```

#### Eliminar archivo (con confirmación)
```
¿Eliminar 'DATA.BIN' (10,240 bytes)? [s/N]: s

✓ Archivo eliminado exitosamente
  Archivo: DATA.BIN
  Espacio liberado: 10,240 bytes (10.00 KB)
  Clusters liberados: 10
```

## Formato FiUnamFS

### Especificación técnica

FiUnamFS es un filesystem simple que simula un disquete de 1.44MB con las siguientes características:

- **Tamaño total**: 1,474,560 bytes (1.44 MB)
- **Tamaño de cluster**: 1,024 bytes (1 KB)
- **Total de clusters**: 1,440
- **Estructura**:
  - Cluster 0: Superblock (metadata del filesystem)
  - Clusters 1-4: Directorio (hasta 64 archivos)
  - Clusters 5-1439: Área de datos (1,435 clusters disponibles)

### Superblock (cluster 0, 1024 bytes)

| Offset | Tamaño | Campo            | Descripción                        |
|--------|--------|------------------|------------------------------------|
| 0-8    | 9      | signature        | "FiUnamFS" (ASCII)                 |
| 10-14  | 5      | version          | "26-1" o "26-2" (ASCII)            |
| 20-35  | 16     | volume_label     | Etiqueta del volumen               |
| 40-43  | 4      | cluster_size     | 1024 (little-endian uint32)        |
| 45-48  | 4      | directory_clusters | 3-4 (little-endian uint32)       |
| 50-53  | 4      | total_clusters   | 1440 (little-endian uint32)        |

### Directory Entry (64 bytes por entrada)

| Offset | Tamaño | Campo              | Descripción                          |
|--------|--------|--------------------|--------------------------------------|
| 0      | 1      | file_type          | '.' = activo, '-' = vacío            |
| 1-15   | 15     | filename           | Nombre (max 14 chars ASCII + null)   |
| 16-19  | 4      | start_cluster      | Cluster inicial (little-endian)      |
| 20-23  | 4      | file_size          | Tamaño en bytes (little-endian)      |
| 24-37  | 14     | created_timestamp  | AAAAMMDDHHMMSS (ASCII)               |
| 38-51  | 14     | modified_timestamp | AAAAMMDDHHMMSS (ASCII)               |
| 52-63  | 12     | reserved           | Reservado para uso futuro            |

### Limitaciones

- **Máximo de archivos**: Depende de clusters de directorio (3-4 clusters × 16 entradas = 48-64 archivos)
- **Nombres de archivo**: Máximo 14 caracteres ASCII
- **Sin subdirectorios**: Estructura plana únicamente
- **Asignación contigua**: Los clusters de un archivo deben ser consecutivos
- **Algoritmo first-fit**: Se asigna el primer espacio contiguo disponible

## Arquitectura de Threading

### Modelo de 2 hilos

El sistema implementa un modelo productor-consumidor bidireccional con dos hilos especializados:

#### 1. Hilo de E/S (I/O Thread) - `IOThread`
- **Responsabilidad**: Ejecutar todas las operaciones del filesystem
- **Recursos exclusivos**: Mantiene el file handle único del archivo .img
- **Rol en colas**:
  - Consumer de `command_queue` (recibe comandos)
  - Producer de `result_queue` (envía resultados)
- **Comportamiento**:
  - Bloquea en `queue.get()` esperando comandos (eficiente)
  - Se ejecuta en loop hasta recibir comando `'exit'`
  - Convierte todas las excepciones a diccionarios de error

#### 2. Hilo de Interfaz (UI Thread) - Main Thread
- **Responsabilidad**: Manejar interfaz de usuario y CLI
- **Rol en colas**:
  - Producer de `command_queue` (envía comandos)
  - Consumer de `result_queue` (recibe resultados)
- **Comportamiento**:
  - Envía comandos mediante `submit_command()` (non-blocking)
  - Espera resultados con `wait_for_result()` (blocking con timeout)
  - Nunca accede directamente al filesystem

### Sincronización Thread-Safe

#### Mecanismo de comunicación
- **Tipo**: `queue.Queue` de Python stdlib
- **Propiedades**: FIFO, thread-safe, bloqueo interno automático
- **Dos colas**:
  - `command_queue`: UI Thread → I/O Thread (comandos y argumentos)
  - `result_queue`: I/O Thread → UI Thread (resultados y errores)

#### Prevención de race conditions
- **Patrón Single-Writer**: Solo el I/O Thread modifica el filesystem
- **No se requieren locks manuales**: Queue maneja sincronización internamente
- **Orden garantizado**: Las operaciones se ejecutan en orden FIFO estricto
- **Aislamiento de recursos**: El file handle nunca se comparte entre hilos

#### Ventajas del diseño
- ✅ Sin deadlocks posibles (no hay locks manuales)
- ✅ Sin race conditions (un solo escritor)
- ✅ Eficiente (bloqueo inteligente en lugar de polling)
- ✅ Simple (Queue maneja toda la complejidad de sincronización)

## Manejo de Errores

El sistema valida exhaustivamente todas las operaciones y proporciona mensajes de error claros:

### Errores comunes

#### Filesystem inválido
```
❌ Error: Filesystem inválido: Firma incorrecta. Se esperaba 'FiUnamFS', se encontró 'INVALID'
```

#### Archivo no encontrado
```
❌ Error: Archivo 'NOEXISTE.TXT' no encontrado en el filesystem
   Archivos disponibles: README.TXT, DATA.BIN
```

#### Nombre de archivo inválido
```
❌ Error: Nombre de archivo demasiado largo. Máximo 14 caracteres, se recibieron 20
```

#### Sin espacio disponible
```
❌ Error: No hay espacio contiguo disponible
   Se necesitan: 50,000 bytes
   Disponibles: 12,288 bytes
```

#### Conflicto de nombre
```
❌ Error: Ya existe un archivo con el nombre 'README.TXT' en el filesystem
```

#### Directorio lleno
```
❌ Error: El directorio está lleno. Máximo 64 archivos permitidos
```

### Validaciones implementadas

- ✅ **Firma del filesystem**: Verifica "FiUnamFS" en superblock
- ✅ **Versión**: Valida versión "26-2"
- ✅ **Nombres de archivo**: Máximo 14 caracteres ASCII
- ✅ **Espacio disponible**: Verifica antes de importar
- ✅ **Asignación contigua**: Busca espacio contiguo suficiente
- ✅ **Duplicados**: Previene nombres duplicados
- ✅ **Límite de archivos**: Máximo 64 archivos en directorio
- ✅ **Timeout de threading**: 10 segundos por operación

## Cumplimiento Académico

Este proyecto cumple con los siguientes requisitos académicos:

- ✅ 5 operaciones implementadas (list, export, import, delete + threading)
- ✅ Estilo PEP 8 para código Python
- ✅ Arquitectura concurrente con 2 hilos
- ✅ Mecanismos de sincronización documentados
- ✅ Sin dependencias externas (solo stdlib)

## Estructura del Proyecto

```
proyecto2SO/
├── src/
│   ├── fiunamfs_manager.py    # Punto de entrada, CLI
│   ├── models/                 # Modelos de datos
│   │   ├── superblock.py
│   │   ├── directory_entry.py
│   │   └── filesystem.py
│   ├── services/               # Threading
│   │   ├── io_thread.py
│   │   └── ui_thread.py
│   └── utils/                  # Utilidades
│       ├── binary_utils.py
│       ├── validation.py
│       └── exceptions.py
├── tests/                      # Pruebas unitarias
├── fiunamfs/
│   └── fiunamfs.img           # Imagen de filesystem de prueba
└── README.md
```

## Licencia

Proyecto académico - Sistemas Operativos, Facultad de Ingeniería UNAM
