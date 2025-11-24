import os
import logging
import hashlib
from typing import Optional , Dict , Any
from django.core.files import File
from . import get_storage

logger = logging.getLogger('storage_manager')


class FileService :
    """
    Единый сервис для операций с файлами
    """

    def __init__(self , storage=None) :
        self.storage = storage or get_storage()
        logger.debug("FileService инициализирован")

    def upload_file(self , instance , file_obj , category='files') :
        """
        Загрузка файла через менеджер хранилища
        """
        logger.info(f"FileService.upload_file начат")
        logger.debug(f"instance: {instance}, file_obj: {file_obj}, category: {category}")

        try :
            # Генерируем имя файла через storage
            filename = self.storage.generate_filename(instance , file_obj.name , category)
            logger.debug(f"Сгенерировано имя файла: {filename}")

            # Сохраняем файл
            result = self.storage.save(filename , file_obj)
            logger.info(f"Файл успешно загружен: {result}")
            return result

        except Exception as e :
            logger.error(f"Ошибка в FileService.upload_file: {str(e)}" , exc_info=True)
            raise

    def get_file_info(self , file_path) -> Optional[Dict[str , Any]] :
        """
        Получение полной информации о файле
        """
        logger.info(f"Запрос информации о файле: {file_path}")

        try :
            if not file_path or not self.file_exists(file_path) :
                logger.debug(f"Файл не существует или путь пустой: {file_path}")
                return None

            info = {
                'path' : file_path ,
                'name' : os.path.basename(file_path) ,
                'size' : self.get_file_size(file_path) ,
                'url' : self.get_file_url(file_path) ,
                'exists' : True ,
                'hash' : self.calculate_file_hash(file_path) ,
            }

            logger.debug(f"Информация о файле: {info}")
            return info

        except Exception as e :
            logger.error(f"Ошибка при получении информации о файле {file_path}: {str(e)}")
            return None

    def get_file_url(self , file_path) -> Optional[str] :
        """
        Получение URL файла
        """
        logger.debug(f"Запрос URL для файла: {file_path}")

        try :
            url = self.storage.url(file_path)
            logger.debug(f"Получен URL: {url}")
            return url
        except Exception as e :
            logger.error(f"Ошибка при получении URL для файла {file_path}: {str(e)}")
            return None

    def delete_file(self , file_path) -> bool :
        """
        Удаление файла
        """
        logger.info(f"Попытка удаления файла: {file_path}")

        try :
            if self.file_exists(file_path) :
                self.storage.delete(file_path)
                logger.info(f"Файл успешно удален: {file_path}")
                return True
            else :
                logger.warning(f"Файл не существует, удаление невозможно: {file_path}")
                return False

        except Exception as e :
            logger.error(f"Ошибка при удалении файла {file_path}: {str(e)}" , exc_info=True)
            return False

    def file_exists(self , file_path) -> bool :
        """
        Проверка существования файла
        """
        if not file_path :
            return False

        logger.debug(f"Проверка существования файла: {file_path}")

        try :
            exists = self.storage.exists(file_path)
            logger.debug(f"Файл {file_path} существует: {exists}")
            return exists
        except Exception as e :
            logger.error(f"Ошибка при проверке существования файла {file_path}: {str(e)}")
            return False

    def get_file_size(self , file_path) -> int :
        """
        Получение размера файла в байтах
        """
        logger.debug(f"Запрос размера файла: {file_path}")

        try :
            if self.file_exists(file_path) :
                size = self.storage.size(file_path)
                logger.debug(f"Размер файла {file_path}: {size} байт")
                return size
            else :
                logger.warning(f"Файл не существует, размер недоступен: {file_path}")
                return 0
        except Exception as e :
            logger.error(f"Ошибка при получении размера файла {file_path}: {str(e)}")
            return 0

    def calculate_file_hash(self , file_path , algorithm='md5') -> Optional[str] :
        """
        Вычисляет хеш файла
        """
        if not self.file_exists(file_path) :
            return None

        logger.debug(f"Вычисление хеша {algorithm} для файла: {file_path}")

        try :
            hash_obj = hashlib.new(algorithm)
            with self.storage.open(file_path , 'rb') as f :
                for chunk in iter(lambda : f.read(4096) , b"") :
                    hash_obj.update(chunk)

            file_hash = hash_obj.hexdigest()
            logger.debug(f"Хеш файла {file_path}: {file_hash}")
            return file_hash
        except Exception as e :
            logger.error(f"Ошибка при вычислении хеша файла {file_path}: {str(e)}")
            return None

    def copy_file(self , source_path , target_instance , target_category='files') :
        """
        Копирование файла с генерацией нового имени
        """
        logger.info(f"Копирование файла: {source_path} -> {target_category}")

        try :
            if not self.file_exists(source_path) :
                error_msg = f"Файл не найден: {source_path}"
                logger.error(error_msg)
                raise FileNotFoundError(error_msg)

            # Открываем исходный файл
            with self.storage.open(source_path , 'rb') as source_file :
                # Создаем объект File для передачи в storage
                django_file = File(source_file , name=os.path.basename(source_path))

                # Загружаем как новый файл с генерацией имени
                result = self.upload_file(target_instance , django_file , target_category)
                logger.info(f"Файл успешно скопирован: {source_path} -> {result}")
                return result

        except Exception as e :
            logger.error(f"Ошибка при копировании файла {source_path}: {str(e)}" , exc_info=True)
            raise

    def move_file(self , source_path , target_instance , target_category='files') :
        """
        Перемещение файла с последующим удалением оригинала
        """
        logger.info(f"Перемещение файла: {source_path} -> {target_category}")

        try :
            new_path = self.copy_file(source_path , target_instance , target_category)
            self.delete_file(source_path)
            logger.info(f"Файл успешно перемещен: {source_path} -> {new_path}")
            return new_path
        except Exception as e :
            logger.error(f"Ошибка при перемещении файла {source_path}: {str(e)}")
            raise

    def cleanup_orphaned_files(self , used_file_paths , storage_prefix='') :
        """
        Очистка неиспользуемых файлов
        """
        logger.info(f"Очистка orphaned файлов, префикс: {storage_prefix}")

        try :
            # Для локального хранилища
            if hasattr(self.storage , 'listdir') :
                all_files , _ = self.storage.listdir(storage_prefix)
                orphaned_files = set(all_files) - set(used_file_paths)

                deleted_count = 0
                for file_path in orphaned_files :
                    if self.delete_file(file_path) :
                        deleted_count += 1

                logger.info(f"Удалено orphaned файлов: {deleted_count}")
                return deleted_count

            return 0
        except Exception as e :
            logger.error(f"Ошибка при очистке orphaned файлов: {str(e)}")
            return 0


# Глобальный экземпляр сервиса
file_service = FileService()