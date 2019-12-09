# benbot
Slack bot that reads lunch/dinner menus, stores them, and regurgitates this info on command.

## How do I use this?
1. Clone the repo
1. Create a [Slack bot](https://slack.com/apps/A0F7YS25R-bots), and get its API token
1. Create a Google Sheet with the structure below
1. Create a [Google Service Account](https://console.cloud.google.com/apis/credentials),
   download the JSON, rename as 'service_account.json' and move to the `config/` directory
1. Share your sheet with your bot user's email address (in the `service_account.json` under "client_email")
1. Copy the `config/config.yml.tpl` to `config/config.yml` and fill it out with your values
1. Create and run the Docker container using the `Dockerfile` 


#### Google Sheets Structure
Two identital worksheets (tabs) in a single Spreadsheet, named `lunch` and `dinner`, each with 
the following structure (just a header row):

| Year   | Week  | Monday  | Tuesday | Wednesday | Thursday | Friday |
| ------ |:-----:| :------:| :------:| :--------:| :-------:| :-----:| 
|        |       |         |         |           |          |        |