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
