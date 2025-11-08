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

## Arquitectura de Threading

### Modelo de 2 hilos

1. **Hilo de E/S (I/O Thread)**:
   - Ejecuta todas las operaciones del filesystem
   - Mantiene el file handle exclusivo de la imagen
   - Consume comandos de la cola de comandos

2. **Hilo de Interfaz (UI Thread)**:
   - Maneja la entrada del usuario y argumentos CLI
   - Produce comandos en la cola de comandos
   - Consume resultados de la cola de resultados

### Sincronización

- **Mecanismo**: `queue.Queue` (FIFO thread-safe)
- **Prevención de race conditions**: Solo el hilo de E/S accede al archivo del filesystem
- **Patrón single-writer**: Garantiza integridad de datos sin necesidad de locks explícitos

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
