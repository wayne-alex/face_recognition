import os


def count_lines_of_code(directory):
    total_lines = 0
    for dirpath, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            if filename.endswith('.py'):  # Count only Python files
                filepath = os.path.join(dirpath, filename)
                with open(filepath, 'r', encoding='utf-8') as file:
                    lines = file.readlines()
                    total_lines += len(lines)
    return total_lines


project_directory = r'C:\Users\wayne\PycharmProjects\face_recognition_login'
total_lines = count_lines_of_code(project_directory)
print(f'Total lines of code: {total_lines}')
