<template>
  <div>
    <h3>Справочник имен:</h3>
    <ul>
      <li v-for="(value, key) in dictionary" :key="key">
        {{ key }}: {{ value }}
      </li>
    </ul>
  </div>
</template>

<script>
export default {
  name: 'Dictionary',
  data() {
    return {
      dictionary: {
        mounting_plate_types_update: 'mounting-plate-types-update',
        mounting_plate_types_list: 'mounting-plate-types-list',
        power_types_create: 'power-types-create',
      },
    };
  },
};
</script>
