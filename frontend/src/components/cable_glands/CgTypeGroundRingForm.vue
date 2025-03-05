<template>
  <div>
    <div class="form-group">
      <label for="name">Имя</label>
      <input v-model="formData.name" id="name" type="text" class="form-control" placeholder="Введите имя" required>
    </div>

    <div class="form-group">
      <label for="modelLine">Модель линии</label>
      <select v-model="formData.modelLine" class="form-control" id="modelLine" required>
        <option v-for="line in modelLines" :key="line.id" :value="line.id">{{ line.name }}</option>
      </select>
    </div>

    <div class="form-group">
      <label for="bodyMaterial">Материал корпуса</label>
      <select v-model="formData.cableGlandBodyMaterial" class="form-control" id="bodyMaterial" required>
        <option v-for="material in bodyMaterials" :key="material.id" :value="material.id">{{ material.name }}</option>
      </select>
    </div>

    <div class="form-group">
      <label for="dnMetalSleeve">Диаметр металлорукава</label>
      <input v-model="formData.dnMetalSleeve" id="dnMetalSleeve" type="number" class="form-control" placeholder="Диаметр металлорукава">
    </div>
  </div>
</template>

<script>
export default {
  props: {
    formData: Object,
    modelLines: Array,
    bodyMaterials: Array
  }
};
</script>
