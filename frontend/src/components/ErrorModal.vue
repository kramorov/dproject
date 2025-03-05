<template>
  <div v-if="visible" class="modal-overlay">
    <div class="modal">
      <div class="modal-content">
        <p>{{ message }}</p>
        <button @click="closeModal">OK</button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    message: String,  // Текст ошибки, который будет отображаться
    visible: Boolean, // Состояние видимости модального окна
  },
  methods: {
    closeModal() {
      this.$emit('close'); // Событие для закрытия модального окна
    }
  }
};
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
}

.modal {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  width: 300px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.modal-content p {
  margin: 0;
  font-size: 16px;
}

button {
  margin-top: 20px;
  background-color: #007bff;
  color: #fff;
  padding: 10px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
}

button:hover {
  background-color: #0056b3;
}
</style>
