import streamlit as st
import pandas as pd
from db_init import init_django

init_django()
from pneumatic_fittings.models import PneumaticFitting

st.title("✍️ Редактор базы данных")

# Загружаем данные
query = PneumaticFitting.objects.all().values('id', 'name', 'code', 'is_active', 'pipe_diameter')
df = pd.DataFrame(list(query))

st.write("Измените данные прямо в таблице и нажмите кнопку сохранения ниже.")

# Визуальный редактор
edited_df = st.data_editor(
    df,
    num_rows="dynamic",
    disabled=["id"],
    width="stretch", # Новый формат (растянуть по ширине)
    key="fitting_editor"
)

if st.button("💾 Сохранить изменения в Django DB"):
    try:
        for index, row in edited_df.iterrows():
            PneumaticFitting.objects.update_or_create(
                id=row['id'],
                defaults={
                    'name': row['name'],
                    'code': row['code'],
                    'is_active': row['is_active'],
                    'pipe_diameter': row.get('pipe_diameter', 0)
                }
            )
        st.success("Данные успешно синхронизированы с БД!")
    except Exception as e:
        st.error(f"Ошибка при сохранении: {e}")