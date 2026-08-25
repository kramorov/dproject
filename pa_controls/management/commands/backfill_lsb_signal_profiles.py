# pa_controls/management/commands/backfill_lsb_signal_profiles.py
"""
Перенос БКВ на новую схему сигналов (профили ControlUnitSignalProfile).

По составу каждой коробки (points + датчики) создаёт/переиспользует типовой
профиль сигналов и привязывает его к LimitSwitchBox.signal_profile.

Правила разметки ролей:
  - 2 точки:  Вых. Открыто + Вых. Закрыто (один переключатель/модель на обе роли);
  - 3 точки:  + Вых. Промежуточное положение;
  - 4 точки:  + Вых. 2 промежуточных положения (2 датчика);
  - датчик-трансмиттер (4-20 мА) → Вых. Текущее положение (аналоговый сигнал).

Запуск:
  python manage.py backfill_lsb_signal_profiles            # dry-run
  python manage.py backfill_lsb_signal_profiles --apply    # записать
  python manage.py backfill_lsb_signal_profiles --apply --force  # перепривязать
"""
import logging
from collections import Counter, defaultdict

from django.core.management.base import BaseCommand
from django.db import transaction

from pa_controls.models import LimitSwitchBox
from params.models import (
    ControlUnitSignalProfile,
    ControlUnitSignalProfileEntry,
    SignalRole,
)

logger = logging.getLogger(__name__)

ROLE_OPEN = 'OUTPUT_OPEN'
ROLE_CLOSE = 'OUTPUT_CLOSE'
ROLE_WAY = 'OUTPUT_WAY_SWITCH'
ROLE_WAY_X2 = 'OUTPUT_WAY_SWITCH_X2'
ROLE_CURRENT_POS = 'OUTPUT_CURRENT_POSITION'

ROLES_HINT = {
    1: 'закрыто',
    2: 'откр/закр',
    3: 'откр/закр + промежуточное',
    4: 'откр/закр + 2 промежуточных',
}

# Код типа датчика по схеме артикулов БКВ (ЯМАЛ/УРАЛ): буква + цифра.
# M1 — механика SPDT (V-152), D0 — DPDT (SV-16), N4 — NAMUR safety (SJ3,5-SN),
# N5 — NAMUR Ex (NJ2-V3-N), N7 — PNP (NBB2), N8 — NAMUR Ex (SNI3,5),
# R8 — геркон SPST (МКА), R9 — геркон SPDT (DOS), E — трансмиттер, P — потенциометр.
# Ex-цифра артикула (0/1/2/3) в код профиля НЕ входит — профиль общий для всех Ex.
SENSOR_CODE_MAP = {
    'SNI3,5-G-3,5-PL-0,5-HT2': 'N8',
    'V-152-1C25': 'M1',
    'DOS-23R': 'R9',
    'NJ2-V3-N': 'N5',
    'SJ3,5-SN': 'N4',
    'NBB2-V3-E2': 'N7',
    'SV-16': 'D0',
    'МКА-20103М': 'R8',
}

# Цифра партнёра в E-кодах (трансмиттер + датчик): E0 — механика SPDT, E5 — NAMUR
E_PARTNER_DIGIT = {
    'V-152-1C25': '0',
    'NJ2-V3-N': '5',
}


def _sensor_token(sensor):
    """Код типа датчика из артикула БКВ: буква+цифра (например 'M1', 'N8')."""
    if not sensor:
        return 'M0'
    token = SENSOR_CODE_MAP.get(sensor.code or '')
    if token:
        return token
    variety = sensor.variety.name if sensor.variety_id else ''
    cf = sensor.contact_form.code if sensor.contact_form_id else ''
    st = sensor.signal_type.name if sensor.signal_type_id else ''
    if variety == 'Механический':
        return 'D0' if cf == 'DPDT' else 'M1' if cf == 'SPDT' else 'M0'
    if variety == 'Индуктивный':
        if 'функцией безопасности' in st:
            return 'N4'
        if 'PNP' in st:
            return 'N7'
        return 'N5'
    if variety == 'Герконовый':
        return 'R9' if cf == 'SPDT' else 'R8'
    if variety == 'Трансмиттер':
        return 'E'
    if variety == 'Потенциометр':
        return 'P0'
    return 'M0'


def _is_transmitter(sensor):
    st = (sensor.signal_type.name or '') if sensor.signal_type_id else ''
    return '4-20' in st


def _roles_for_box(box, sensors):
    """Возвращает список (code_роли, датчик) для коробки."""
    tx = [s for s in sensors if _is_transmitter(s)]
    mech = [s for s in sensors if not _is_transmitter(s)]
    roles = []

    if mech:
        if box.points >= 2:
            roles.append((ROLE_OPEN, mech[0]))
            roles.append((ROLE_CLOSE, mech[0] if len(mech) == 1 else mech[1]))
        if box.points == 3:
            roles.append((ROLE_WAY, mech[0] if len(mech) <= 2 else mech[2]))
        if box.points == 4:
            roles.append((ROLE_WAY_X2, mech[0]))
    if tx:
        roles.append((ROLE_CURRENT_POS, tx[0]))

    # Убираем дубли (роль, датчик) с сохранением порядка
    seen, unique = set(), []
    for role, sensor in roles:
        if (role, sensor.id) not in seen:
            seen.add((role, sensor.id))
            unique.append((role, sensor))
    return unique


def _profile_code(box, sensors):
    """Код профиля по схеме артикулов БКВ: {точек}{буква}{цифра-типа}.

    Смешанные составы (трансмиттер + датчик): буква E + цифра партнёра
    (E0 — механика SPDT, E5 — NAMUR). Ex-цифра артикула не входит.
    """
    tx = [s for s in sensors if _is_transmitter(s)]
    mech = [s for s in sensors if not _is_transmitter(s)]
    if tx:
        partner_digit = E_PARTNER_DIGIT.get((mech[0].code or '') if mech else '', '0')
        return f"{box.points}E{partner_digit}"
    primary = box.primary_sensor or (mech[0] if mech else None)
    token = _sensor_token(primary)
    if token == 'E':
        return f"{box.points}E0"
    return f"{box.points}{token}"


def _profile_name(box, roles):
    signal_types = []
    for _role, sensor in roles:
        name = sensor.signal_type.name if sensor.signal_type_id else 'без типа'
        if name not in signal_types:
            signal_types.append(name)
    return f"БКВ {box.points} датчика ({ROLES_HINT.get(box.points, '')}), " + " + ".join(signal_types)


class Command(BaseCommand):
    help = 'Переносит БКВ на профили сигналов (ControlUnitSignalProfile).'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true',
                            help='Записать изменения (по умолчанию dry-run)')
        parser.add_argument('--force', action='store_true',
                            help='Перепривязать коробки, у которых профиль уже есть')

    @transaction.atomic
    def handle(self, *args, **options):
        apply = options['apply']
        force = options['force']

        role_map = {
            code: SignalRole.objects.get(code=code)
            for code in (ROLE_OPEN, ROLE_CLOSE, ROLE_WAY, ROLE_WAY_X2, ROLE_CURRENT_POS)
        }

        boxes = (
            LimitSwitchBox.objects
            .select_related('primary_sensor__signal_type')
            .order_by('id')
        )

        stats = Counter()
        profile_boxes = defaultdict(list)

        for box in boxes:
            if box.signal_profile_id and not force:
                stats['already_bound'] += 1
                continue

            sensors = []
            if box.primary_sensor_id:
                sensors.append(box.primary_sensor)

            roles = _roles_for_box(box, sensors)
            if not roles:
                stats['no_sensor_data'] += 1
                self.stdout.write(self.style.WARNING(
                    f'  box #{box.id} "{box.name[:40]}" — нет данных о датчиках, пропущена'
                ))
                continue

            code = _profile_code(box, sensors)
            name = _profile_name(box, roles)

            if apply:
                profile, created = ControlUnitSignalProfile.objects.get_or_create(
                    code=code,
                    defaults={
                        'name': name,
                        'description': 'Типовой профиль БКВ (создан автоматически при переносе данных).',
                        'sorting_order': 100,
                        'is_active': True,
                    },
                )
                if created:
                    stats['profiles_created'] += 1
                else:
                    stats['profiles_reused'] += 1
                    if profile.name != name:
                        profile.name = name
                        profile.save(update_fields=['name'])
                        stats['profiles_renamed'] += 1

                for role_code, sensor in roles:
                    entry, e_created = ControlUnitSignalProfileEntry.objects.get_or_create(
                        profile=profile,
                        signal_role=role_map[role_code],
                        defaults={'sensor': sensor, 'is_default_calibration': True},
                    )
                    if e_created:
                        stats['entries_created'] += 1

                if box.signal_profile_id != profile.id:
                    box.signal_profile = profile
                    box.save(update_fields=['signal_profile'])
                    stats['boxes_bound'] += 1
            else:
                stats['boxes_planned'] += 1

            profile_boxes[code].append(box.id)

        self.stdout.write('')
        self.stdout.write(self.style.MIGRATE_HEADING(
            'DRY-RUN' if not apply else 'APPLIED'
        ))
        self.stdout.write(f"  коробок обработано: {sum(profile_boxes[k].__len__() for k in profile_boxes)}"
                          f" (всего в выборке: {boxes.count()})")
        self.stdout.write(f"  пропущено — уже привязаны: {stats['already_bound']}")
        self.stdout.write(f"  пропущено — нет данных о датчиках: {stats['no_sensor_data']}")
        self.stdout.write(f"  профилей создано: {stats['profiles_created']}")
        self.stdout.write(f"  профилей переиспользовано: {stats['profiles_reused']}")
        self.stdout.write(f"  профилей переименовано: {stats['profiles_renamed']}")
        self.stdout.write(f"  записей профилей создано: {stats['entries_created']}")
        self.stdout.write(f"  коробок привязано: {stats['boxes_bound']}")
        self.stdout.write('')
        self.stdout.write('Профили → коробки:')
        for code in sorted(profile_boxes):
            ids = profile_boxes[code]
            self.stdout.write(f"  {code}: {len(ids)} коробок (id: {ids[0]}..{ids[-1]})")
