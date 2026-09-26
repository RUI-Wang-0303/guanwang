<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import PipeMap from "./components/PipeMap.vue";
const data = ref(null),
  loading = ref(false),
  error = ref(""),
  selectedId = ref(""),
  selection = ref([]),
  notice = ref("");
const filters = reactive({ q: "", risk: "", material: "", min_diameter: 300 });
const applied = ref("");
const active = computed(() =>
  data.value?.pipes.find((p) => p.pipe_id === selectedId.value),
);
const colors = { 高: "#ff806c", 中: "#edc36b", 低: "#48cbb0" };
const ring = computed(() => {
  const d = data.value?.summary.distribution || { 高: 0, 中: 0, 低: 0 },
    total = d.高 + d.中 + d.低;
  if (!total) return "#203443";
  const a = (d.高 / total) * 100,
    b = ((d.高 + d.中) / total) * 100;
  return (
    "conic-gradient(#ff806c 0% " +
    a +
    "%,#edc36b " +
    a +
    "% " +
    b +
    "%,#48cbb0 " +
    b +
    "% 100%)"
  );
});
const materials = computed(() => {
  const groups = {};
  for (const p of data.value?.pipes || [])
    groups[p.material] = (groups[p.material] || 0) + 1;
  return Object.entries(groups).sort((a, b) => b[1] - a[1]);
});
// 点击“应用筛选”后，请求后端；统计、地图和列表一起使用返回结果。
async function load() {
  loading.value = true;
  error.value = "";
  notice.value = "";
  const query = new URLSearchParams({ ...filters });
  try {
    const res = await fetch("/api/dashboard?" + query);
    if (!res.ok) throw new Error("接口返回 " + res.status);
    const next = await res.json();
    data.value = next;
    applied.value = query.toString();
    if (!next.pipes.some((p) => p.pipe_id === selectedId.value))
      selectedId.value = next.pipes[0]?.pipe_id || "";
    selection.value = selection.value.filter((id) =>
      next.pipes.some((p) => p.pipe_id === id),
    );
  } catch (e) {
    error.value = "加载失败：" + e.message + "。请确认后端已启动，再重试。";
  } finally {
    loading.value = false;
  }
}
function reset() {
  Object.assign(filters, { q: "", risk: "", material: "", min_diameter: 300 });
  load();
}
function addActive() {
  if (active.value && !selection.value.includes(active.value.pipe_id))
    selection.value.push(active.value.pipe_id);
  notice.value = "已加入排查清单，可在下方列表查看并导出。";
}
// 导出使用上次成功应用的筛选，避免输入框未提交时导错数据。
async function download() {
  try {
    const query = new URLSearchParams(applied.value);
    if (selection.value.length) query.set("ids", selection.value.join(","));
    const res = await fetch("/api/export?" + query);
    if (!res.ok) throw new Error("导出失败");
    const url = URL.createObjectURL(await res.blob()),
      a = document.createElement("a");
    a.href = url;
    a.download = "演示排查清单.csv";
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    notice.value = "排查清单已导出（包含演示数据标识）。";
  } catch (e) {
    notice.value = e.message + "，请确认后端连接。";
  }
}
onMounted(load);
</script>
<template>
  <div class="app-shell">
    <header class="header">
      <div class="brand">
        <div class="brand-symbol">≈</div>
        <div>
          <span class="eyebrow">WATER NETWORK / RISK INTELLIGENCE</span>
          <h1>大口径供水管网<span>安全风险评估</span></h1>
        </div>
      </div>
      <div class="header-meta">
        <span class="demo-badge">演示数据</span
        ><span class="version">DEMO / V0.1</span>
      </div>
    </header>
    <div class="context-bar">
      <div>
        <i class="live-dot"></i>风险总览 <span class="divider">/</span
        ><span class="muted">管段分析与排查决策</span>
      </div>
      <span class="muted"
        >评估时间 {{ data?.meta.as_of || "—" }} ·
        {{ data?.meta.model_version || "结果待加载" }}</span
      >
    </div>
    <div class="demo-banner">
      当前为界面开发演示：管段、风险分数与建议均为虚构样例；地图为可替换占位组件，非真实
      GIS 数据。
    </div>
    <form class="filters" @submit.prevent="load">
      <label class="search-label"
        ><span>搜索管段</span
        ><input
          v-model="filters.q"
          placeholder="输入编号或道路名称"
          maxlength="100" /></label
      ><label
        ><span>风险等级</span
        ><select v-model="filters.risk">
          <option value="">全部等级</option>
          <option>高</option>
          <option>中</option>
          <option>低</option>
        </select></label
      ><label
        ><span>管材</span
        ><select v-model="filters.material">
          <option value="">全部管材</option>
          <option v-for="m in data?.filters.materials" :key="m">{{ m }}</option>
        </select></label
      ><label
        ><span>最小管径</span
        ><select v-model.number="filters.min_diameter">
          <option :value="300">DN300</option>
          <option :value="500">DN500</option>
          <option :value="800">DN800</option>
          <option :value="1000">DN1000</option>
        </select></label
      ><button class="primary" :disabled="loading">
        {{ loading ? "加载中…" : "应用筛选" }}</button
      ><button type="button" class="quiet" @click="reset" :disabled="loading">
        重置
      </button>
    </form>
    <div v-if="error" role="alert" class="error">
      {{ error }} <button @click="load">重试</button>
    </div>
    <main v-if="data" class="dashboard" :aria-busy="loading">
      <aside class="left-stack">
        <section class="panel">
          <h2><span>管网概况</span><small>当前筛选</small></h2>
          <div class="metric-main">
            <strong>{{ data.summary.count }}</strong
            ><span>管段 / 条</span>
          </div>
          <div class="metric-pair">
            <div>
              <b class="coral">{{ data.summary.high_count }}</b
              ><span>高风险管段</span>
            </div>
            <div>
              <b>{{ data.summary.length_km.toFixed(2) }}</b
              ><span>管线总长 / km</span>
            </div>
          </div>
        </section>
        <section class="panel">
          <h2>风险等级分布<small>规则分级 · 演示</small></h2>
          <div class="distribution">
            <div
              class="donut"
              :style="{ background: ring }"
              role="img"
              :aria-label="
                '风险分布：高' +
                data.summary.distribution.高 +
                '，中' +
                data.summary.distribution.中 +
                '，低' +
                data.summary.distribution.低
              "
            >
              <div>
                <strong>{{ data.summary.count }}</strong
                ><span>已评估管段</span>
              </div>
            </div>
            <div class="distribution-values">
              <div v-for="r in ['高', '中', '低']" :key="r">
                <span
                  ><i :style="{ background: colors[r] }"></i>{{ r }}风险</span
                ><b>{{ data.summary.distribution[r] }}</b>
              </div>
            </div>
          </div>
        </section>
        <section class="panel material-panel">
          <h2>管材分布<small>条</small></h2>
          <div v-if="!materials.length" class="muted">暂无匹配数据</div>
          <div v-for="[m, n] in materials" :key="m" class="material-row">
            <div>
              <span>{{ m }}</span
              ><b>{{ n }}</b>
            </div>
            <div class="bar-track">
              <i
                :style="{
                  width: (n / Math.max(data.summary.count, 1)) * 100 + '%',
                }"
              ></i>
            </div>
          </div>
        </section>
        <section class="panel model-panel">
          <h2>模型验证</h2>
          <div class="pending">待队友提供评估结果</div>
          <p>高风险识别效果、测试集指标及基线对比将在模型交付后接入。</p>
        </section>
      </aside>
      <section class="panel map-panel">
        <h2>管网空间总览<small>二维交互占位</small></h2>
        <PipeMap
          :pipes="data.pipes"
          :selected-id="selectedId"
          :filters="filters"
          @pipe-select="selectedId = $event"
        />
        <div class="map-selection">
          <span class="muted">当前选择</span
          ><b>{{ active?.pipe_id || "暂无管段" }}</b
          ><span>{{ active?.road || "调整筛选条件后重试" }}</span
          ><span class="map-hint">点击管线查看右侧详情</span>
        </div>
      </section>
      <aside class="right-stack">
        <section class="panel detail-panel">
          <h2>
            管段风险档案<small>{{ active ? "已选中" : "待选择" }}</small>
          </h2>
          <template v-if="active"
            ><div class="detail-heading">
              <div>
                <strong>{{ active.pipe_id }}</strong>
                <p>{{ active.road }}</p>
              </div>
              <span
                class="risk-pill"
                :style="{
                  color: colors[active.risk_level],
                  borderColor: colors[active.risk_level] + '55',
                }"
                >{{ active.risk_level }}风险</span
              >
            </div>
            <div class="score">
              <b :style="{ color: colors[active.risk_level] }">{{
                active.risk_score
              }}</b
              ><span>/ 100 <small>演示风险分 · 非概率</small></span>
            </div>
            <dl>
              <div>
                <dt>管径</dt>
                <dd>DN{{ active.diameter_mm }}</dd>
              </div>
              <div>
                <dt>管材</dt>
                <dd>{{ active.material }}</dd>
              </div>
              <div>
                <dt>管龄</dt>
                <dd>{{ active.age_years }} 年</dd>
              </div>
              <div>
                <dt>长度</dt>
                <dd>{{ active.length_m }} m</dd>
              </div>
            </dl></template
          >
          <p v-else class="empty">没有可查看的管段</p>
        </section>
        <section class="panel">
          <h2>风险影响因素<small>示例解释</small></h2>
          <template v-if="active"
            ><div v-for="(f, i) in active.factors" :key="f" class="factor">
              <span class="factor-dot"></span><span>{{ f }}</span>
            </div>
            <p class="footnote">
              示例说明用于展示解释区域，不代表已证实的事故原因。
            </p></template
          >
          <p v-else class="empty">请选择管段</p>
        </section>
        <section class="panel recommendation">
          <h2>排查建议<small>待业务复核</small></h2>
          <template v-if="active"
            ><p>{{ active.recommendation }}</p>
            <button
              class="primary full"
              @click="addActive"
              :disabled="selection.includes(active.pipe_id)"
            >
              {{
                selection.includes(active.pipe_id)
                  ? "已加入排查清单"
                  : "＋ 加入排查清单"
              }}
            </button></template
          >
          <p v-else class="empty">请选择管段</p>
        </section>
      </aside>
      <section class="panel table-panel">
        <h2>
          <span>管段优先排查列表 <small>按演示风险分降序</small></span
          ><button
            class="quiet export-button"
            @click="download"
            :disabled="!data.pipes.length || loading"
          >
            {{
              selection.length
                ? "导出已选 " + selection.length + " 条"
                : "导出当前结果"
            }}
          </button>
        </h2>
        <div class="table-scroll">
          <table>
            <thead>
              <tr>
                <th>选择</th>
                <th>管段编号</th>
                <th>所在道路</th>
                <th>管径</th>
                <th>管材</th>
                <th>风险分</th>
                <th>等级</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="p in data.pipes"
                :key="p.pipe_id"
                :class="{ active: selectedId === p.pipe_id }"
              >
                <td>
                  <input
                    type="checkbox"
                    v-model="selection"
                    :value="p.pipe_id"
                    :aria-label="'加入清单 ' + p.pipe_id"
                  />
                </td>
                <td class="mono">{{ p.pipe_id }}</td>
                <td>{{ p.road }}</td>
                <td>DN{{ p.diameter_mm }}</td>
                <td>{{ p.material }}</td>
                <td class="mono" :style="{ color: colors[p.risk_level] }">
                  {{ p.risk_score }}
                </td>
                <td>
                  <span
                    class="level-dot"
                    :style="{ background: colors[p.risk_level] }"
                  ></span
                  >{{ p.risk_level }}
                </td>
                <td>
                  <button
                    class="text-button"
                    @click="selectedId = p.pipe_id"
                    :aria-label="'查看 ' + p.pipe_id"
                  >
                    查看详情 ↗
                  </button>
                </td>
              </tr>
              <tr v-if="!data.pipes.length">
                <td colspan="8" class="empty">
                  没有匹配管段，请调整筛选条件。
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </main>
    <div v-else-if="loading" class="initial-loading">正在连接演示数据服务…</div>
    <div v-if="notice" class="toast" role="status">
      {{ notice }}<button @click="notice = ''">关闭</button>
    </div>
    <footer>
      <span>管网安全风险评估与决策 · 竞赛演示原型</span
      ><span>数据来源：本地虚构样例 · 原始竞赛数据未接入</span>
    </footer>
  </div>
</template>
