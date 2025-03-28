<template>
  <div class="data-table">
    <div class="table-header" v-if="$slots.header">
      <slot name="header"></slot>
    </div>
    
    <a-table
      :columns="columns"
      :data-source="dataSource"
      :pagination="pagination"
      :loading="loading"
      :row-key="rowKey"
      :row-selection="rowSelection"
      @change="handleTableChange"
    >
      <template #headerCell="{ column }">
        <slot :name="`header-${column.dataIndex}`" :column="column">
          {{ column.title }}
        </slot>
      </template>
      
      <template #bodyCell="{ column, record }">
        <slot :name="`body-${column.dataIndex}`" :record="record" :column="column">
          {{ record[column.dataIndex] }}
        </slot>
      </template>
    </a-table>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  columns: {
    type: Array,
    required: true
  },
  dataSource: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  pagination: {
    type: [Object, Boolean],
    default: () => ({
      current: 1,
      pageSize: 10,
      total: 0,
      showSizeChanger: true,
      showTotal: (total) => `共 ${total} 条`
    })
  },
  rowKey: {
    type: [String, Function],
    default: 'id'
  },
  rowSelection: {
    type: Object,
    default: null
  }
});

const emit = defineEmits(['change']);

const handleTableChange = (pagination, filters, sorter) => {
  emit('change', pagination, filters, sorter);
};
</script>

<style scoped>
.data-table {
  width: 100%;
}

.table-header {
  margin-bottom: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style> 