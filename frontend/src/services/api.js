import axios from 'axios';
import {API_URL} from '../config/api'


const api = axios.create({
  baseURL: 'http://127.0.0.1:8000/api/',  // URL вашего DRF API
  timeout: 5000,
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer YOUR_TOKEN',  // Если используется аутентификация
  },
});

export default api;


export const fetchActuators = async () => {
  const urlstr = `${API_URL}/api/electric_actuators/actual-actuator/`;
  console.log('вызвана fetchActuators')
  console.log(urlstr)
  const response = await axios.get(urlstr);
  return response.data;
};

export const deleteActuators = async (ids) => {
  await axios.post(`${API_URL}/api/electric_actuators/actual-actuator/delete/`, { ids });
};

export const copyActuators = async (ids) => {
  // Преобразуем массив ids в строку и вставляем его в URL
  const idsString = ids.join(','); // Преобразуем массив в строку, например: "1,2,3"
  await axios.post(`${API_URL}/api/electric_actuators/actual-actuator/${idsString}/copy/`);
};

export const fetchModelLines = async () => {
  const response = await axios.get(`${API_URL}/api/electric_actuators/model-lines/`);
  return response.data;
};

export const fetchVoltages = async () => {
  const response = await axios.get(`${API_URL}/api/params/power-types/`);
  return response.data;
};

export const fetchModels = async (lineId, voltageId) => {
  const response = await axios.get(`${API_URL}/api/electric_actuators/model-data/`, {
    params: { model_line: lineId, voltage: voltageId }
  });
  return response.data;
};



export const processStringWithModelName = async (data) => {
  const response = await axios.post(`${API_URL}/api/process-string-with-model-name/`, data);
  return response.data;
};