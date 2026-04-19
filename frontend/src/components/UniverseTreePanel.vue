<template>
  <div class="tree-panel-wrap">
    <header v-if="universe" class="tree-header">
      <span class="tree-seal" aria-hidden="true">目</span>
      <div class="tree-meta">
        <div class="tree-label">批注索引</div>
        <div class="tree-hint">
          <template v-if="nodeCount > 0">本卷 {{ nodeCount }} 条批注</template>
          <template v-else>尚无批注 · 从右侧开笔</template>
        </div>
      </div>
    </header>
    <div ref="container" class="tree-panel">
      <div v-if="!treeData" class="placeholder">
        <div class="placeholder-dots" aria-hidden="true">⋯</div>
        <p>开始推演后<br/>分叉树将在此显示</p>
      </div>
      <svg v-else ref="svgEl" class="tree-svg" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  treeData: { type: Object, default: null },
  selectedNodeId: { type: Number, default: null },
  universe: { type: Object, default: null },
})

const nodeCount = computed(() => {
  if (!props.treeData) return 0
  let n = 0
  ;(function walk(node) {
    if (node.node_type !== 'root') n++
    node.children?.forEach(walk)
  })(props.treeData)
  return n
})

const emit = defineEmits(['select-node', 'node-delete-request'])

const container = ref(null)
const svgEl = ref(null)
let resizeObserver = null

// 通过 getComputedStyle 读取 design token，支持主题切换
function getToken(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim()
}
function buildColors() {
  return {
    link:         getToken('--c-border-sepia'),
    nodeStroke:   getToken('--c-ivory-aged'),
    nodeDefault:  getToken('--c-umber-deep'),
    nodeSelected: getToken('--c-oxblood'),
    nodeBranch:   getToken('--c-tarnished-gold'),
    nodeDelete:   getToken('--c-oxblood'),
    textDefault:  getToken('--c-umber'),
    textMuted:    getToken('--c-sepia'),
  }
}
let C = {}

onMounted(() => {
  resizeObserver = new ResizeObserver(() => { if (props.treeData) renderTree() })
  if (container.value) resizeObserver.observe(container.value)
})

onUnmounted(() => resizeObserver?.disconnect())

watch(() => [props.treeData, props.selectedNodeId], async () => {
  if (props.treeData) { await nextTick(); renderTree() }
}, { deep: true })

function renderTree() {
  if (!svgEl.value || !container.value || !props.treeData) return
  C = buildColors()  // 每次渲染重新读取 token，支持主题切换

  const W = container.value.clientWidth
  const H = container.value.clientHeight
  const m = { top: 48, right: 120, bottom: 48, left: 110 }

  const root = d3.hierarchy(props.treeData)
  // 用 nodeSize 保证每个节点有固定间距，避免节点数多时水平方向塌陷
  // nodeSize([垂直间距, 水平列距])：160px 列距确保 10 字标签不重叠
  const tree = d3.tree().nodeSize([36, 160])
  tree(root)

  // 计算实际垂直范围，居中显示
  let minX = Infinity, maxX = -Infinity
  root.each(d => { if (d.x < minX) minX = d.x; if (d.x > maxX) maxX = d.x })
  const centerOffset = (H - m.top - m.bottom - (maxX - minX)) / 2 - minX + m.top

  const svg = d3.select(svgEl.value)
  svg.selectAll('*').remove()
  svg.attr('width', W).attr('height', H)
    .attr('role', 'group')
    .attr('aria-label', '宇宙分叉树')

  const g = svg.append('g').attr('transform', `translate(${m.left},${centerOffset})`)

  svg.call(
    d3.zoom()
      .scaleExtent([0.2, 2.5])
      .on('zoom', e => g.attr('transform', e.transform))
  )

  // Links
  g.selectAll('.link')
    .data(root.links())
    .join('path')
    .attr('fill', 'none')
    .attr('stroke', C.link)
    .attr('stroke-width', 1.5)
    .attr('d', d3.linkHorizontal().x(d => d.y).y(d => d.x))

  // Nodes
  const node = g.selectAll('.node')
    .data(root.descendants())
    .join('g')
    .attr('transform', d => `translate(${d.y},${d.x})`)
    .attr('role', 'button')
    .attr('tabindex', '0')
    .attr('aria-label', d => {
      const action = d.data.protagonist_action ? `：${d.data.protagonist_action.substring(0, 25)}` : ''
      return `第${d.data.turn_number}回${action}`
    })
    .attr('aria-pressed', d => d.data.id === props.selectedNodeId ? 'true' : 'false')
    .style('cursor', 'pointer')
    .on('click', (_, d) => emit('select-node', d.data.id))
    .on('contextmenu', (event, d) => {
      event.preventDefault()
      emit('node-delete-request', d.data.id)
    })
    .on('keydown', (event, d) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault()
        emit('select-node', d.data.id)
      }
      if (event.key === 'Delete') {
        event.preventDefault()
        emit('node-delete-request', d.data.id)
      }
    })

  // Node circles
  node.append('circle')
    .attr('r', d => d.data.id === props.selectedNodeId ? 8 : 5)
    .attr('fill', d => nodeColor(d.data))
    .attr('stroke', C.nodeStroke)
    .attr('stroke-width', 2)

  // Branch indicator ring for nodes with branches
  node.filter(d => d.data.branch_prompt)
    .append('circle')
    .attr('r', 9)
    .attr('fill', 'none')
    .attr('stroke', C.nodeBranch)
    .attr('stroke-width', 1)
    .attr('stroke-dasharray', '3 2')

  // Hover 删除按钮（非根节点显示，hover 时可见）
  const deleteBtn = node.filter(d => d.data.node_type !== 'root')
    .append('g')
    .attr('class', 'delete-btn')
    .attr('transform', 'translate(10, -10)')
    .attr('role', 'button')
    .attr('tabindex', '-1')
    .attr('aria-label', '删除节点')
    .style('opacity', 0)
    .style('cursor', 'pointer')
    .on('click', (event, d) => {
      event.stopPropagation()
      emit('node-delete-request', d.data.id)
    })

  deleteBtn.append('circle')
    .attr('r', 7)
    .attr('fill', C.nodeDelete)
    .attr('stroke', C.nodeStroke)
    .attr('stroke-width', 1.5)

  deleteBtn.append('path')
    .attr('d', 'M-3,-3 L3,3 M3,-3 L-3,3')
    .attr('stroke', 'white')
    .attr('stroke-width', 1.5)
    .attr('stroke-linecap', 'round')

  // Hover 显示/隐藏删除按钮
  node.on('mouseenter', function() {
    d3.select(this).select('.delete-btn').style('opacity', 1)
  })
  node.on('mouseleave', function() {
    d3.select(this).select('.delete-btn').style('opacity', 0)
  })

  // Labels · 统一居节点下方居中，避免左右溢出 panel
  const labels = node.append('text')
    .attr('x', 0)
    .attr('dy', '1.6em')
    .attr('text-anchor', 'middle')
    .style('font-family', 'var(--font-serif)')
    .style('font-size', '10px')
    .style('letter-spacing', '0.02em')
    .style('fill', d => d.data.id === props.selectedNodeId ? C.nodeSelected : C.textDefault)
    .style('font-weight', d => d.data.id === props.selectedNodeId ? '600' : '400')
    .text(d => truncate(d.data.label, 8))

  // SVG <title> 提供完整名 on hover（被截断时才加）
  labels.filter(d => (d.data.label?.length || 0) > 8)
    .append('title')
    .text(d => d.data.label)
}

function nodeColor(data) {
  if (data.id === props.selectedNodeId) return C.nodeSelected
  if (data.children && data.children.length > 1) return C.nodeBranch
  return C.nodeDefault
}
function truncate(s, n) { return s?.length > n ? s.slice(0, n) + '…' : s || '' }
</script>

<style scoped>
.tree-panel-wrap {
  width: 100%; height: 100%;
  display: flex; flex-direction: column;
  overflow: hidden;
}
.tree-header {
  display: flex; align-items: center; gap: var(--sp-3);
  padding: var(--sp-3) var(--sp-5);
  border-bottom: 1px solid var(--c-border-archive);
  flex-shrink: 0;
  background: rgba(232, 223, 200, 0.4);
}
.tree-seal {
  display: inline-flex; align-items: center; justify-content: center;
  width: 22px; height: 22px;
  background: var(--c-oxblood);
  color: var(--c-ivory-aged);
  font-family: var(--font-serif-alt);
  font-size: 12px;
  font-weight: 600;
  border-radius: 2px;
  box-shadow: var(--shadow-oxblood-seal);
  flex-shrink: 0;
}
.tree-meta { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.tree-label {
  font-family: var(--font-serif-alt);
  font-size: 14px;
  font-weight: 500;
  color: var(--c-umber-deep);
  letter-spacing: 0.04em;
  line-height: 1;
}
.tree-hint {
  font-family: var(--font-serif);
  font-style: italic;
  font-size: 11px;
  color: var(--c-sepia);
}
.tree-panel {
  width: 100%;
  flex: 1;
  position: relative;
  background: transparent;
  overflow: hidden;
}

.placeholder {
  position: absolute; inset: 0;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: var(--sp-3); text-align: center;
}
.placeholder-dots {
  font-size: 32px;
  color: var(--c-tarnished-gold);
  letter-spacing: 6px;
  opacity: 0.5;
}
.placeholder p {
  font-family: var(--font-serif);
  font-style: italic;
  font-size: 13px;
  color: var(--c-sepia);
  line-height: 1.7;
  max-width: 180px;
}

.tree-svg { width: 100%; height: 100%; overflow: visible; }
</style>
