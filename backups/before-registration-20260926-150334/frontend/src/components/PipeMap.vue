<script setup>
import { ref } from "vue";
defineProps({
  pipes: { type: Array, default: () => [] },
  selectedId: String,
  filters: Object,
});
const emit = defineEmits(["pipe-select"]);
const showLabels = ref(true);
const colors = { 高: "#ff806c", 中: "#edc36b", 低: "#48cbb0" };
</script>
<template>
  <div class="map-toolbar">
    <span class="map-caption"
      ><i class="live-dot"></i>管网示意 · GIS 待接入</span
    ><label><input type="checkbox" v-model="showLabels" /> 管段编号</label>
  </div>
  <svg
    class="network-map"
    viewBox="0 0 760 520"
    role="group"
    aria-label="虚构管网占位图，可点击或使用 Tab 和回车选择管段"
  >
    <defs>
      <pattern id="grid" width="38" height="38" patternUnits="userSpaceOnUse">
        <path
          d="M 38 0 L 0 0 0 38"
          fill="none"
          stroke="#173044"
          stroke-width=".6"
        />
      </pattern>
      <filter id="glow"><feGaussianBlur stdDeviation="4" /></filter>
    </defs>
    <rect width="760" height="520" fill="url(#grid)" />
    <path
      d="M-30 115 C180 60 135 300 390 290 S610 440 800 365"
      fill="none"
      stroke="#153c50"
      stroke-width="57"
      opacity=".6"
    />
    <path
      d="M-30 115 C180 60 135 300 390 290 S610 440 800 365"
      fill="none"
      stroke="#245268"
      stroke-width="1"
      stroke-dasharray="7 8"
    />
    <g class="blocks" fill="#102a38" stroke="#1e3e4f">
      <path
        d="M78 57h102v46H78z M288 42h90v53h-90z M490 69h132v55H490z M83 345h88v86H83z M280 342h98v58h-98z M535 385h88v62h-88z"
      />
    </g>
    <text x="332" y="281" class="river-label">示 意 水 系</text>
    <g
      v-for="pipe in pipes"
      :key="pipe.pipe_id"
      role="button"
      tabindex="0"
      :aria-label="pipe.pipe_id + ' ' + pipe.risk_level + '风险，查看详情'"
      :aria-pressed="selectedId === pipe.pipe_id"
      @click="emit('pipe-select', pipe.pipe_id)"
      @keydown.enter.prevent="emit('pipe-select', pipe.pipe_id)"
      @keydown.space.prevent="emit('pipe-select', pipe.pipe_id)"
      class="pipe-hit"
    >
      <path
        v-if="selectedId === pipe.pipe_id"
        :d="pipe.demo_path"
        :stroke="colors[pipe.risk_level]"
        stroke-width="13"
        fill="none"
        filter="url(#glow)"
        opacity=".5"
      />
      <path
        :d="pipe.demo_path"
        stroke="transparent"
        stroke-width="22"
        fill="none"
      />
      <path
        :d="pipe.demo_path"
        :stroke="colors[pipe.risk_level]"
        :stroke-width="selectedId === pipe.pipe_id ? 5 : 2.8"
        fill="none"
        stroke-linecap="round"
      />
      <circle
        :cx="pipe.demo_label[0]"
        :cy="pipe.demo_label[1]"
        :r="selectedId === pipe.pipe_id ? 5 : 3"
        :fill="colors[pipe.risk_level]"
        stroke="#081522"
        stroke-width="2"
      />
      <text
        v-if="showLabels"
        :x="pipe.demo_label[0] + 8"
        :y="pipe.demo_label[1] - 9"
        class="pipe-label"
        :class="{ selected: selectedId === pipe.pipe_id }"
      >
        {{ pipe.pipe_id }}
      </text>
    </g>
    <g transform="translate(713 30)">
      <path d="M0 0l-7 22 7-5 7 5z" fill="#8fb2c4" />
      <text x="-4" y="-7" fill="#8fb2c4" font-size="11">N</text>
    </g>
    <text
      v-if="!pipes.length"
      x="380"
      y="245"
      text-anchor="middle"
      fill="#c2d8e3"
    >
      当前筛选条件下没有管段
    </text>
  </svg>
  <div class="map-footer">
    <div class="legend">
      <span v-for="r in ['高', '中', '低']" :key="r"
        ><i :style="{ background: colors[r] }"></i>{{ r }}风险</span
      >
    </div>
    <span>非真实地理位置 · 无比例尺</span>
  </div>
</template>
