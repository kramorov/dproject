<template>
  <table class="w3-table w3-bordered w3-striped">
    <thead>
      <tr>
        <th
          v-for="column in columns"
          :key="column.key" class="w3-hover-shadow-small">
          {{ column.title }}
        </th>
      </tr>
    </thead>
    <tbody>
      <UnsortedTableItem
        v-for="actuator in actuators"
        :key="actuator.id"
        :actuator="actuator"
        :columns="columns"
        :isSelected="selectedRows.includes(actuator.id)"
        @toggleSelection="toggleSelection" class="w3-hover-shadow-small"
      />
    </tbody>
  </table>
</template>

<script>
import UnsortedTableItem from './UnsortedTableItem.vue';

export default {
  name: 'UnsortedTable',
  components: { UnsortedTableItem },
  props: {
    actuators: Array,         // Данные актюаторов
    columns: Array,           // Массив колонок с названием и ключом для полей
    selectedRows: Array       // Список выбранных строк
  },
  methods: {
    toggleSelection(id) {
      this.$emit('toggleSelection', id);  // Эмиттируем событие в родительский компонент
    }
  }
};
</script>
