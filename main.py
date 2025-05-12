import requests
from terminaltables import AsciiTable
import time
from dotenv import load_dotenv
import os


def print_salary_statistics(statistics, title):
    vacancy_statistics_table = [['Язык программирования', 'Найдено вакансий', 'Обработано вакансий', 'Средняя зарплата']]
    for language, salary_statistics in statistics.items():
        vacancy_statistics_table.append([
            language,
            salary_statistics['vacancies_found'],
            salary_statistics['vacancies_processed'],
            salary_statistics['average_salary']
        ])
    table = AsciiTable(vacancy_statistics_table, title)
    print(table.table)


def get_superjob_statistics(programming_languages, headers_superjob, superjob_page_count):
    salary_statistics = {}
    for language in programming_languages:
        url = 'https://api.superjob.ru/2.0/vacancies/'
        page = 0
        total_vacancies_found = 0
        total_vacancies_processed = 0
        total_salary = 0

        while True:
            params = {
                'keyword': language,
                'page': page,
                'count': superjob_page_count
            }

            print(f"Загрузка вакансий для языка: {language}, страница: {page}")
            response = requests.get(url, headers=headers_superjob, params=params, verify=False)

            if response.ok:
                pass

            superjob_response = response.json()

            if 'objects' not in superjob_response or not superjob_response['objects']:
                break

            for vacancy in superjob_response['objects']:
                total_vacancies_processed += 1
                total_vacancies_found = superjob_response['total']

                salary_from = vacancy.get('payment_from', 0)
                salary_to = vacancy.get('payment_to', 0)
                average_salary = calculate_average_salary(salary_from, salary_to)

                total_salary += average_salary

            page += 1

        if total_vacancies_processed:
            average_salary = int(total_salary / total_vacancies_processed)
        else:
            average_salary = 0

        salary_statistics[language] = {
            "vacancies_found": total_vacancies_found,
            "vacancies_processed": total_vacancies_processed,
            "average_salary": average_salary
        }

    return salary_statistics


def predict_rub_salary_hh(vacancy):
    salary = vacancy.get('salary')
    if not salary or salary['currency'] != 'RUR':
        return None

    from_salary = salary.get('from')
    to_salary = salary.get('to')

    return calculate_average_salary(from_salary, to_salary) * 1.2 if from_salary else \
           calculate_average_salary(from_salary, to_salary) * 0.8 if to_salary else None


def get_hh_statistics(programming_languages, area_moscow,vacancies_per_page,headers_hh):
    salary_statistics = {}
    for language in programming_languages:
        url = f"https://api.hh.ru/vacancies"
        params = {
            'area': area_moscow,  # Москва
            'text': language,
            'per_page': vacancies_per_page,  # Количество вакансий на странице
            'page': 0  # Начальная страница
        }

        vacancies_found = 0
        vacancies_processed = 0
        total_salary = 0

        initial_response = requests.get(url, params=params, headers=headers_hh, verify=False)
        initial_response.raise_for_status()
        initial_data = initial_response.json()
        vacancies_found = initial_data['found']

        # Определяем количество страниц
        pages_number = (vacancies_found // 20) + (1 if vacancies_found % 20 > 0 else 0)

        print(f"Найдено вакансий: {vacancies_found}, страниц: {pages_number}")

        page = 0
        while page < pages_number:
            print(f"Загрузка {language}, страница {page + 1} из {pages_number}")

            # Обновляем параметры для текущей страницы
            params['page'] = page
            page_response = requests.get(url, params=params, headers=headers_hh, verify=False)

            # Проверка на ошибки
            try:
                page_response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                print(f"Ошибка при загрузке страницы {page + 1}: {e}")
                break  # Прерываем цикл, если произошла ошибка

            page_payload = page_response.json()

            # Обрабатываем вакансии на текущей странице
            for vacancy in page_payload['items']:
                expected_salary = predict_rub_salary_hh(vacancy)
                if expected_salary is not None:
                    total_salary += expected_salary
                    vacancies_processed += 1

            page += 1
            time.sleep(1)  # Задержка между запросами

        if vacancies_processed > 0:
            average_salary = int(total_salary / vacancies_processed)
        else:
            average_salary = 0

        salary_statistics[language] = {
            "vacancies_found": vacancies_found,
            "vacancies_processed": vacancies_processed,
            "average_salary": average_salary
        }

    return salary_statistics
    

def calculate_average_salary(salary_from, salary_to):
    if salary_from and salary_to:
        return (salary_from + salary_to) / 2
    elif salary_from:
        return salary_from
    elif salary_to:
        return salary_to
    return 0


def main():

    load_dotenv()
    superjob_api_key = os.getenv('SUPERJOB_API_KEY')
    area_moscow = 1 
    vacancies_per_page = 20
    superjob_page_count = 100
    
    programming_languages = [
        "JavaScript", "Java", "Python", "Ruby",
        "PHP", "C++", "C#", "Go"
    ]

    headers_superjob = {
        'X-Api-App-Id': superjob_api_key,
    }
    
    headers_hh = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    hh_statistics = get_hh_statistics(programming_languages, area_moscow,vacancies_per_page, headers_hh)
    superjob_statistics = get_superjob_statistics(programming_languages, headers_superjob, superjob_page_count)

    print_salary_statistics(hh_statistics, 'HeadHunter Moscow')
    print_salary_statistics(superjob_statistics, 'SuperJob Moscow')


if __name__ == "__main__":
    main()
