# params/exd_signals.py
"""Инвалидация кэша совместимости Exd при изменении справочников.

Версия EXD_COMPAT_CACHE_VERSION_KEY инкрементируется при любом изменении
справочников взрывозащиты; configurator.services.parameter_filter включает
версию в ключ кэша (см. exd-option.md §6.2).
"""
from django.db.models.signals import post_save, post_delete

EXD_COMPAT_CACHE_VERSION_KEY = 'exd_compat_version'

_registered = False


def _bump_version(sender, **kwargs):
    from django.core.cache import cache
    try:
        cache.incr(EXD_COMPAT_CACHE_VERSION_KEY, ignore_key_check=True)
    except Exception:
        pass


def register():
    global _registered
    if _registered:
        return
    from .exd_models import (
        ExdOption, TemperatureClass, HazardousGroup,
        ExplosionProtectionMethod, ExplosionProtectionType,
    )
    for model in (
        ExdOption, TemperatureClass, HazardousGroup,
        ExplosionProtectionMethod, ExplosionProtectionType,
    ):
        post_save.connect(_bump_version, sender=model,
                          dispatch_uid=f'exd_bump_save_{model.__name__}')
        post_delete.connect(_bump_version, sender=model,
                            dispatch_uid=f'exd_bump_delete_{model.__name__}')
    _registered = True


register()
