<template>
  <header class="edit-item">
    <slot name="description">{{description}} </slot>
    <slot name="value">{{value}} </slot>
  </header>
</template>

<script>

export default {
  props: ["description", "value"],
 /* components: {Icon}, */
  name: "EditListItem.vue"
}
</script>

<style scoped>
.edit-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background-color: #333;
  color: #fff;
  padding: 10px 20px;
}
</style>