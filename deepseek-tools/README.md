# DeepSeek Tools — reference for the agent

## Quick navigation (use these first)

```
python deepseek-tools/show_lines.py <path> <start> <end>
    → показать строки файла с номерами, Unicode-safe

python deepseek-tools/find_class.py <path> <ClassName> [all]
    → показать класс целиком (поля + Meta + __str__)
    → с 'all' — включая @property и методы

python deepseek-tools/dump_model_range.py <path> <ClassName> [padding]
    → класс + N строк после (по умолчанию только класс)

python deepseek-tools/list_model_fields.py <path> <ClassName>
    → только строки "= models." внутри класса
```

## Check/Debug one-off scripts

| Script | Purpose |
|---|---|
| `_check_models.py` | Django model field inspection (edit per need) |
| `_check_exd.py` | Quick Django attribute check |
| `_check_cert.py` | Find all class names in cert_doc/models.py |
| `_check_cert2.py` | Verify CertRelation compiles |
| `_check_media.py` | Verify MediaLibraryItem fields |
| `_check_media2.py` | Same but with path fix |
| `_check_fittings.py` | Verify PneumaticFitting get_filter_options |
| `_dump_exd.py` | Dump ExdOption data from DB |
| `_dump_vf.py` | Dump ValveFunction lines (old, use show_lines instead) |
| `_import_exd.py` | Import temperature class descriptions |
| `_apply_temp_descriptions.py` | Apply temp class descriptions to DB |
| `_show_temp_descriptions.py` | Show temp class descriptions |
| `_find_str.py` | Find __str__ method line numbers |
| `_find_class.py` | Find class by name (old, use find_class.py instead) |

## Legacy text files

| File | Content |
|---|---|
| `_valve_func.txt` | ValveFunction dump (outdated) |
| `_valve_function.txt` | ValveFunction dump (outdated) |
| `_direction_valve_model.txt` | DirectionValve model dump |
| `_dv_out.txt` | DirectionValve output |

## Typical workflow

1. `find_class.py` → see model structure
2. `list_model_fields.py` → see only DB fields  
3. `show_lines.py` → read exact lines for patch context
4. Write `_check_xxx.py` → verify Django compiles after edits
5. `apply_patch` or `edit_file` → make changes
6. Re-run `_check_xxx.py` → verify
