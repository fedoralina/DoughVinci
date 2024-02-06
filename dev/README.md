# Alexa

In separate terminals:

- rasa run actions
- rasa run -m models --endpoints endpoints.yml
- ngrok http 5005
---
- copy https-URL from ngrok terminal
- paste into Alexa Skill-Kit: 
    - Endpoint / HTTPS / SSL: My dev. endpoint is subdomain...
- add `/webhooks/alexa_assistant/webhook` after the ngrok URL
- URL should look like `abc.ngrok.io/webhooks/alexa_assistant/webhook`
---
- save and build
- test by saying the invocation name followed by "hi"