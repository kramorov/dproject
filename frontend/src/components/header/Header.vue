<template>
<!--  <div id="header" class="w3-container w3-teal">-->
<!--    <div class="w3-cell-row">-->
    <header class="w3-container w3-teal">
      <div class="w3-left">
          <Logo />
      </div>
      <div class="w3-right">
        <TopMenu  />
      </div>
      <div class="w3-right ">
        <Auth />
      </div>
  </header>

</template>

<script>
import Logo from "./Logo.vue";
import TopMenu from "./TopMenu.vue";
import Auth from "./Auth.vue";

export default {
  name: "Header",
  components: {
    Logo,
    TopMenu,
    Auth,
  },
};
</script>

<style scoped>
/*.header {*/
/*  display: flex;*/
/*  align-items: center;*/
/*  justify-content: space-between;*/
/*  background-color: #333;*/
/*  color: #fff;*/
/*  padding: 10px 20px;*/
/*}*/
</style>
