<template>
  <div class="mounting-plate-types">
    <h1>Типы монтажных площадок</h1>
    <ul>
      <li v-for="plate in plates" :key="plate.id">
        {{ plate.symbolic_code }}
      </li>
    </ul>
  </div>
</template>

<script>
export default {
  data() {
    return {
      plates: [],
    };
  },
  mounted() {
    this.fetchMountingPlateTypes();
  },
  methods: {
    async fetchMountingPlateTypes() {
      try {
        const response = await fetch('http://localhost:8000/api/params/mounting-plate-types/list');
        if (response.ok) {
          this.plates = await response.json();
        } else {
          console.error('Ошибка при загрузке данных');
        }
      } catch (error) {
        console.error('Ошибка сети:', error);
      }
    }
  }
};
</script>

<style scoped>
.mounting-plate-types {
  padding: 20px;
}
ul {
  list-style-type: none;
  padding: 0;
}
li {
  margin-bottom: 10px;
  font-size: 16px;
}
</style>
