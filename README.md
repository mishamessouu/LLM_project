# LLM_project
Group Project for the course Large Language Models and Societal Consequences of Artificial Intelligence 1RT730.

## Run the chatbot (chatbot.py)

1) Set OpenAI API key
- Create a file named `.env` in the project root with:
	- `OPENAI_API_KEY=sk-...`

2) Ensure the database is available
- The app will look for `happiness.db` in this order:
	1. Environment variable `HAPPINESS_DB_PATH`
	2. `./happiness.db` (project root)
	3. `./preprocessing/happiness.db`

3) Start the app
```
python chatbot.py
```
This will launch the Gradio web UI and open it in your browser.

## Preprocessing (optional)
If you need to (re)create the SQLite DB, use the scripts in `preprocessing/`. Ensure the output file is named `happiness.db` and placed as described above.