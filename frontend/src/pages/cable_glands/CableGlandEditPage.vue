
// CableGlandEditPage.vue
<template>
  <div class="cable-gland-edit">
    <h1>Редактирование данных по кабельным вводам</h1>
    <div class="filters">
      <label>
        Name:
        <input v-model="filters.name" @input="fetchData" />
      </label>
      <!-- Add other filters here -->
    </div>
    <table>
      <thead>
        <tr>
          <th>Тип</th>
          <th>Артикул</th>
          <th>Производитель</th>
          <th>...</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in items" :key="item.id">
          <td>{{ item.model_line.cable_gland_type.name }}</td>
          <td>{{ item.name }}</td>
          <td>{{ item.model_line.brand.name }}</td>
          <td><AppActionButton type="Изменить" @click="editItem(item.id)" /></td>
          <td><button @click="editItem(item.id)">Edit</button></td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import axios from 'axios';
import {API_URL} from "../../config/api.js";
import AppActionButton from '../../components/AppActionButton.vue';
import ErrorModal from "../../components/ErrorModal.vue";

export default {
    components: {
    ErrorModal,  // Добавляем модальное окно как компонент
    AppActionButton,
  },
  data() {
    return {
      items: [],
      filters: { name: '' },
    };
  },
  methods: {
    fetchData() {
      axios.get(`${API_URL}/cg/cable-glands`, { params: this.filters }).then((response) => {
        this.items = response.data;
        console.log(response.data)
      });
    },
    editItem(id) {
      this.$router.push(`${API_URL}/cg/cable-input-data/edit/${id}`);
    },
  },
  created() {
    this.fetchData();
  },
};
</script>

<style scoped>
.cable-gland-edit {
  padding: 20px;
}
.filters {
  margin-bottom: 20px;
  display: flex;
  gap: 15px;
}
table {
  width: 100%;
  border-collapse: collapse;
}
th, td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
}
</style>
