// src/services/apiErrorHandler.js
export function handleApiError(error) {
  let errorMessage = 'Неизвестная ошибка';
  console.log("apiErrorHandler. Ошибка перехвачена:", error);
  // Проверка ошибок сети
  if (error.code === "ERR_NETWORK") {
    errorMessage = "Ошибка сети! Сервер недоступен.";}
  else if (error.code === "ERR_CONNECTION_REFUSED") {
    errorMessage = "Ошибка сети! Сервер недоступен. Отказано в подключении к серверу. Возможно, он не отвечает.";
  }
  // Проверка на ошибки от сервера (например, код 404, 500 и другие)
  else if (error.response) {
    const status = error.response.status;
    switch (status) {
      case 400:
        errorMessage = "Ошибка запроса. Невалидные данные.";
        break;
      case 401:
        errorMessage = "Ошибка авторизации. Пожалуйста, войдите в систему.";
        break;
      case 404:
        errorMessage = "Ресурс не найден.";
        break;
      case 500:
        errorMessage = "Ошибка сервера. Попробуйте позже.";
        break;
      default:
        errorMessage = `Ошибка: ${status} - ${error.response.statusText}`;
        break;
    }
  }
  // Прочие ошибки
  else {
    errorMessage = `Ошибка: ${error.message}`;
  }

  return errorMessage;
}
