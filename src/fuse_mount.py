#!/usr/bin/env python3
"""
FiUnamFS FUSE Mount - Módulo de montaje FUSE para FiUnamFS

Este módulo implementa una interfaz FUSE (Filesystem in Userspace) que
permite montar un filesystem FiUnamFS como un directorio nativo del sistema.

OPERACIONES IMPLEMENTADAS:

Lectura:
- getattr(): Obtener atributos de archivos/directorios
- readdir(): Listar contenidos del directorio
- read(): Leer contenido de un archivo

Escritura:
- write(): Escribir datos a un archivo
- create(): Crear un nuevo archivo
- truncate(): Truncar archivo (para sobrescritura)

Eliminación:
- unlink(): Eliminar un archivo

ARQUITECTURA:

El módulo usa la clase Filesystem existente para todas las operaciones,
manteniendo la consistencia con la CLI. No requiere threading adicional
ya que FUSE maneja las llamadas en su propio contexto de hilos.

Autor: PaoGo (pao.gonzma@gmail.com)
"""

import os
import sys
import errno
import stat
import time
from typing import Dict, List

try:
    from fuse import FUSE, FuseOSError, Operations
except ImportError:
    print("Error: fusepy no está instalado.", file=sys.stderr)
    print("Instálalo con: pip3 install fusepy", file=sys.stderr)
    sys.exit(1)

from models.filesystem import Filesystem
from utils.exceptions import (
    FileNotFoundInFilesystemError,
    FilenameConflictError,
    NoSpaceError,
    DirectoryFullError
)


class FiUnamFSMount(Operations):
    """
    Implementación FUSE para FiUnamFS.

    Esta clase expone el filesystem FiUnamFS como un directorio montable
    en el sistema operativo, permitiendo usar herramientas nativas.

    Atributos:
        fs: Instancia de Filesystem (maneja operaciones de bajo nivel)
        fs_path: Ruta al archivo .img del filesystem
    """

    def __init__(self, fs_path: str):
        """
        Inicializa el mount point de FUSE.

        Args:
            fs_path: Ruta al archivo .img del filesystem FiUnamFS
        """
        self.fs_path = fs_path
        self.fs = Filesystem(fs_path)

        # Timestamp de montaje (usado para directorio raíz)
        self.mount_time = int(time.time())

    def destroy(self, path):
        """
        Limpieza al desmontar el filesystem.

        Args:
            path: Path del punto de montaje (ignorado)
        """
        if self.fs:
            self.fs.close()

    # ========== OPERACIONES DE LECTURA ==========

    def getattr(self, path: str, fh=None) -> Dict:
        """
        Obtiene atributos de un archivo o directorio.

        Esta operación es llamada por el kernel cuando se hace stat(),
        ls, o cualquier operación que necesite metadata del archivo.

        Args:
            path: Ruta del archivo (e.g., "/", "/archivo.txt")
            fh: File handle (no usado, FUSE lo provee)

        Returns:
            Diccionario con atributos del archivo (st_mode, st_size, etc.)

        Raises:
            FuseOSError: Si el archivo no existe (ENOENT)
        """
        # Directorio raíz
        if path == '/':
            return {
                'st_mode': stat.S_IFDIR | 0o755,  # Directorio con permisos 755
                'st_nlink': 2,                     # . y ..
                'st_size': 4096,                   # Tamaño convencional de directorio
                'st_ctime': self.mount_time,
                'st_mtime': self.mount_time,
                'st_atime': self.mount_time,
            }

        # Archivo individual
        # Remover el '/' inicial para buscar en el filesystem
        filename = path[1:]

        try:
            # Buscar el archivo en el directorio
            entry = self.fs._find_file(filename)

            # Convertir timestamp de FiUnamFS a Unix timestamp
            # Formato FiUnamFS: AAAAMMDDHHMMSS
            created = entry.created_timestamp
            modified = entry.modified_timestamp

            # Parsear timestamp (AAAAMMDDHHMMSS)
            try:
                created_time = time.mktime(time.strptime(created, '%Y%m%d%H%M%S'))
                modified_time = time.mktime(time.strptime(modified, '%Y%m%d%H%M%S'))
            except (ValueError, OverflowError):
                # Si el timestamp es inválido, usar el tiempo de montaje
                created_time = self.mount_time
                modified_time = self.mount_time

            return {
                'st_mode': stat.S_IFREG | 0o644,  # Archivo regular con permisos 644
                'st_nlink': 1,                     # Un solo link
                'st_size': entry.file_size,        # Tamaño del archivo
                'st_ctime': created_time,          # Tiempo de creación
                'st_mtime': modified_time,         # Tiempo de modificación
                'st_atime': modified_time,         # Último acceso = última modificación
            }

        except FileNotFoundInFilesystemError:
            # Archivo no existe
            raise FuseOSError(errno.ENOENT)

    def readdir(self, path: str, fh) -> List[str]:
        """
        Lista el contenido de un directorio.

        En FiUnamFS solo hay un directorio (raíz), por lo que siempre
        retorna la lista completa de archivos activos.

        Args:
            path: Ruta del directorio (debe ser "/")
            fh: File handle (no usado)

        Returns:
            Lista de nombres de archivos (incluyendo '.' y '..')

        Raises:
            FuseOSError: Si el path no es "/" (ENOENT)
        """
        # Solo soportamos el directorio raíz
        if path != '/':
            raise FuseOSError(errno.ENOENT)

        # Obtener lista de archivos del filesystem
        result = self.fs.list_files()

        # FUSE requiere '.' y '..' en la lista
        files = ['.', '..']

        # Agregar todos los archivos activos
        for file_info in result['files']:
            files.append(file_info['filename'])

        return files

    def read(self, path: str, size: int, offset: int, fh) -> bytes:
        """
        Lee datos de un archivo.

        Args:
            path: Ruta del archivo (e.g., "/archivo.txt")
            size: Número de bytes a leer
            offset: Posición desde donde leer
            fh: File handle (no usado)

        Returns:
            Bytes leídos del archivo

        Raises:
            FuseOSError: Si el archivo no existe (ENOENT)
        """
        # Remover el '/' inicial
        filename = path[1:]

        try:
            # Buscar el archivo
            entry = self.fs._find_file(filename)

            # Leer todos los datos del archivo
            data = self.fs._read_file_data(entry)

            # Retornar el slice solicitado
            return data[offset:offset + size]

        except FileNotFoundInFilesystemError:
            raise FuseOSError(errno.ENOENT)

    # ========== OPERACIONES AUXILIARES ==========

    def statfs(self, path: str) -> Dict:
        """
        Retorna estadísticas del filesystem.

        Usado por comandos como 'df' para mostrar espacio usado/libre.

        Args:
            path: Ruta (ignorado, siempre retorna stats globales)

        Returns:
            Diccionario con estadísticas del filesystem
        """
        result = self.fs.list_files()

        total_clusters = self.fs.superblock.total_clusters
        cluster_size = self.fs.superblock.cluster_size

        # Clusters usados por datos (result tiene bytes, convertir a clusters)
        used_bytes = result['used_space']
        used_clusters = (used_bytes + cluster_size - 1) // cluster_size

        # Clusters libres
        free_clusters = total_clusters - used_clusters - 5  # 5 = superblock + directorio

        return {
            'f_bsize': cluster_size,           # Tamaño de bloque
            'f_frsize': cluster_size,          # Tamaño de fragmento
            'f_blocks': total_clusters,        # Total de bloques
            'f_bfree': free_clusters,          # Bloques libres
            'f_bavail': free_clusters,         # Bloques disponibles para no-root
            'f_files': 64,                     # Total de inodos (entradas de directorio)
            'f_ffree': 64 - result['total_files'],  # Inodos libres
            'f_favail': 64 - result['total_files'], # Inodos disponibles
            'f_namemax': 14,                   # Longitud máxima de nombre
        }
