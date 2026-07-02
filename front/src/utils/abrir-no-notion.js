/**
 * Abre a página (nota) da tarefa no Notion, em uma nova aba.
 *
 * A `url` vem do contrato da API (link da página no Notion). Quando ausente,
 * não faz nada — o chamador deve evitar oferecer a ação nesse caso.
 */
export function abrirNoNotion(tarefa) {
  if (!tarefa?.url) return
  window.open(tarefa.url, '_blank', 'noopener,noreferrer')
}
