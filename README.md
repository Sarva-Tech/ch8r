# Ch8r

Ch8r is an open source smart customer support agent that provides chat widget and API access. It works by allowing users to upload their documents as knowledge base files and then processes 
them in a way AI can search and provide information to users. 

## Features 

- Application based data separation
- Knowledge base
- Widget integration
- Chat API access
- Conversation insights
- Smart human escalation
- Notification profiles
- Project management integrations

## Roadmap

- Automated knowledge base processing.
- Support for additional knowledge base sources such as URLs, Discord, and Slack.
- Bring and use your own AI models and vector databases. 
- Additional project management integrations such as Jira and Linear.
- CRMs integration.
- Custom tool integration to perform product specific actions.
- Support for creating Discord,Slack, and WhatsApp chat bots.

## Technologies

Tech stack used for development:

- **Python**
- **Django**
- **Celery**
- **Qdrant** 
- **Nuxt.js**
- **Vue.js**
- **Tailwind CSS**
- **ShadCN Vue**
  

## Project Structure

The project is organized into separate directories for backend, frontend, and widget to keep concerns isolated and maintainable:

- **backend/**: Contains Django project, APIs, models, serializers, and other server-side logic.  
- **frontend/**: Contains Nuxt.js + Vue.js application along with TailwindCSS and ShadCN Vue components.  
- **widget/**: Contains the embeddable smart support widget code for client integration.


## Backend Setup Instructions

Follow these steps before running the backend:

- Clone the Repository
- Navigate to Backend Directory
  ``` cd backend ```
- Create a Virtual Environment
- Install Python Dependencies
- Configure Environment Variables
- Apply Database Migrations
- Run Qdrant Vector Database
  ```
  docker run -p 6333:6333 -p 6334:6334 \
    -v ~{{ path to project }}/qdrant_storage:/qdrant/storage:z \
    qdrant/qdrant
  ```
- Start Celery Worker
  ``` celery -A config worker -l info --pool=solo ```
- Run Django Server
  ```
    watchfiles --ignore-paths uploads "daphne config.asgi:application" .
  ```

## Frontend Setup Instructions
- Navigate to Frontend Directory
  ``` cd frontend ```
- Run `npm install`
- Run `npm run dev`

## Widget Setup Instructions
- Navigate to Widget Directory
  `cd widget`
- Serve widget `python -m http.server 3002`
