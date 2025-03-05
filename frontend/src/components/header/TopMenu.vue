<template>
  <div class="w3-bar teal">
    <a href="/drive-selection" class="w3-bar-item w3-button">Подбор электропривода</a>
    <a href="/cable-gland-edit" class="w3-bar-item w3-button">Подбор кабельного ввода</a>
    <a href="/client-requests" class="w3-bar-item w3-button">Запросы клиентов</a>

    <div class="w3-dropdown-hover ">
      <button class="w3-button">Редактирование справочников</button>
      <div class="w3-dropdown-content w3-bar-block teal w3-card-4">
        <a href="/drive-data" class="w3-bar-item w3-button ">Данные приводов</a>
        <a href="/ett-decode" class="w3-bar-item w3-button ">Расшифровка ЕТТ</a>
        <a href="/cable-gland-body-material-edit" class="w3-bar-item w3-button">Редактирование материала кабельных вводов</a>
        <a href="/cable-input-data" class="w3-bar-item w3-button">Данные по кабельным вводам</a>
        <a href="/adaptation-data" class="w3-bar-item w3-button">Данные по адаптации</a>
      </div>
    </div>
  </div>
</template>

<!--<template>-->
<!--  <div class="w3-bar w3-light-grey">-->
<!--    <router-link to="/drive-selection" class="w3-bar-item w3-button">Подбор электропривода</router-link>-->
<!--    <router-link to="/cable-gland-edit" class="w3-bar-item w3-button">Подбор кабельного ввода</router-link>-->

<!--    <div class="w3-dropdown-click">-->
<!--      <button class="w3-bar-item w3-button">Редактирование справочников</button>-->
<!--      <div class="w3-dropdown-content w3-bar-block w3-card-4">-->
<!--        <router-link to="/drive-data" class="w3-bar-item w3-button">Данные приводов</router-link>-->
<!--        <router-link to="/cable-gland-body-material-edit" class="w3-bar-item w3-button">Редактирование материала кабельных вводов</router-link>-->
<!--        <router-link to="/cable-input-data" class="w3-bar-item w3-button">Данные по кабельным вводам</router-link>-->
<!--        <router-link to="/adaptation-data" class="w3-bar-item w3-button">Данные по адаптации</router-link>-->
<!--      </div>-->
<!--    </div>-->
<!--  </div>-->
<!--</template>-->

<script>
export default {
  name: "TopMenu",
};
</script>

<style >

</style>
