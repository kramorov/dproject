# pa_controls/views/signal_profiles.py
"""
GET /api/pa-controls/signal-profiles/ — справочник профилей сигналов БКВ.

Профили с развёрнутыми записями (роль → датчик / входной сигнал)
для формы админки БКВ (просмотр состава профиля).
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from params.models import ControlUnitSignalProfile


class LimitSwitchSignalProfilesView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        qs = ControlUnitSignalProfile.objects.filter(is_active=True).prefetch_related(
            'entries__signal_role',
            'entries__sensor__signal_type',
            'entries__sensor__contact_form',
            'entries__input_signal',
        ).order_by('sorting_order', 'name')

        result = []
        for profile in qs:
            entries = []
            for e in profile.entries.all():
                component = None
                signal_type = None
                contact_form = None
                if e.sensor_id:
                    component = e.sensor.name
                    if e.sensor.signal_type_id:
                        signal_type = e.sensor.signal_type.name
                    if e.sensor.contact_form_id:
                        contact_form = e.sensor.contact_form.name
                elif e.input_signal_id:
                    component = e.input_signal.name
                entries.append({
                    'role': e.signal_role.name if e.signal_role_id else '—',
                    'direction': e.signal_role.direction if e.signal_role_id else '—',
                    'component': component or '—',
                    'signal_type': signal_type,
                    'contact_form': contact_form,
                })
            result.append({
                'id': profile.id,
                'name': profile.name,
                'code': profile.code,
                'description': profile.description,
                'entries': entries,
            })
        return Response(result)
