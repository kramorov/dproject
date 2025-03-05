<template>
  <div class="w3-container">
    <!-- Header Section -->
    <header>
      <div class="w3-bar w3-teal">
        <slot name="header"/>
      </div>
    </header>

    <!-- Main Section -->
    <main>
      <div class="w3-container">
        <slot name="main"/>
      </div>
    </main>

    <!-- Footer Section -->
    <footer>
      <div class="w3-bar w3-teal">
        <slot name="footer"/>
      </div>
    </footer>
  </div>
</template>


<script>
export default {
  name: "AppLayout.vue"
}
</script>

<style scoped>

</style>