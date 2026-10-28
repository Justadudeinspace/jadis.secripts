"""Compatibility facade preserving bounded ramdisk inspection imports."""

from secripts.images.ramdisk import compression, cpio_metadata
from secripts.images.ramdisk import inspect_ramdisk as _inspect

LIMIT = 16 * 1024 * 1024


def inspect_ramdisk(data, declared_size, *, output_limit=None):
    return _inspect(
        data,
        declared_size,
        output_limit=min(LIMIT, output_limit if output_limit is not None else LIMIT),
    )


__all__ = ["compression", "cpio_metadata", "inspect_ramdisk"]
