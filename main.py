import os
import requests
import re
import datetime
import sys


def get_data(url):
    try:
        response = requests.get(url)
    except requests.exceptions.ConnectionError:
        print('Произошла ошибка подключения. Выполнение программы прервано')
        sys.exit()
    except requests.exceptions.Timeout:
        print('Истекло время ожидания ответа от сервера. Выполнение программы прервано')
        sys.exit()
    except requests.exceptions.URLRequired:
        print('Введен недействительный URL. Выполнение программы прервано')
        sys.exit()
    except requests.exceptions.TooManyRedirects:
        print('Слишком много перенаправлений. Выполнение программы прервано')
        sys.exit()
    except requests.exceptions.ContentDecodingError:
        print('Не удалось декодировать содержимое ответа. Выполнение программы прервано')
        sys.exit()
    except requests.exceptions.RequestException:
        print('Не удалось подключиться к серверу. Выполнение программы прервано')
        sys.exit()

    return response.json()



def crop_str(str):
    if len(str) > 48:
        return f'{str[:48]}...\n'
    return f'{str}\n'


def create_file(data_todo, user):
    # Списки завершенных и незавершенных задач
    user_task_completed = []
    user_task_uncompleted = []
    # Дабы постоянно не повторять конструкцию .get('username') сразу сохраним в переменную
    username = user.get('username')

    # Проход циклом для поиска действий определенного пользователя
    for task in data_todo:
        if task.get('userId') == user.get('id'):
            if task['completed']:
                user_task_completed.append(crop_str(task['title']))
            else:
                user_task_uncompleted.append(crop_str(task['title']))

    # Для минимизации количества процессов записи в файл, изначально данные будут записываться в переменную
    writing_data = f'Отчет для: {user.get("company").get("name")}.\n' \
                   f'{user.get("name")} <{user.get("email")}> {datetime.datetime.now().strftime("%d.%m.%Y %H:%M")}\n'

    # Проверки на пустоту списков задач:
    # 1. Если отсутствуют любые задачи
    if user_task_completed or user_task_uncompleted:
        writing_data += f'Всего задач: {len(user_task_completed) + len(user_task_uncompleted)}\n \n'

        # 2. Если отсутствуют завыершенные задачи
        if user_task_completed:
            writing_data += f'Завершенные задачи({len(user_task_completed)}):\n' \
                            f'{"".join(user_task_completed)}\n'
        else:
            writing_data += 'У пользователя отсутствуют выполненные задачи\n'

        # 3. Если отсутствуют незавершенные задачи
        if user_task_uncompleted:
            writing_data += f'Незавершенные задачи({len(user_task_uncompleted)}):\n' \
                            f'{"".join(user_task_uncompleted)}\n'
        else:
            writing_data += 'У пользователя отсутствуют незавершенные задачи задачи\n'

    else:
        writing_data += 'У пользователя отсутствуют любые задачи\n'

    try:
        # Создаем новый отчет с префиксом new для последующей подмены
        with open(f'{username}_new.txt', 'w+') as user_file:
            # Записываем в отчет данные
            user_file.write(writing_data)
            # Жестко записываем его
            os.fsync(user_file)

        # Переименовываем старый отчет при его наличии
        if os.path.isfile(f'{username}.txt'):
            # Достаем дату его создания из файла с помощью регулярного выражения
            pattern = r'\d{2}.\d{2}.\d{4} \d{2}:\d{2}'
            with open(f'{username}.txt') as file:
                date_str = re.findall(pattern, file.readlines()[1])[0]
                date_datetime = datetime.datetime.strptime(date_str, "%d.%m.%Y %H:%M").strftime("%Y-%m-%dT%H:%M")

            # Переименовываем старый отчет с добавлением даты его создания
            os.rename(f'{username}.txt', f'old_{username}_{date_datetime}.txt')

        # У нового отчета убираем постфикс new
        os.rename(f'{username}_new.txt', f'{username}.txt')

    except:
        # В случае, если переименование старого отчета произошло, а создание нового - нет
        # Возвращаем старому отчету прежнее название
        if not os.path.isfile(f'{username}.txt'):
            os.rename(f'{username}_{date_datetime}.txt', f'{username}.txt')

        # В случае, если исключение произошло после создания нового отчета,
        # но до или во время его переименования, удаляем его
        if os.path.isfile(f'{username}_new.txt'):
            os.remove(f'{username}_new.txt')

        print('Произошел сбой записи/переименования файлов (Обновление разрешено не чаще, чем раз в минуту)')


def main():
    url_todos = 'https://json.medrating.org/todos'
    url_users = 'https://json.medrating.org/users'

    data_todo = get_data(url_todos)
    data_users = get_data(url_users)

    # Создаем папку в случае её отсутствия и переходим в неё
    if not os.path.isdir('tasks'):
        os.mkdir('tasks')
    os.chdir('tasks')

    # Проход по всем пользователям. Предполагается, что каждая запись - уникальный пользователь,
    # а также все поля словаря пользователей заполненны корректно
    for user in data_users:
        create_file(data_todo, user)


if __name__ == "__main__":
    main()
