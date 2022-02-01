# benbot
Slack bot that gets Cafe Bon Appetit lunch menus and regurgitates this info on command.

## How do I use this?
1. Clone the repo
2. Create a [Slack app](https://api.slack.com/apps)
3. Add a bot token to your Slack app.
4. Copy the `config/config.tpl.yml` to `config/config.yml` and fill it out with your values
5. Find your cafe-name(s) from the Cafe Bon Appetit URL (`https://{company}.cafebonappetit.com/cafe/{cafe}/`)
6. Get the app running in your server (implementation totally up to you, I use NGINX to run `hypercorn --bind unix:benbot.sock -m 007 src/benbot6:app`)
7. Set your Slack app up for Event Subscriptions (really only need app_mention with the app_mentions:read scope)
8. Have fun.
