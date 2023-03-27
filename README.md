# Convert markdown

Run 

```
node convert_markdown.js --input-dir copilot/data/data --output-dir copilot/data/doc-sections
```


# Embed text

Run 

```
python embed_text.py --input_dir="copilot/data/doc-sections"
```

# Run app

Install requirements with

```
pip install -r requirements.txt
```

Run server with

```
python manage.py runserver
```