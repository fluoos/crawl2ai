<template>
  <div class="link-list">
    <div class="list-header">
      <h3>已爬取链接列表</h3>
      <a-button 
        type="primary" 
        @click="$emit('refresh-all')" 
        :loading="refreshLoading"
      >
        重新获取所有链接
      </a-button>
    </div>
    
    <a-table :dataSource="links" :columns="columns" rowKey="id" :loading="loading">
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'action'">
          <a-button type="link" @click="$emit('view', record)">查看</a-button>
          <a-button type="link" @click="$emit('refresh', record)" :loading="record.refreshing">
            重新获取
          </a-button>
        </template>
      </template>
    </a-table>
  </div>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue';

defineProps({
  links: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  refreshLoading: {
    type: Boolean,
    default: false
  }
});

defineEmits(['view', 'refresh', 'refresh-all']);

const columns = [
  {
    title: 'URL',
    dataIndex: 'url',
    key: 'url',
  },
  {
    title: '深度',
    dataIndex: 'depth',
    key: 'depth',
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
  },
  {
    title: '操作',
    key: 'action',
  }
];
</script>

<style scoped>
.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  margin-top: 24px;
}
</style> 