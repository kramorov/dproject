/**
 * useCatalogWizard — unified wizard adapter (graph or flat).
 *
 * Usage:
 *   const { type, config } = await useCatalogWizard('pneumatic_fittings')
 *
 * Returns:
 *   type: 'graph' → config.entry_node_id, config.entry_options, config.graph_json, ...
 *   type: 'flat' → config.wizard_id, config.pages, config.filters, ...
 */
import api from '@/shared/api'

export async function useCatalogWizard(code) {
  const { data } = await api.get(`/core/catalog-wizard/${code}/`)
  return data
}
