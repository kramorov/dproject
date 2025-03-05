<template>
  <div class="w3-modal" style="display: block">
    <div class="w3-modal-content w3-card-4 w3-animate-zoom">
      <header class="w3-container w3-teal">
        <span @click="close" class="w3-button w3-display-topright">&times;</span>
        <h2>Редактировать запрос</h2>
      </header>
      <div class="w3-container">
        <!-- Форма редактирования -->
        <form @submit.prevent="save">
          <label>Код:</label>
          <input
            class="w3-input"
            type="text"
            v-model="request.symbolic_code"
          />

          <label>Тип запроса:</label>
          <input class="w3-input" type="text" v-model="request.request_type" />

          <button type="submit" class="w3-button w3-green w3-margin-top">
            Сохранить
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    request: {
      type: Object,
      required: true,
    },
  },
  emits: ['close'],
  setup(props, { emit }) {
    const close = () => {
      emit('close');
    };

    const save = () => {
      // Логика сохранения изменений
      console.log('Сохранено:', props.request);
      close();
    };

    return {
      close,
      save,
    };
  },
};
</script>