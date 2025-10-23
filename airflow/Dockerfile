# Custom Airflow image = base Airflow + this project's data deps.
# Pinned to 2.10.5 (stable, heavily documented). Bump later if desired.
FROM apache/airflow:2.10.5-python3.12

# Install extra Python deps under Airflow's constraints to avoid version drift.
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.10.5/constraints-3.12.txt"

# supabase installed WITHOUT the Airflow constraint — it needs a newer httpx than
# the constraint pins, so constraining it would fail to resolve. Separate layer.
RUN pip install --no-cache-dir "supabase==2.18.1"

# NOTE: No Chrome/Selenium installed — the DAG uses the pure-HTTP bs4 downloader,
# which the live-site test proved works. If you later switch back to Selenium,
# add chromium + chromium-driver here (apt-get, as root user) and set CHROME_BIN.
