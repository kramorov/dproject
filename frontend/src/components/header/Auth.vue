<template>
  <div >
    <router-link to="/login" class="w3-bar-item w3-button">Вход</router-link>
    <router-link to="/register" class="w3-bar-item w3-button">Регистрация</router-link>
  </div>
</template>

<script>
export default {
  name: "Auth",
};
</script>

<style >
/*.auth {*/
/*  flex: 1;*/
/*  display: flex;*/
/*  justify-content: flex-end;*/
/*  align-items: center;*/
/*}*/

/*.auth a {*/
/*  color: #fff;*/
/*  text-decoration: none;*/
/*  margin-left: 10px;*/
/*  padding: 5px 10px;*/
/*  transition: color 0.3s;*/
/*}*/

/*.auth a:hover {*/
/*  color: #ccc;*/
/*}*/
</style>
