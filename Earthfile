VERSION 0.7
FROM python:3.10
WORKDIR /contrib

linting-files:
  COPY .prettierignore .
  SAVE ARTIFACT .

src-files:
  COPY electricitymap ./electricitymap
  COPY parsers ./parsers
  COPY ./config+src-files/* ./config
  COPY scripts ./scripts
  COPY web/public/locales/en.json ./web/public/locales/en.json
  COPY __init__.py ./__init__.py
  COPY pyproject.toml .
  SAVE ARTIFACT .

poetry-lock:
  COPY poetry.lock .
  SAVE ARTIFACT .

prepare:
  FROM +src-files
  RUN pip install poetry==1.6.1
  RUN apt-get update && apt-get install -y python3-opencv tesseract-ocr tesseract-ocr-jpn tesseract-ocr-eng libgl1
  RUN poetry config virtualenvs.create false
  RUN poetry install --compile -E parsers

build:
  FROM +prepare

test:
  FROM +build
  COPY tests ./tests
  COPY web/src/utils/constants.ts ./web/src/utils/constants.ts # TODO: python tests should not depend on this js file
  COPY web/geo/world.geojson ./web/geo/world.geojson
  RUN poetry run check

# includes both test target and build target here to make sure both can work
# we can split into two later if required
test-all:
  BUILD +build
  BUILD ./config+test
  # BUILD ./web+build # TODO: This currently fails for unknown reasons, disabling for now
  BUILD ./web+test

