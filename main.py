import requests
from terminaltables import AsciiTable
import time
from dotenv import load_dotenv
import os


def print_salary_statistics(statistics, title):
    table_data = [['Язык программирования', 'Найдено вакансий', 'Обработано вакансий', 'Средняя зарплата']]
    for language, salary_data in statistics.items():
        table_data.append([
            language,
            salary_data['vacancies_found'],
            salary_data['vacancies_processed'],
            salary_data['average_salary']
        ])
    table = AsciiTable(table_data, title)
    print(table.table)


def summarize_vacancies_salary(vacancies, salary_predictor):
    total_vacancies_processed = 0
    total_salary = 0

    for vacancy in vacancies:
        expected_salary = salary_predictor(vacancy)
        if expected_salary is not None:
            total_salary += expected_salary
            total_vacancies_processed += 1

    return total_salary, total_vacancies_processed


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

            if not response.ok:
                print(f"Ошибка при запросе: {response.status_code} - {response.text}")
                break

            superjob_response = response.json()

            if 'objects' not in superjob_response or not superjob_response['objects']:
                break

            total_vacancies_found = superjob_response['total']
            total_salary, total_vacancies_processed = summarize_vacancies_salary(superjob_response['objects'], predict_rub_salary_sj)

            total_salary += page_total_salary
            total_vacancies_processed += page_vacancies_processed
            
            page += 1
            time.sleep(1)

        average_salary = int(total_salary / total_vacancies_processed) if total_vacancies_processed else 0

        salary_statistics[language] = {
            "vacancies_found": total_vacancies_found,
            "vacancies_processed": total_vacancies_processed,
            "average_salary": average_salary
        }

    return salary_statistics


def get_hh_statistics(programming_languages, area_moscow, vacancies_per_page, headers_hh):
    salary_statistics = {}
    for language in programming_languages:
        url = "https://api.hh.ru/vacancies"
        params = {
            'area': area_moscow,  
            'text': language,
            'per_page': vacancies_per_page,  
            'page': 0  
        }

        initial_response = requests.get(url, params=params, headers=headers_hh, verify=False)
        initial_response.raise_for_status()
        initial_response_content = initial_response.json()

        vacancies_found = initial_response_content['found']
        pages_number = initial_response_content['pages'] 

        print(f"Найдено вакансий: {vacancies_found}, страниц: {pages_number}")

        total_salary = 0
        total_vacancies_processed = 0
        
        total_salary, vacancies_processed = summarize_vacancies_salary(initial_response_content['items'], predict_rub_salary_hh)

        for page in range(1, pages_number):
            print(f"Загрузка {language}, страница {page + 1} из {pages_number}")

            params['page'] = page
            page_response = requests.get(url, params=params, headers=headers_hh, verify=False)

            try:
                page_response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                print(f"Ошибка при загрузке страницы {page + 1}: {e}")
                break  

            page_payload = page_response.json()

            page_total_salary, page_vacancies_processed = summarize_vacancies_salary(page_payload['items'], predict_rub_salary_hh)
            
            total_salary += page_total_salary
            total_vacancies_processed += page_vacancies_processed

            time.sleep(1)  

        average_salary = int(total_salary / vacancies_processed) if vacancies_processed else 0

        salary_statistics[language] = {
            "vacancies_found": vacancies_found,
            "vacancies_processed": vacancies_processed,
            "average_salary": average_salary
        }

    return salary_statistics


def predict_rub_salary_hh(vacancy):
    salary = vacancy.get('salary')
    if not salary or salary['currency'] != 'RUR':
        return None

    from_salary = salary.get('from')
    to_salary = salary.get('to')

    return predict_rub_salary(from_salary, to_salary, 'RUR')


def predict_rub_salary_sj(vacancy):
    salary_from = vacancy.get('payment_from', 0)
    salary_to = vacancy.get('payment_to', 0)

    return predict_rub_salary(salary_from, salary_to, 'RUR')


def predict_rub_salary(salary_from=None, salary_to=None, currency='RUR'):
    if currency != 'RUR':
        return None

    if salary_from > 0 and salary_to > 0:
        return (salary_from + salary_to) / 2
    if salary_from > 0:
        return salary_from * 1.2
    if salary_to > 0:
        return salary_to * 0.8

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
