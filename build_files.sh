# Install pip
python3.9 -m ensurepip

# Install Python dependencies
python3.9 -m pip install -r requirements.txt

# Collect static files
python3.9 manage.py collectstatic --noinput
