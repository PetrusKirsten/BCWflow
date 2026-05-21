install:
	pip install -e ".[dev]"

collect-queues:
	python -m parkflow.data.collect_queue_times

build-queues:
	python -m parkflow.data.build_queue_times_dataset

make-modeling:
	python -m parkflow.data.make_modeling_dataset

collect-context:
	python -m parkflow.data.historical_context

dashboard:
	streamlit run dashboard/app.py

test:
	pytest

collect-queues-loop:
	python -m parkflow.data.run_queue_times_collector --interval-minutes 30

audit-data:
	python -m parkflow.data.audit_processed_data


eda-notebook:
	jupyter lab notebooks/02_exploratory_analysis.ipynb

eda-refresh:
	python -m parkflow.data.build_queue_times_dataset
	python -m parkflow.data.make_modeling_dataset
	python -m parkflow.data.audit_processed_data
