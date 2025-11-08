#!/usr/bin/env python3
"""
FiUnamFS Manager - Gestor de Sistema de Archivos FiUnamFS

Este programa proporciona una interfaz de línea de comandos para gestionar
archivos en imágenes de filesystem FiUnamFS (Facultad de Ingeniería UNAM).

Arquitectura de 2 hilos:
- Hilo de UI (Main): Maneja la interfaz de usuario mediante argparse
- Hilo de E/S (Worker): Ejecuta operaciones del filesystem

Comunicación mediante queue.Queue (thread-safe FIFO)
Sincronización: Solo el hilo de E/S modifica el filesystem (patrón single-writer)

Autor: PaoGo (pao.gonzma@gmail.com)
Versión: 1.0.0
"""

import argparse
import sys
from typing import Dict

from models.filesystem import Filesystem
from utils.exceptions import (
    FiUnamFSError,
    InvalidFilesystemError,
    FileNotFoundInFilesystemError
)


def display_list_result(result: Dict) -> None:
    """
    Muestra el resultado de la operación list de forma formateada.

    Args:
        result: Diccionario con 'files', 'total_files', 'used_space', 'free_space'
    """
    files = result['files']
    total_files = result['total_files']
    used_space = result['used_space']
    free_space = result['free_space']

    print(f"\n{'=' * 80}")
    print(f"Contenido del filesystem FiUnamFS")
    print(f"{'=' * 80}")

    if total_files == 0:
        print("\nNo hay archivos en el filesystem.")
    else:
        # Encabezados de la tabla
        print(f"\n{'Archivo':<16} {'Tamaño':>10}  {'Creado':<20} {'Modificado':<20} {'Cluster':>7}")
        print(f"{'-' * 16} {'-' * 10}  {'-' * 20} {'-' * 20} {'-' * 7}")

        # Listar cada archivo
        for file_info in files:
            filename = file_info['filename'][:15]  # Truncar si es muy largo
            size = file_info['size']
            created = file_info['created']
            modified = file_info['modified']
            cluster = file_info['start_cluster']

            print(f"{filename:<16} {size:>10}  {created:<20} {modified:<20} {cluster:>7}")

    # Resumen de espacio
    print(f"\n{'-' * 80}")
    print(f"Total: {total_files} archivos")
    print(f"Espacio usado: {used_space:,} bytes ({used_space / 1024:.2f} KB)")
    print(f"Espacio libre: {free_space:,} bytes ({free_space / 1024:.2f} KB)")
    print(f"{'=' * 80}\n")


def cmd_list(args: argparse.Namespace) -> int:
    """
    Ejecuta el comando 'list' para listar archivos del filesystem.

    Args:
        args: Argumentos parseados de argparse

    Returns:
        Código de salida (0 = éxito, 1 = error)
    """
    try:
        # Abrir filesystem y ejecutar operación
        with Filesystem(args.filesystem) as fs:
            result = fs.list_files()
            display_list_result(result)
        return 0

    except InvalidFilesystemError as e:
        print(f"\n❌ Error: Filesystem inválido", file=sys.stderr)
        print(f"   {e}", file=sys.stderr)
        print(f"\nVerifica que el archivo sea una imagen FiUnamFS válida.", file=sys.stderr)
        return 1

    except FileNotFoundError as e:
        print(f"\n❌ Error: Archivo no encontrado", file=sys.stderr)
        print(f"   No se pudo abrir: {args.filesystem}", file=sys.stderr)
        print(f"\nVerifica que la ruta sea correcta.", file=sys.stderr)
        return 1

    except FiUnamFSError as e:
        print(f"\n❌ Error en el filesystem: {e}", file=sys.stderr)
        return 1

    except Exception as e:
        print(f"\n❌ Error inesperado: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def main():
    """
    Función principal - configura argparse y ejecuta el comando apropiado.
    """
    # Parser principal
    parser = argparse.ArgumentParser(
        prog='fiunamfs_manager',
        description='Gestor de archivos para filesystem FiUnamFS',
        epilog='Proyecto académico - Sistemas Operativos, FI-UNAM'
    )

    # Subcommands
    subparsers = parser.add_subparsers(
        title='comandos',
        description='Operaciones disponibles',
        dest='command',
        required=True
    )

    # Comando: list
    parser_list = subparsers.add_parser(
        'list',
        help='Lista todos los archivos del filesystem'
    )
    parser_list.add_argument(
        'filesystem',
        help='Ruta a la imagen del filesystem (.img)'
    )
    parser_list.set_defaults(func=cmd_list)

    # Parsear argumentos
    args = parser.parse_args()

    # Ejecutar comando correspondiente
    exit_code = args.func(args)
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
