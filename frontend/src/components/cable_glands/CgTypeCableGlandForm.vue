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

    <div v-if="formData.modelLine?.for_armored_cable === false">
      <div class="form-group">
        <label for="cableDiameterInnerMin">Минимальный внутренний диаметр</label>
        <input v-model="formData.cableDiameterInnerMin" id="cableDiameterInnerMin" type="number" class="form-control" placeholder="Минимальный внутренний диаметр">
      </div>

      <div class="form-group">
        <label for="cableDiameterInnerMax">Максимальный внутренний диаметр</label>
        <input v-model="formData.cableDiameterInnerMax" id="cableDiameterInnerMax" type="number" class="form-control" placeholder="Максимальный внутренний диаметр">
      </div>
    </div>

    <div v-if="formData.modelLine?.for_metal_sleeve_cable">
      <div class="form-group">
        <label for="dnMetalSleeve">Диаметр металлорукава</label>
        <input v-model="formData.dnMetalSleeve" id="dnMetalSleeve" type="number" class="form-control" placeholder="Диаметр металлорукава">
      </div>
    </div>

    <div class="form-group">
      <label for="threadA">Резьба A</label>
      <select v-model="formData.threadA" class="form-control" id="threadA" required>
        <option v-for="thread in threadSizes" :key="thread.id" :value="thread.id">{{ thread.size }}</option>
      </select>
    </div>

    <div class="form-group">
      <label for="exd_same_as_model_line">Взрывозащита как у модели линии</label>
      <input v-model="formData.exd_same_as_model_line" type="checkbox" id="exd_same_as_model_line">
    </div>

    <div v-if="!formData.exd_same_as_model_line" class="form-group">
      <label for="exd">Степень взрывозащиты</label>
      <select v-model="formData.exd" class="form-control" id="exd" multiple>
        <option v-for="option in exdOptions" :key="option.id" :value="option.id">{{ option.name }}</option>
      </select>
    </div>

    <div class="form-group">
      <label for="parent">Родитель</label>
      <select v-model="formData.parent" class="form-control" id="parent">
        <option v-for="line in modelLines" :key="line.id" :value="line.id">{{ line.name }}</option>
      </select>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    formData: Object,
    modelLines: Array,
    threadSizes: Array,
    bodyMaterials: Array,
    exdOptions: Array
  }
};
</script>
