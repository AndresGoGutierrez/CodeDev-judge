# CodeDev - Virtual Judge Platform

A **web platform designed to strengthen programming skills among students** by providing tools and resources to prepare effectively for programming competitions.
Built with **Microservices architecture**, **Python**, **Javascript**, and **React**, fully deployable via Docker/Kubernetes with CI/CD integration.

---

## 👨‍💻 Overview

This project is a virtual judge system that simulates real competition environments, allowing students to practice, submit code, and receive automated feedback.
It features multiple independent microservices for authentication, code evaluation, document library, and support management, all accessible through a unified web interface.

---

## 🚀 Main Features

- Virtual Judge Microservice: Evaluates code in multiple programming languages with automated test cases.
- Authentication Microservice: Secure user registration, login, and session management.
- Document Library Microservice: Centralized access to learning resources and problem statements.
- Support (PQRS) Microservice: Handles user requests, questions, and feedback.
- Unified Frontend: Intuitive React-based interface for seamless user interaction.
- Scalable Architecture: Independent deployment and scaling of each microservice.
- CI/CD Pipeline: Automated testing and deployment using GitHub/GitLab.

---

## 🧰 Tech Stack

**Core Technologies**
- 🧩 Microservices Architecture
- 🔄 API REST (HTTP/JSON)
- 🐳 Docker
- 🎨 Thymeleaf
- 🧱 Domain-Driven Design (DDD)

**Backend Technologies**
- 🐍 Python / Node.js (for microservices)
- ☕ JavaScript
- 🗄️ PostgreSQL / MongoDB (database per service)

**Frontend & Design**
- ⚛️ React + JavaScript
- 🎨 CSS / Tailwind CSS (for responsive design)

**Development & DevOps**
- 🔧 Git (GitFlow) with branch protection
- 🛠️ GitHub / GitLab CI/CD
- 📄 Swagger for API documentation
- 🧪 Unit & Integration Testing (JUnit, Jest, etc.)
- 🔐 Security Practices: Input validation, Circuit Breaker 

**Methodology**
- 🔄 Agile (Scrum) with 2–10 week sprints
- 📊 Trello for project management
---

## 🧱 Architecture

The project follows an **MVC architecture** (Model–View–Controller) with a clear separation of concerns:

CodeDev/
├── microservice-authentication/ # Auth service (JWT, OAuth2)
├── microservice-virtual-judge/ # Code evaluation service
├── microservice-library/ # Document and resource library
├── microservice-pqrs/ # Support and feedback system
└── frontend-react/ # Unified React frontend

## 📽️ Project preview

<div align="center"> 
 <a href="https://youtu.be/EbccvGG35hM" target="_blank"> 
    <img src="https://i.ibb.co/N2qhk00f/image.png" alt="CodeDev Preview" width="700" style="border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.2);"> 
  </a>
</div>

## 🔗 Connect with Me

<p align="center">
  <a href="https://linkedin.com/in/andresgogutierrez/" target="_blank" style="margin-left: 15px;">
    <img src="https://img.icons8.com/doodle/48/000000/linkedin--v2.png" alt="LinkedIn"/>
  </a>
  <a href="https://github.com/AndresGoGutierrez" target="_blank" style="margin-left: 15px;">
    <img src="https://img.icons8.com/doodle/48/000000/github--v1.png" alt="GitHub"/>
  </a>
  <a href="mailto:andregogutierrezgmail.com" target="_blank" style="margin-left: 15px;">
    <img src="https://img.icons8.com/doodle/48/000000/new-post.png" alt="Email"/>
  </a>
</p>
