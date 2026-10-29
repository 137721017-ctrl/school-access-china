PY ?= python

.PHONY: demo tables clean
demo:
	$(PY) demo/run_demo.py

tables:
	$(PY) -m src.run_all --table $$SCHOOL_ACCESS_TABLE --out outputs

clean:
	rm -rf outputs/*.csv demo/synthetic
