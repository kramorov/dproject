<template>
  <button>
    <Icon v-if="showIcon" />
    {{text}}
  </button>
</template>

<script>
import Icon from "Icon"
export default {
  props: ["text", "showIcon"],
  components: {Icon},
  name: "AppButton.vue"
}
</script>

<style scoped>

</style>