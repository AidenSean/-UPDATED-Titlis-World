import google.generativeai as genai

genai.configure(api_key="AIzaSyBGcAWwCpxrzY3z9hayFz8qmHT4WDe2Gzg")
models = genai.list_models()

for model in models:
    print(model.name)
