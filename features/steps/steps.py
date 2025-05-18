import allure
from behave import given, when, then
from pages.main_page import MainPage


@given('Открыть страницу "{url}"')
def open_page(context, url):
    context.main_page = MainPage(context.driver)
    context.main_page.open_page(url)


@then('URL должен быть "{expected_url}"')
def check_url(context, expected_url):
    assert context.driver.current_url == expected_url


@when('Пользователь вводит "{text}" в поле с плейсхолдером "{placeholder}"')
def enter_text(context, text, placeholder):
    context.main_page.enter_text_to_placeholder(text, placeholder)


@then('Пользователь видит заголовок содержащий "{text}"')
def check_title(context, text):
    assert context.main_page.check_title_contains(text), \
        f"Заголовок не содержит '{text}'"


@when('Пользователь кликает на текст "{text}"')
def step_click_by_text(context, text):
    context.main_page.click_by_text(text)


@when('Пользователь кликает на "{element_type}" с текстом "{text}"')
def click_by_text_and_type(context, element_type, text):
    context.main_page.click_by_text(text, element_type.lower())


@when('Пользователь кликает на элемент с ID "{element_id}"')
def click_element_by_id(context, element_id):
    context.main_page.click_by_id(element_id)


@when('Пользователь кликает на элемент с классом "{class_name}"')
def click_element_by_class(context, class_name):
    context.main_page.click_by_class(class_name)


@when('Пользователь кликает на {index}-й элемент с классом "{class_name}"')
def click_element_by_class_with_index(context, index, class_name):
    context.main_page.click_by_class(class_name, int(index) - 1)


@when('Пользователь кликает на элемент с data-component "{component_name}"')
def click_element_by_data_component(context, component_name):
    context.main_page.click_by_data_component(component_name)


@then('Пользователь ожидает сообщение с текстом "{expected_text}"')
def check_expected_message(context, expected_text):
    """
    Проверяет наличие текста на странице
    Примеры:
      Тогда Пользователь ожидает сообщение с текстом "Добро пожаловать"
    """
    is_present = context.main_page.is_text_present(expected_text)
    assert is_present, (
        f"Текст '{expected_text}' не найден на странице. "
        f"Текущий URL: {context.driver.current_url}"
    )


@when('Пользователь вводит "{text}" в поле с data-component "{component_name}"')
def enter_text_to_data_component(context, text, component_name):
    """
    Пример использования:
      Когда Пользователь вводит "test@example.com" в поле с data-component "email-input"
    """
    try:
        context.main_page.enter_text_to_data_component(text, component_name)
    except Exception as e:
        allure.attach(
            context.driver.get_screenshot_as_png(),
            name=f"enter_text_data-component_error",
            attachment_type=allure.attachment_type.PNG
        )
        raise AssertionError(f"Не удалось ввести текст в data-component='{component_name}': {str(e)}")


@then('Пользователь ожидает, что элемента с текстом "{text}" нет на странице')
def step_text_not_present(context, text):
    """
    Пример использования:
      Тогда Пользователь ожидает, что элемента с текстом "Ошибка" нет на странице
    """
    is_not_present = context.main_page.is_text_not_present(text)
    assert is_not_present, f"Элемент с текстом '{text}' найден на странице, хотя не должен был быть"
