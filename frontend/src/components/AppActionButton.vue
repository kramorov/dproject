<template>
  <button class="app-action-button" @click="$emit('click')">
    <img v-if="buttonData.icon" :src="getIconPath(buttonData.icon)" :alt="buttonData.label" class="icon" />
    <span v-else class="icon-text">{{ buttonData.iconFallback }}</span>
    <span class="label">{{ buttonData.label }}</span>
  </button>
</template>
<!--<AppActionButton icon="custom-icon.svg" label="Мой текст" @click="myFunction" />-->
<!--<AppActionButton type="Сохранить" @click="saveFunction" />-->
<!--<AppActionButton type="Отмена" @click="cancelFunction" />-->

<script>
export default {
  props: {
    icon: String, // Название иконки или null
    label: String, // Текст кнопки или null
    type: String, // Типовая кнопка (например, "Ок", "Сохранить") или null
  },
  computed: {
    buttonData() {
      if (this.type && this.presetButtons[this.type]) {
        return this.presetButtons[this.type]; // Если передан тип, берем предустановленные данные
      }
      return {
        icon: this.icon || null,
        iconFallback: this.icon ? "" : "🔘", // Фолбэк символ, если иконки нет
        label: this.label || "",
      };
    },
  },
  data() {
    return {
      presetButtons: {
        "Ок": { icon: "../assets/icons/ok.png", label: "Ок" },
        "Отмена": { icon: "../assets/icons/cancel.png", label: "Отмена" },
        "Сохранить": { icon: "../assets/icons/save.png", label: "Сохранить" },
        "Удалить": { icon: "../assets/icons/x.png", label: "Удалить" },
        "Изменить": { icon: "../assets/icons/edit.svg", label: "Изменить" },
        "Добавить": { icon: "../assets/icons/plus.png", label: "Добавить" },
        "Да": { icon: "../assets/icons/checked.png", label: "Да" },
        "Нет": { icon: "../assets/icons/x.png", label: "Нет" },
      },
    };
  },
  methods: {
    getIconPath(icon) {
      return `/icons/${icon}`; // Пути к изображениям хранятся в папке /public/icons/
    },
  },
};
</script>

<style scoped>
.app-action-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border: none;
  background-color: #007bff;
  color: white;
  cursor: pointer;
  border-radius: 5px;
  transition: 0.3s;
}

.app-action-button:hover {
  background-color: #0056b3;
}

.icon {
  width: 20px;
  height: 20px;
}

.icon-text {
  font-size: 18px;
}

.label {
  font-size: 14px;
}
</style>
