import math
from typing import Any, Dict, List, Union
from typing import List

def split_operations(expression: str) -> List[str]:
    """
    Splits the input expression into individual operations,
    ignoring commas that are enclosed within parentheses.

    Args:
        expression (str): The input string containing operations separated by commas.

    Returns:
        List[str]: A list of operation strings.
    """
    operations = []
    current_op = ''
    paren_count = 0
    for char in expression:
        if char == ',' and paren_count == 0:
            if current_op:
                operations.append(current_op)
                current_op = ''
        else:
            if char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1
            current_op += char
    if current_op:
        operations.append(current_op)
    return operations

def parse_arguments(operation: str, func_name: str) -> List[str]:
    """
    Parses the argument list from a function call expression.

    Args:
        operation (str): The function call expression.
        func_name (str): The name of the function to parse.

    Returns:
        List[str]: A list of argument strings.

    Raises:
        ValueError: If the operation does not match the expected function syntax.
    """
    if operation.startswith(func_name + "(") and operation.endswith(")"):
        # Extract the argument substring between the parentheses
        args_str = operation[len(func_name) + 1: -1]
        # Split the arguments, taking nested parentheses into account
        args = split_arguments(args_str)
        return args
    else:
        raise ValueError(f"Invalid syntax for {func_name}: {operation}")

def split_arguments(args_str: str) -> List[str]:
    """
    Splits a string of function arguments into individual arguments,
    properly handling nested parentheses.

    Args:
        args_str (str): The string containing comma-separated arguments.

    Returns:
        List[str]: A list of individual argument strings.
    """
    args = []
    current_arg = ''
    paren_count = 0
    for char in args_str:
        if char == ',' and paren_count == 0:
            args.append(current_arg)
            current_arg = ''
        else:
            if char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1
            current_arg += char
    if current_arg:
        args.append(current_arg)
    return args

def value(arg: str, results: List[Any], const_dict: Dict[str, Union[int, float]]) -> Union[int, float]:
    """
    Parses a value from the argument string.

    Args:
        arg (str): The argument to parse.
        results (List[Any]): List of intermediate results, accessed by reference (e.g., '#0').
        const_dict (Dict[str, Union[int, float]]): Dictionary of predefined constants.

    Returns:
        Union[int, float]: The numerical value parsed from the argument.
    """
    arg = arg.strip()
    if arg.startswith("#"):  # Reference to intermediate result
        index = int(arg[1:])
        return results[index] if index < len(results) else float('nan')
    elif arg.startswith("const_"):  # Reference to constant
        return const_dict.get(arg, float('nan'))
    elif "%" in arg:  # Percentage representation
        return float(arg.strip('%')) / 100
    elif "$" in arg:  # Currency representation
        return float(arg.strip('$'))
    else:  # Plain numerical value
        return float(arg)


def format_number(number, operation):
    """
    Formats a numeric value.

    - If the operation contains a percent sign, output as a percent.
    - Otherwise, return the number with up to 4 decimal places.

    Args:
        number: The number to format.
        operation: The operation string, used to infer formatting style.

    Returns:
        str or int or float: The formatted number.
    """
    try:
        # Output as percent if required by operation syntax
        if "%" in operation:
            return f"{round(float(number) * 100, 2)}%"
            # Normal formatting for int or float
        if isinstance(number, (int, float)):
            formatted_number = round(float(number), 4)
            if formatted_number.is_integer():
                return int(formatted_number)
            return formatted_number
            # Try to convert string to float
        if isinstance(number, str) and number.replace('.', '', 1).isdigit():
            formatted_number = round(float(number), 4)
            if formatted_number.is_integer():
                return int(formatted_number)
            return formatted_number
            # If the input cannot be handled, raise error
        raise ValueError(f"Invalid input for formatting: {number}")
    except Exception as e:
        # Catch and return exception information
        return f"Error: {str(e)}"


def evaluate_expression(expressions: List[str]):
    """
    Parses and evaluates a list of expressions.

    Supported operations: add, subtract, multiply, divide, exp.

    Args:
        expressions (List[str]): A list of string expressions to evaluate.

    Returns:
        Any: The final result, or an error message if an error occurs.
    """
    results = []  # Store intermediate results (#0 refers to results[0])
    const_dict = {
        'const_1': 1, 'const_2': 2, 'const_3': 3, 'const_4': 4,
        'const_5': 5, 'const_6': 6, 'const_7': 7,
        'const_100': 100, 'const_1000': 1000,
        'const_10000': 10000, 'const_1000000': 1000000
    }  # Predefined constants

    for expression in expressions:
        # Remove whitespace and convert to lowercase for uniform parsing
        expression = expression.replace(" ", "").lower()
        # Split complex expression considering nested commas in parentheses
        operations = split_operations(expression)
        for operation in operations:
            try:
                # Recognize and evaluate supported operations
                if operation.startswith("add("):
                    args = parse_arguments(operation, "add")
                    result = value(args[0], results, const_dict) + value(args[1], results, const_dict)
                elif operation.startswith("subtract("):
                    args = parse_arguments(operation, "subtract")
                    result = value(args[0], results, const_dict) - value(args[1], results, const_dict)
                elif operation.startswith("multiply("):
                    args = parse_arguments(operation, "multiply")
                    result = value(args[0], results, const_dict) * value(args[1], results, const_dict)
                elif operation.startswith("divide("):
                    args = parse_arguments(operation, "divide")
                    denominator = value(args[1], results, const_dict)
                    if denominator == 0:
                        result = "Error: Division by zero"
                    else:
                        result = value(args[0], results, const_dict) / denominator
                elif operation.startswith("exp("):
                    args = parse_arguments(operation, "exp")
                    result = value(args[0], results, const_dict) ** value(args[1], results, const_dict)
                else:
                    result = f"Error: Unsupported operation '{operation}'"
                    # Round floats, maintain up to 4 decimals
                if isinstance(result, (int, float)):
                    if isinstance(result, float) or result % 1 != 0:
                        result = round(result, 4)
                        # Store intermediate result
                results.append(result)
            except Exception as e:
                results.append(f"Error: {str(e)}")
                # Format the most recent result
            res = format_number(results[-1], operation)
    return res


def remove_multiply_suffix(strings: str) -> str:
    """
    Detects and removes specific multiplication suffixes at the end of the expression string.

    Args:
        strings (str): The string to be processed.

    Returns:
        str: The processed string with designated suffixes removed.
    """
    strings = strings.replace(" ", "")
    strings = [strings]
    suffixes_to_remove = [
        ",multiply(#0,100)", ",multiply(#1,100)", ",multiply(#2,100)",
        ",multiply(#3,100)", ",multiply(#4,100)"
    ]
    processed_strings = []
    for string in strings:
        for suffix in suffixes_to_remove:
            if string.endswith(suffix):
                string = string[: -len(suffix)]
                break  # Stop at the first matching suffix
        processed_strings.append(string)
    return processed_strings[0]