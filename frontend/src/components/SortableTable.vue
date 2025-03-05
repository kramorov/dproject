<template>
  <div class="list-container">
    <table>
      <thead>
        <tr>
          <th v-for="(column, index) in columns" :key="index" @click="sortTable(column.field)">
            {{ column.title }}
            <span v-if="sortField === column.field">
              <span v-if="sortOrder === 'asc'">↑</span>
              <span v-if="sortOrder === 'desc'">↓</span>
            </span>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in sortedData" :key="item.id"
            :class="{'selected': selectedRows.includes(item.id)}"
            @click="toggleSelection(item.id)">
          <td v-for="(column, index) in columns" :key="index">{{ item[column.field] }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
export default {
  props: {
    data: {
      type: Array,
      required: true
    },
    columns: {
      type: Array,
      required: true
    },
    selectedRows: {
      type: Array,
      required: true
    }
  },
  data() {
    return {
      sortField: this.columns[0].field, // По умолчанию сортируем по первому столбцу
      sortOrder: 'asc', // Начальный порядок сортировки
    };
  },
  computed: {
    sortedData() {
      return this.data.sort((a, b) => {
        let comparison = 0;

        if (a[this.sortField] > b[this.sortField]) {
          comparison = 1;
        } else if (a[this.sortField] < b[this.sortField]) {
          comparison = -1;
        }

        return this.sortOrder === 'asc' ? comparison : -comparison;
      });
    }
  },
  methods: {
    toggleSelection(id) {
      this.$emit('update:selectedRows', this.selectedRows.includes(id)
        ? this.selectedRows.filter(rowId => rowId !== id)
        : [...this.selectedRows, id]);
    },
    sortTable(field) {
      if (this.sortField === field) {
        // Если нажали на тот же заголовок, меняем порядок сортировки
        this.sortOrder = this.sortOrder === 'asc' ? 'desc' : 'asc';
      } else {
        // Если новый заголовок, сортируем по нему по возрастанию
        this.sortField = field;
        this.sortOrder = 'asc';
      }
    }
  }
};
</script>

<style scoped>
table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  padding: 10px;
  border: 1px solid #ddd;
  text-align: left;
}

th {
  cursor: pointer;
  background-color: #f4f4f4;
}

.selected {
  background-color: #e0f7fa;
}
</style>
