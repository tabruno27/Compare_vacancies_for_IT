import requests
from terminaltables import AsciiTable
import time
from dotenv import load_dotenv
import os


load_dotenv()

SUPERJOB_API_KEY = os.getenv('SUPERJOB_API_KEY')

programming_languages = [
    "JavaScript", "Java", "Python", "Ruby",
    "PHP", "C++", "C#", "Go"
]

headers_superjob = {
    'X-Api-App-Id': SUPERJOB_API_KEY,
}

headers_hh = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def print_salary_statistics(statistics, title):
    table_data = [['Язык программирования', 'Найдено вакансий', 'Обработано вакансий', 'Средняя зарплата']]
    for language, data in statistics.items():
        table_data.append([
            language,
            data['vacancies_found'],
            data['vacancies_processed'],
            data['average_salary']
        ])
    table = AsciiTable(table_data, title)
    print(table.table)

def get_superjob_statistics():
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
                'count': 100
            }

            print(f"Загрузка вакансий для языка: {language}, страница: {page}")
            response = requests.get(url, headers=headers_superjob, params=params, verify=False)
            data = response.json()

            if 'objects' not in data or not data['objects']:
                break

            for vacancy in data['objects']:
                total_vacancies_processed += 1
                total_vacancies_found = data['total']

                if vacancy.get('payment_from') or vacancy.get('payment_to'):
                    salary_from = vacancy.get('payment_from', 0)
                    salary_to = vacancy.get('payment_to', 0)
                    if salary_from and salary_to:
                        average_salary = (salary_from + salary_to) / 2
                    elif salary_from:
                        average_salary = salary_from
                    elif salary_to:
                        average_salary = salary_to
                    else:
                        average_salary = 0

                    total_salary += average_salary

            page += 1

        if total_vacancies_processed > 0:
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
    if salary is None or salary['currency'] != 'RUR':
        return None

    from_salary = salary.get('from')
    to_salary = salary.get('to')

    if from_salary is not None and to_salary is not None:
        return (from_salary + to_salary) / 2
    elif from_salary is not None:
        return from_salary * 1.2
    elif to_salary is not None:
        return to_salary * 0.8
    else:
        return None

def get_hh_statistics():
    salary_statistics = {}
    for language in programming_languages:
        url = f"https://api.hh.ru/vacancies"
        params = {
            'area': 1,
            'text': language,
            'per_page': 20,
            'page': 0
        }

        vacancies_found = 0
        vacancies_processed = 0
        total_salary = 0

        initial_response = requests.get(url, params=params, headers=headers_hh, verify=False)
        initial_response.raise_for_status()
        initial_data = initial_response.json()
        vacancies_found = initial_data['found']

        pages_number = (vacancies_found // 20) + (1 if vacancies_found % 20 > 0 else 0)

        print(f"Найдено вакансий: {vacancies_found}, страниц: {pages_number}")

        page = 0
        while page < pages_number:
            print(f"Загрузка {language}, страница {page + 1} из {pages_number}")

            params['page'] = page
            page_response = requests.get(url, params=params, headers=headers_hh, verify=False)

            try:
                page_response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                print(f"Ошибка при загрузке страницы {page + 1}: {e}")
                break

            page_payload = page_response.json()

            for vacancy in page_payload['items']:
                expected_salary = predict_rub_salary_hh(vacancy)
                if expected_salary is not None:
                    total_salary += expected_salary
                    vacancies_processed += 1

            page += 1
            time.sleep(1)

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

if __name__ == "__main__":
    hh_statistics = get_hh_statistics()
    superjob_statistics = get_superjob_statistics()

    print_salary_statistics(hh_statistics, 'HeadHunter Moscow')
    print_salary_statistics(superjob_statistics, 'SuperJob Moscow')
