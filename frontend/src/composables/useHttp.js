import { ref } from 'vue';
import axios from 'axios';

export function useHttp() {
  const get = async (url) => {
    const response = await axios.get(url);
    return response.data;
  };

  const post = async (url, data) => {
    const response = await axios.post(url, data);
    return response.data;
  };

  const put = async (url, data) => {
    const response = await axios.put(url, data);
    return response.data;
  };

  const del = async (url) => {
    await axios.delete(url);
  };

  return {
    get,
    post,
    put,
    del,
  };
}