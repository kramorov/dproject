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
      <label for="threadA">Резьба A</label>
      <select v-model="formData.threadA" class="form-control" id="threadA" required>
        <option v-for="thread in threadSizes" :key="thread.id" :value="thread.id">{{ thread.size }}</option>
      </select>
    </div>

    <div class="form-group">
      <label for="threadB">Резьба B</label>
      <select v-model="formData.threadB" class="form-control" id="threadB" required>
        <option v-for="thread in threadSizes" :key="thread.id" :value="thread.id">{{ thread.size }}</option>
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
    bodyMaterials: Array
  }
};
</script>
