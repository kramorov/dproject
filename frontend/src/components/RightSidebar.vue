<template>
  <aside class="right-sidebar">
    <div class="filters">
      <h2>Фильтры</h2>
      <p>Делайте что хотите: Разместите здесь фильтры или другой контент.</p>
    </div>
  </aside>
</template>

<script>
export default {
  name: "RightSidebar",
};
</script>

<style scoped>
.right-sidebar {
  width: 300px;
  background-color: #f8f9fa;
  padding: 20px;
  border-left: 1px solid #ddd;
  /* Убедитесь, что элемент находится справа */
  order: 2; /* Панель будет отображаться справа в flex-контейнере */
}

.filters {
  background-color: #ffffff;
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.filters h2 {
  font-size: 1.5rem;
  margin-bottom: 10px;
}
</style>
