<!-- shared/components/catalog/EngineerSelection.vue -->
<!-- DEBUG: EngineerSelection -->
<template>
  <div class="engineer-selection">
    <span class="debug-tag" v-if="debug">EngineerSelection</span>
    <PageTitle :title="labels.title" />
    <div class="search-bar" v-if="withSearch"><input v-model="search" :placeholder="labels.searchPlaceholder||'Поиск...'" @input="onSearchInput" /></div>
    <EngineerFilterBar
      v-if="filtersLoaded"
      :filters="filterData"
      :show-compatible="showCompatible"
      :show-compatible-toggle="showCompatibleAvailable"
      @change="onFilterChange"
      @reset="resetFilters"
      @toggle-compatible="toggleCompatible"
    />
    <main class="main">
        <SelectionResultGrid
          :items="items"
          :compatible-items="compatibleData"
          :total="total"
          :loading="loading"
          :results-label="labels.resultsLabel || 'Найдено:'"
          :empty-text="labels.emptyLabel || 'Ничего не найдено'"
          mode="offset"
          :offset="offset"
          :limit="limit"
          :split-mode="splitFilter"
          main-title="🎯 Точно подходят"
          @select="id => $emit('select', id)"
          @offset-change="goPage"
        />
    </main>
  </div>
</template>
<script setup>
import { onMounted } from 'vue'
import { debug } from '@/shared/config'
import PageTitle from '@/shared/components/PageTitle.vue'
import EngineerFilterBar from '@/shared/components/catalog/EngineerFilterBar.vue'
import EngineerProductCard from '@/shared/components/catalog/EngineerProductCard.vue'
import SelectionResultGrid from '@/shared/components/catalog/SelectionResultGrid.vue'
import { useCatalog } from '@/shared/composables/useCatalog.js'
const props = defineProps({ api:{type:Object,required:true}, labels:{type:Object,default:()=>({})}, withSearch:{type:Boolean,default:true}, fixedParams:{type:[Object,Function],default:null}, presetFilters:{type:Object,default:null} })
defineEmits(['select', 'navigate'])
const { items,compatibleData,total,exactTotal,compatibleTotal,splitFilter,loading,limit,offset, filterData,filtersLoaded,showCompatibleAvailable,showCompatible,search, activeFilters, loadFilters,fetchData, onFilterChange,toggleCompatible,resetFilters, onSearchInput,goPage } = useCatalog(props.api,{ mode:'engineer', withSearch:props.withSearch, fixedParams:props.fixedParams })
onMounted(async()=>{
  await loadFilters()
  if (props.presetFilters) {
    for (const [k, v] of Object.entries(props.presetFilters)) { activeFilters[k] = v }
  }
  fetchData()
})
</script>
<style scoped>
.engineer-selection{max-width:1200px;margin:0 auto;padding:var(--cat-gap-xl,16px)} .search-bar{margin-bottom:20px} .search-bar input{width:100%;padding:12px 16px;font-size:var(--cat-text-lg,16px);border:1px solid var(--cat-border,#d1d5db);border-radius:var(--cat-radius-lg,8px);background:var(--cat-surface,#fff);outline:none;color:var(--cat-text,#1f2937)} .search-bar input:focus{border-color:var(--cat-primary,#2563eb);box-shadow:0 0 0 3px rgba(37,99,235,.1)} .main{max-width:100%}
</style>
