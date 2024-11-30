# Code Style Guide: Writing Maintainable and Readable Code

Code is read much more often than it is written. Write for the developer who will maintain your code tomorrow.

## 1. Naming Conventions

### Variable and Function Naming

- Use descriptive, self-explanatory names that reveal intent
- Avoid abbreviations and single-letter variables (except in very specific contexts like loop counters)
- Use verb phrases for functions that perform actions
- Use nouns or adjective phrases for variables

**Examples:**

```python
def calculate_total_revenue(quarterly_sales, annual_bonus):
customer_contact_list = []
total_employee_count = 42
```

### Naming Patterns

- Use snake_case for Python (lowercase with underscores)
- Use camelCase for JavaScript
- Use PascalCase for class names
- Be consistent with your language's conventions

## 2. Avoiding Magic Numbers and Strings

### Replace Magic Values with Named Constants

- Define constants at the top of the file or in a constants module
- Use ALL_CAPS for constants

**Example:**

```python
ADULT_AGE_THRESHOLD = 18
MAX_TICKET_PRICE = 50

if user_age > ADULT_AGE_THRESHOLD and ticket_price < MAX_TICKET_PRICE:
    approve_purchase()
```

## 3. Comments and Documentation

### Minimize Unnecessary Comments

- Write self-documenting code that doesn't need extensive explanation
- Comments should explain "why", not "what"
- Remove commented-out code
- Use docstrings for function and class documentation

**Bad Example:**

```python
# Add 1 to x
x = x + 1  # Redundant comment explaining exactly what the code does

# Commented-out code
# old_calculation = x * 2
current_calculation = x * 3
```

**Good Example:**

```python
def calculate_tax_rate(income):
    """
    Calculate progressive tax rate based on income bracket.

    Handles edge cases for minimum income threshold and maximum tax rate.

    :param income: Annual income in local currency
    :return: Applicable tax rate as a percentage
    """
    if income <= TAX_EXEMPTION_THRESHOLD:
        return 0

    return apply_progressive_tax_calculation(income)
```

## 4. Function and Method Design

### Single Responsibility Principle

- Each function should do one thing and do it well
- Keep functions short and focused
- Avoid functions with more than 3-4 parameters

**Example:**

```python
def validate_user_data(user_info):
    # Validates user data

def save_user_to_database(validated_user):
    # Saves user to database

def send_welcome_email(user_email):
    # Sends welcome email
```

## 5. Error Handling and Defensive Programming

### Explicit Error Handling

- Use specific exception types
- Provide meaningful error messages
- Avoid silent failures

**Example:**

```python
def divide_numbers(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
```

## 6. Code Structure and Organization

### Keep Functions and Classes Focused

- Follow the Single Responsibility Principle
- Break complex logic into smaller, manageable pieces
- Use meaningful abstractions

## 7. Avoid Code Smells

### Common Anti-Patterns to Avoid

- Deep nesting (more than 2-3 levels)
- Long methods/functions
- Duplicated code
- Overly complex conditional logic

## 8. Configuration and Environment

### Separate Configuration from Code

- Use environment variables for configuration
- Create configuration files for different environments
- Avoid hardcoding sensitive information

## 9. Performance Considerations

### Write Clear Code First, Optimize Later

- Prioritize readability over premature optimization
- Use profiling tools to identify actual bottlenecks
- Comment performance-critical sections
