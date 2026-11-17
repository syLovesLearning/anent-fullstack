<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { createSession, devLogin, loginUser, registerUser, type UserInfo } from './api/client'
import ApiTester from './components/ApiTester.vue'
import ChatWorkspace from './components/ChatWorkspace.vue'
import EvalDashboard from './components/EvalDashboard.vue'
import KnowledgeBase from './components/KnowledgeBase.vue'
import MemoryManager from './components/MemoryManager.vue'
import PlatformOverview from './components/PlatformOverview.vue'
import RetrievalLab from './components/RetrievalLab.vue'
import WorkflowCenter from './components/WorkflowCenter.vue'

type TabKey = 'overview' | 'chat' | 'workflow' | 'mem' | 'lab' | 'kb' | 'eval' | 'api'
const activeTab = ref<TabKey>('overview')
const token = ref('')
const sessionId = ref('')
const currentUser = ref<UserInfo | null>(null)
const initError = ref('')

const showAuthModal = ref(false)
const authMode = ref<'login' | 'register'>('login')
const formUser = ref('')
const formPwd = ref('')
const formRole = ref<'user' | 'admin' | 'readonly' | 'external_guest'>('user')
const formGroups = ref('public,engineering')
const authErr = ref('')

async function applyAuth(auth: { access_token: string; user: UserInfo }) {
  token.value = auth.access_token
  currentUser.value = auth.user
  const sess = await createSession(token.value)
  sessionId.value = sess.id
}

async function quickSwitch(preset: 'admin' | 'eng' | 'guest' | 'ext') {
  initError.value = ''
  try {
    if (preset === 'admin') await applyAuth(await devLogin('shenyang', 'admin', ['public', 'engineering', 'finance']))
    else if (preset === 'eng') await applyAuth(await devLogin('dev_user', 'user', ['public', 'engineering']))
    else if (preset === 'guest') await applyAuth(await devLogin('guest', 'readonly', ['public']))
    else await applyAuth(await devLogin('ext_visitor', 'external_guest', ['public']))
  } catch (err) {
    initError.value = err instanceof Error ? err.message : '切换账号失败'
  }
}

async function submitAuthForm() {
  authErr.value = ''
  try {
    if (authMode.value === 'login') {
      await applyAuth(await loginUser(formUser.value.trim(), formPwd.value))
    } else {
      const groups = formGroups.value.split(',').map((s) => s.trim()).filter(Boolean)
      await applyAuth(await registerUser(formUser.value.trim(), formPwd.value, formRole.value, groups))
    }
    showAuthModal.value = false
    formPwd.value = ''
  } catch (err) {
    authErr.value = err instanceof Error ? err.message : String(err)
  }
}

onMounted(() => quickSwitch('admin'))
</script>

<template>
  <div class="shell">
    <nav class="topbar">
      <div class="brand">
        <strong>透明智能体工作台</strong>
        <template v-if="currentUser">
          <span class="badge badge-ok">{{ currentUser.username }} · {{ currentUser.role }}</span>
          <span class="badge badge-blue">组: {{ currentUser.groups.join(',') }}</span>
        </template>
      </div>

      <div class="tabs">
        <button class="btn" :class="{ 'btn-primary': activeTab === 'overview' }" @click="activeTab = 'overview'">能力全景</button>
        <button class="btn" :class="{ 'btn-primary': activeTab === 'chat' }" @click="activeTab = 'chat'">完整对话</button>
        <button class="btn" :class="{ 'btn-primary': activeTab === 'workflow' }" @click="activeTab = 'workflow'">OA/SRM 流程</button>
        <button class="btn" :class="{ 'btn-primary': activeTab === 'mem' }" @click="activeTab = 'mem'">我的记忆</button>
        <button class="btn" :class="{ 'btn-primary': activeTab === 'lab' }" @click="activeTab = 'lab'">命中透视台</button>
        <button class="btn" :class="{ 'btn-primary': activeTab === 'kb' }" @click="activeTab = 'kb'">知识库管理</button>
        <button class="btn" :class="{ 'btn-primary': activeTab === 'eval' }" @click="activeTab = 'eval'">黄金测试集</button>
        <button class="btn" :class="{ 'btn-primary': activeTab === 'api' }" @click="activeTab = 'api'">接口测试台</button>
      </div>

      <div class="auth-actions">
        <button class="btn" @click="quickSwitch('admin')">切 Admin</button>
        <button class="btn" @click="quickSwitch('eng')">切 研发组</button>
        <button class="btn" @click="quickSwitch('guest')">切 只读</button>
        <button class="btn" @click="quickSwitch('ext')">切 外部访客</button>
        <button class="btn btn-primary" @click="showAuthModal = true">登录/注册</button>
      </div>
    </nav>

    <main class="container">
      <div v-if="initError" class="err-banner">{{ initError }}</div>
      <template v-else-if="token">
        <PlatformOverview v-if="activeTab === 'overview'" @navigate="(t) => (activeTab = t)" />
        <ChatWorkspace v-else-if="activeTab === 'chat'" :token="token" @go-workflow="activeTab = 'workflow'" />
        <WorkflowCenter v-else-if="activeTab === 'workflow'" :token="token" :role="currentUser?.role || 'user'" @go-chat="activeTab = 'chat'" />
        <MemoryManager v-else-if="activeTab === 'mem'" :token="token" />
        <RetrievalLab v-else-if="activeTab === 'lab'" :token="token" />
        <KnowledgeBase v-else-if="activeTab === 'kb'" :token="token" />
        <EvalDashboard v-else-if="activeTab === 'eval'" :token="token" />
        <ApiTester v-else :token="token" :session-id="sessionId" />
      </template>
      <p v-else class="loading">正在初始化鉴权与会话...</p>
    </main>

    <div v-if="showAuthModal" class="modal-mask" @click.self="showAuthModal = false">
      <div class="modal">
        <h3>{{ authMode === 'login' ? '账号密码登录' : '注册新账号（可配角色与分组）' }}</h3>
        <input v-model="formUser" class="m-input" placeholder="用户名" />
        <input v-model="formPwd" type="password" class="m-input" placeholder="密码" />
        <template v-if="authMode === 'register'">
          <select v-model="formRole" class="m-input">
            <option value="user">user (可用 rag_search + memory_save + 流程)</option>
            <option value="readonly">readonly (仅只读查询)</option>
            <option value="external_guest">external_guest (外部访客：公开文档+访客预约)</option>
            <option value="admin">admin (全权限)</option>
          </select>
          <input v-model="formGroups" class="m-input" placeholder="所属分组如 public,engineering" />
        </template>
        <p v-if="authErr" class="err-txt">{{ authErr }}</p>
        <div class="m-actions">
          <button class="btn" @click="authMode = authMode === 'login' ? 'register' : 'login'">
            {{ authMode === 'login' ? '去注册' : '去登录' }}
          </button>
          <button class="btn btn-primary" @click="submitAuthForm">确认</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.topbar {
  background: var(--card); border-bottom: 1px solid var(--border);
  padding: 10px 20px; display: flex; justify-content: space-between; align-items: center; gap: 10px; flex-wrap: wrap;
}
.brand, .tabs, .auth-actions { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.container { max-width: 1280px; margin: 18px auto; padding: 0 18px; }
.err-banner { background: var(--err-soft); color: var(--err); padding: 12px 16px; border-radius: 8px; }
.loading { color: var(--muted); }
.modal-mask { position: fixed; inset: 0; background: rgba(0, 0, 0, 0.35); display: flex; align-items: center; justify-content: center; z-index: 60; }
.modal { background: var(--card); padding: 20px; border-radius: 12px; width: 340px; display: flex; flex-direction: column; gap: 10px; }
.modal h3 { margin: 0 0 4px; font-size: 16px; }
.m-input { padding: 8px 10px; border: 1px solid var(--border); border-radius: 8px; font-size: 13px; }
.m-actions { display: flex; justify-content: space-between; margin-top: 4px; }
.err-txt { color: var(--err); font-size: 12px; margin: 0; }
</style>
