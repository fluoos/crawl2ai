import { reactive, ref } from 'vue';

export function usePagination(fetchFunction, defaultPageSize = 10) {
  const loading = ref(false);
  const dataList = ref([]);
  const pagination = reactive({
    current: 1,
    pageSize: defaultPageSize,
    total: 0,
    showSizeChanger: true,
    showTotal: (total) => `共 ${total} 条`
  });

  const fetchData = async (params = {}) => {
    loading.value = true;
    try {
      const response = await fetchFunction({
        page: pagination.current,
        pageSize: pagination.pageSize,
        ...params
      });
      
      if (response) {
        dataList.value = response.data || [];
        pagination.total = response.total || 0;
      }
      return response;
    } catch (error) {
      console.error('获取数据失败:', error);
      dataList.value = [];
      pagination.total = 0;
    } finally {
      loading.value = false;
    }
  };

  const handleTableChange = (pag) => {
    pagination.current = pag.current;
    pagination.pageSize = pag.pageSize;
    fetchData();
  };

  return {
    loading,
    dataList,
    pagination,
    fetchData,
    handleTableChange
  };
} 