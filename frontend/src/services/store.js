import Vue from 'vue';
import Vuex from 'vuex';
import axios from 'axios';

Vue.use(Vuex);

export default new Vuex.Store({
  state: {
    parameters: {},  // Здесь будут храниться все параметры
    loading: false,  // Состояние загрузки
    error: null,     // Ошибки
  },
  mutations: {
    SET_PARAMETERS(state, parameters) {
      state.parameters = parameters;
    },
    SET_LOADING(state, loading) {
      state.loading = loading;
    },
    SET_ERROR(state, error) {
      state.error = error;
    },
  },
  actions: {
    // Загрузка всех параметров
    async fetchParameters({ commit }) {
      commit('SET_LOADING', true);
      try {
        const response = await axios.get('/api/params/parameters/');  // Эндпоинт для загрузки параметров
        commit('SET_PARAMETERS', response.data);
        commit('SET_ERROR', null);
      } catch (error) {
        commit('SET_ERROR', 'Ошибка при загрузке параметров');
      } finally {
        commit('SET_LOADING', false);
      }
    },
  },
});