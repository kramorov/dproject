<template>
   <div class="w3-logo">
    <router-link to="/">
      <img src="@/assets/vue.svg" alt="Логотип" class="w3-image" style="width: 30px;">
    </router-link>
  </div>
</template>

<script>
export default {
  name: "Logo",
};
</script>

<style scoped>
/*.logo img {*/
/*  width: 50px;*/
/*  height: 50px;*/
/*  cursor: pointer; !* Указывает, что элемент кликабелен *!*/
/*  transition: transform 0.3s; !* Анимация при наведении *!*/
/*}*/

/*.logo img:hover {*/
/*  transform: scale(1.1); !* Увеличение при наведении *!*/
/*}*/
</style>
