<template>
  <div class="modal-overlay" @click.self="close">
    <div class="modal-content">
      <h3>{{ isNew ? "Создать новый материал" : "Редактировать материал" }}</h3>
      <input v-model="localMaterial.name" placeholder="Название" />
      <input v-model="localMaterial.text_description" placeholder="Описание" />
      <div class="modal-buttons">
        <button @click="save">{{ isNew ? "Создать" : "Сохранить" }}</button>
        <button @click="close">Отмена</button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    material: Object,
  },
  data() {
    return {
      localMaterial: this.material ? { ...this.material } : { name: "", text_description: "" },
    };
  },
  computed: {
    isNew() {
      return !this.material; // Проверяем, создаём ли новый материал
    },
  },
  methods: {
    save() {
      this.$emit("save", this.localMaterial); // Отправляем данные в родительский компонент
    },
    close() {
      this.$emit("close");
    },
  },
};
</script>

<style scoped>
/* Стили остаются такими же */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
}
.modal-content {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
  width: 300px;
  text-align: center;
}
.modal-buttons {
  margin-top: 10px;
  display: flex;
  justify-content: space-between;
}
.modal-buttons button {
  padding: 6px 12px;
  border: none;
  cursor: pointer;
  border-radius: 4px;
  transition: 0.3s;
}
.modal-buttons button:first-of-type {
  background: #4caf50;
  color: white;
}
.modal-buttons button:first-of-type:hover {
  background: #388e3c;
}
.modal-buttons button:last-of-type {
  background: #d32f2f;
  color: white;
}
.modal-buttons button:last-of-type:hover {
  background: #b71c1c;
}
</style>
