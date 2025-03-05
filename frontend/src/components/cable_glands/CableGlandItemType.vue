<template>
  <div>
    <h1>Типы кабельных вводов</h1>
    <form @submit.prevent="createCableGlandItemType">
      <input v-model="newType.name" placeholder="Название" />
      <input v-model="newType.text_description" placeholder="Описание" />
      <button type="submit">Создать</button>
    </form>

    <ul>
      <li v-for="type in types" :key="type.id">
        {{ type.name }} - {{ type.text_description }}
        <button @click="deleteType(type.id)">Удалить</button>
        <button @click="editType(type)">Изменить</button>
      </li>
    </ul>

    <div v-if="editingType">
      <h3>Редактировать</h3>
      <input v-model="editingType.name" placeholder="Название" />
      <input v-model="editingType.text_description" placeholder="Описание" />
      <button @click="saveEditedType">Сохранить</button>
      <button @click="cancelEdit">Отменить</button>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      types: [],
      newType: { name: '', text_description: '' },
      editingType: null,
    };
  },
  created() {
    this.fetchTypes();
  },
  methods: {
    fetchTypes() {
      axios.get('/api/cable-gland-item-types/')
        .then(response => {
          this.types = response.data;
        });
    },
    createCableGlandItemType() {
      axios.post('/api/cable-gland-item-types/', this.newType)
        .then(response => {
          this.types.push(response.data);
          this.newType = { name: '', text_description: '' };
        });
    },
    deleteType(id) {
      axios.delete(`/api/cable-gland-item-types/${id}/`)
        .then(() => {
          this.types = this.types.filter(type => type.id !== id);
        });
    },
    editType(type) {
      this.editingType = { ...type };
    },
    saveEditedType() {
      axios.put(`/api/cable-gland-item-types/${this.editingType.id}/`, this.editingType)
        .then(response => {
          const index = this.types.findIndex(type => type.id === this.editingType.id);
          this.types[index] = response.data;
          this.editingType = null;
        });
    },
    cancelEdit() {
      this.editingType = null;
    }
  }
};
</script>

<style scoped>
/* Добавьте стили для компонента */
</style>
