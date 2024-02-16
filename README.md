# DoughVinci
task-based chatbot for pizza ordering, drink recommendations and table booking options built in rasa


## How to test?
Preconditions: Make sure that you have a **Rasa** setup (verion 3.6.16) with **Python** 3.8 (we used 3.8.18) and **Docker**

1. Run duckling server as described in [Rasa docs](https://rasa.com/docs/rasa/components/#ducklingentityextractor)

    `docker run -p 8000:8000 rasa/duckling:latest`

2. Run action server

    `rasa run actions`

3. Train model (run interactive or shell mode)

## Collaborators

<!-- readme: collaborators -start -->
<!-- readme: collaborators -end -->
