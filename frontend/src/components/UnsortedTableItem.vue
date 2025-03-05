<template>
  <tr
    :class="{'w3-light-green selected': isSelected}"
    @click="toggle"
    class="w3-hoverable"
  >
    <td v-for="column in columns" :key="column.key" class="w3-padding">
      {{ actuator[column.field] }}
    </td>
  </tr>
</template>

<script>
export default {
  name: 'UnsortedTableItem',
  props: {
    actuator: Object,         // Один актюатор (строка)
    columns: Array,           // Колонки с ключами и названиями
    isSelected: Boolean       // Строка выделена или нет
  },
  methods: {
    toggle() {
      this.$emit('toggleSelection', this.actuator.id);  // Эмиттируем событие выбора строки
    }
  }
};
</script>

<style scoped>
.selected {
  background-color: #e0f7fa;
}
</style>
