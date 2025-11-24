import { defineStore } from 'pinia'
import axios from 'axios'
// Универсальный сериализатор и вьюха
// Путь к сериализатору /list+depth=ddd - выдает полный список элементов справочника, где ddd - глубина вложенности, дополнительное поле model_name - название модели
// Путь к сериализатору /list+depth=ddd+?filter= - выдает список элементов справочника, где ddd - глубина вложенности, отобранных по заданным полям filter
// в поле filter передается название поля и отбираемое значение. Отбираемых значений может быть несколько
// /form-structure - выдает структуру справочника в виде id, название поля (fieldName), тип поля (fieldType). Если тип поля - NestedSerializer, то возвращает название модели этого поля
// /id=pk выдает значения элементов справочника вида value  - значение поля, название поля (fieldName), тип поля (fieldType)

import {API_URL} from "@/config/api.js"

export const useDataStore = defineStore('data', {
  state: () => ({
    companiesTable: [],
    requestTypesTable: [],
    requestStatusTable: [],
    isLoading: false,
    error: null
  }),
  actions: {
    async fetchInitialData() {
      this.isLoading = true
      // console.log('store.js-Начало загрузки данных this.isLoading:', this.isLoading)
      this.error = null
      try {
        const [companiesRes, requestTypesRes, requestStat] = await Promise.all([
          axios.get(`${API_URL}/api/clients/companies-list/`),
          axios.get(`${API_URL}/api/client_requests/clientrequesttypelist/`),
          axios.get(`${API_URL}/api/client_requests/client-requests-status/`)
        ])
        this.companiesTable = companiesRes.data.results
        this.requestTypesTable = requestTypesRes.data.results
        this.requestStatusTable = requestStat.data.results
        // console.log('store.js-Данные загружены this.isLoading:', this.isLoading)
        this.isLoading = false
        // console.log('store.js-Данные загружены this.isLoading:', this.isLoading)
      } catch (err) {
        this.error = err.message
        console.error('store.js-Ошибка загрузки данных:', err)
      } finally {
        this.isLoading = false
        // console.log('store.js- Загрузка данных завершена this.isLoading:', this.isLoading)
      }
    }
  }

})
