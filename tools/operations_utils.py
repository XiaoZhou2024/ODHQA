import json
import re


def append_to_json_file(file_path, data):
    """
    Appends new data to a JSON file. If the file does not exist, it creates a new JSON array.

    Args:
        file_path (str): The path to the JSON file.
        data (Any): The data to append to the file.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            existing_data = json.load(file)
    except FileNotFoundError:
        existing_data = []

        # Convert dictionary to list if necessary
    if isinstance(existing_data, dict):
        existing_data = [existing_data]

    existing_data.append(data)

    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(existing_data, file, ensure_ascii=False, indent=4)


def replace_content(content_list, table_title_list, table_list):
    """
    Replaces table placeholder tags within content_list with corresponding table titles and tables.

    Args:
        content_list (List[str]): The document's content as a list of strings.
        table_title_list (List[str]): A list of table titles.
        table_list (List[str]): A list of table string contents.

    Returns:
        List[str]: The content list with tables inserted.
    """
    for cnt, table_title in enumerate(table_title_list):
        for i in range(len(content_list)):
            if content_list[i] == "## Table {} ##".format(cnt):
                tmp = "## Table-{}:".format(cnt) + table_title + '\n' + table_list[cnt] + '\n'
                content_list[i] = tmp
    return content_list


def extract_sub_table(content):
    """
    Extracts the sub-table section from the content using a regex pattern.

    Args:
        content (str): The full content string.

    Returns:
        str or None: The extracted sub-table or None if not found.
    """
    pattern = r"### Sub-Table\s*(.*)"
    match = re.search(pattern, content, re.DOTALL)
    return match.group(1).strip() if match else None


def extract_sub_content(content):
    """
    Extracts the sub-content section from the content using a regex pattern.

    Args:
        content (str): The full content string.

    Returns:
        str or None: The extracted sub-content or None if not found.
    """
    pattern = r"### Sub-Content\s*(.*)"
    match = re.search(pattern, content, re.DOTALL)
    return match.group(1).strip() if match else None


def extract_predicted_program(content):
    """
    Extracts the program section from the content using a regex pattern.

    Args:
        content (str): The full content string.

    Returns:
        str or None: The extracted program or None if not found.
    """
    pattern = r"### Program\s*(.*)"
    match = re.search(pattern, content, re.DOTALL)
    return match.group(1).strip() if match else None


def extract_predicted_program1(content):
    """
    Extracts the arithmetic expression section from the content using a regex pattern.

    Args:
        content (str): The full content string.

    Returns:
        str or None: The extracted arithmetic expressions or None if not found.
    """
    pattern = r"### Arithmetic Expressions\s*(.*)"
    match = re.search(pattern, content, re.DOTALL)
    return match.group(1).strip() if match else None


def extract_predicted_answer(content):
    """
    Extracts the answer section from the content using a regex pattern.

    Args:
        content (str): The full content string.

    Returns:
        str or None: The extracted answer or None if not found.
    """
    pattern = r"### Answer\s*(.*)"
    match = re.search(pattern, content, re.DOTALL)
    return match.group(1).strip() if match else None


def extract_sub_answer(content):
    """
    Extracts the sub-answer section from the content using a regex pattern.

    Args:
        content (str): The full content string.

    Returns:
        str or None: The extracted sub-answer or None if not found.
    """
    pattern = r"### Answer\s*(.*)"
    match = re.search(pattern, content, re.DOTALL)
    return match.group(1).strip() if match else None


def combine_tables_with_titles(tables, titles):
    """
    Combines tables and their titles into formatted strings.

    Args:
        tables (List[str]): A list of table contents.
        titles (List[str]): A list of table titles.

    Returns:
        List[str]: A list of formatted strings, each containing a title and table.
    """
    combined = []
    for i in range(len(tables)):
        combined.append("table_{}:".format(i) + titles[i] + '\n' + tables[i] + '\n')
    return combined